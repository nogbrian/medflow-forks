"""
Memory and Context Engineering Service.

Uses PostgreSQL + pgvector for:
- Semantic search in chat history
- Long-term memory storage
- Context window optimization
- Embeddings storage and retrieval
"""

import json
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

logger = structlog.get_logger(__name__)

# Lazy import for embeddings
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class MemoryEntry:
    """A single memory entry with embedding."""
    id: str
    workspace_id: str
    conversation_id: str | None
    content: str
    role: str  # 'user', 'assistant', 'system', 'knowledge'
    embedding: list[float] | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime | None = None
    similarity: float = 0.0


@dataclass
class ContextWindow:
    """Optimized context window for AI requests."""
    system_prompt: str
    memories: list[MemoryEntry]
    recent_messages: list[MemoryEntry]
    knowledge: list[MemoryEntry]
    total_tokens: int = 0

    def to_messages(self) -> list[dict]:
        """Convert to message format for AI."""
        messages = []

        # Add system prompt with context
        full_system = self.system_prompt

        # Add relevant memories
        if self.memories:
            memory_context = "\n\n## Relevant Memories:\n"
            for mem in self.memories:
                memory_context += f"- {mem.content}\n"
            full_system += memory_context

        # Add knowledge
        if self.knowledge:
            knowledge_context = "\n\n## Relevant Knowledge:\n"
            for k in self.knowledge:
                knowledge_context += f"- {k.content}\n"
            full_system += knowledge_context

        if full_system:
            messages.append({"role": "system", "content": full_system})

        # Add recent conversation history
        for msg in self.recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        return messages


class MemoryService:
    """
    Service for managing AI memory with semantic search.

    Features:
    - Store conversation history with embeddings
    - Semantic search for relevant context
    - Context window optimization
    - Long-term memory consolidation
    """

    EMBEDDING_MODEL = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS = 3072

    def __init__(self):
        self.settings = get_settings()
        self._openai_client = None

    @property
    def openai_client(self):
        """Lazy load OpenAI client for embeddings."""
        if self._openai_client is None and OPENAI_AVAILABLE:
            api_key = self.settings.openai_api_key
            if api_key:
                self._openai_client = AsyncOpenAI(api_key=api_key)
        return self._openai_client

    async def create_embedding(self, text: str) -> list[float] | None:
        """Create embedding for text using OpenAI."""
        if not self.openai_client:
            logger.warning("OpenAI not available for embeddings")
            return None

        try:
            response = await self.openai_client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text,
                dimensions=self.EMBEDDING_DIMENSIONS,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Embedding creation failed", error=str(e))
            return None

    async def store_memory(
        self,
        db: AsyncSession,
        workspace_id: str,
        content: str,
        role: str,
        conversation_id: str | None = None,
        metadata: dict | None = None,
    ) -> str | None:
        """Store a memory entry with embedding."""
        try:
            # Create embedding
            embedding = await self.create_embedding(content)

            # Insert into database
            query = text("""
                INSERT INTO ai_memories (
                    workspace_id, conversation_id, content, role,
                    embedding, metadata, created_at
                )
                VALUES (
                    :workspace_id, :conversation_id, :content, :role,
                    :embedding, :metadata, NOW()
                )
                RETURNING id
            """)

            result = await db.execute(query, {
                "workspace_id": workspace_id,
                "conversation_id": conversation_id,
                "content": content,
                "role": role,
                "embedding": embedding,
                "metadata": json.dumps(metadata or {}),
            })

            row = result.fetchone()
            await db.commit()

            return str(row[0]) if row else None

        except Exception as e:
            logger.error("Memory storage failed", error=str(e))
            await db.rollback()
            return None

    async def search_memories(
        self,
        db: AsyncSession,
        workspace_id: str,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        conversation_id: str | None = None,
    ) -> list[MemoryEntry]:
        """Search memories using semantic similarity."""
        try:
            # Create query embedding
            query_embedding = await self.create_embedding(query)
            if not query_embedding:
                return []

            # Build SQL with pgvector - parameterized query to prevent SQL injection
            if conversation_id:
                sql = text("""
                    SELECT
                        id,
                        workspace_id,
                        conversation_id,
                        content,
                        role,
                        metadata,
                        created_at,
                        1 - (embedding <=> :query_embedding::vector) as similarity
                    FROM ai_memories
                    WHERE workspace_id = :workspace_id
                        AND 1 - (embedding <=> :query_embedding::vector) > :threshold
                        AND conversation_id = :conversation_id
                    ORDER BY similarity DESC
                    LIMIT :limit
                """)
                params = {
                    "workspace_id": workspace_id,
                    "query_embedding": query_embedding,
                    "threshold": similarity_threshold,
                    "limit": limit,
                    "conversation_id": conversation_id,
                }
            else:
                sql = text("""
                    SELECT
                        id,
                        workspace_id,
                        conversation_id,
                        content,
                        role,
                        metadata,
                        created_at,
                        1 - (embedding <=> :query_embedding::vector) as similarity
                    FROM ai_memories
                    WHERE workspace_id = :workspace_id
                        AND 1 - (embedding <=> :query_embedding::vector) > :threshold
                    ORDER BY similarity DESC
                    LIMIT :limit
                """)
                params = {
                    "workspace_id": workspace_id,
                    "query_embedding": query_embedding,
                    "threshold": similarity_threshold,
                    "limit": limit,
                }

            result = await db.execute(sql, params)
            rows = result.fetchall()

            return [
                MemoryEntry(
                    id=str(row[0]),
                    workspace_id=str(row[1]),
                    conversation_id=str(row[2]) if row[2] else None,
                    content=row[3],
                    role=row[4],
                    metadata=json.loads(row[5]) if row[5] else {},
                    created_at=row[6],
                    similarity=row[7],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error("Memory search failed", error=str(e))
            return []

    async def get_recent_messages(
        self,
        db: AsyncSession,
        conversation_id: str,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        """Get recent messages from a conversation."""
        try:
            query = text("""
                SELECT
                    id, conversation_id, content, role, images, created_at
                FROM ai_messages
                WHERE conversation_id = :conversation_id
                ORDER BY created_at DESC
                LIMIT :limit
            """)

            result = await db.execute(query, {
                "conversation_id": conversation_id,
                "limit": limit,
            })
            rows = result.fetchall()

            # Reverse to get chronological order
            return [
                MemoryEntry(
                    id=str(row[0]),
                    workspace_id="",  # Not stored in messages
                    conversation_id=str(row[1]),
                    content=row[2],
                    role=row[3],
                    metadata={"images": row[4]} if row[4] else {},
                    created_at=row[5],
                )
                for row in reversed(rows)
            ]

        except Exception as e:
            logger.error("Recent messages fetch failed", error=str(e))
            return []

    async def build_context_window(
        self,
        db: AsyncSession,
        workspace_id: str,
        current_message: str,
        system_prompt: str | None = None,
        conversation_id: str | None = None,
        max_tokens: int = 8000,
    ) -> ContextWindow:
        """
        Build an optimized context window for AI requests.

        Combines:
        - System prompt
        - Relevant memories (semantic search)
        - Recent conversation history
        - Knowledge base entries
        """
        # Search for relevant memories
        memories = await self.search_memories(
            db=db,
            workspace_id=workspace_id,
            query=current_message,
            limit=5,
            similarity_threshold=0.75,
        )

        # Get recent messages if in conversation
        recent_messages = []
        if conversation_id:
            recent_messages = await self.get_recent_messages(
                db=db,
                conversation_id=conversation_id,
                limit=20,
            )

        # TODO: Search knowledge base when implemented

        return ContextWindow(
            system_prompt=system_prompt or "",
            memories=memories,
            recent_messages=recent_messages,
            knowledge=[],
            total_tokens=0,  # TODO: Implement token counting
        )

    async def consolidate_memories(
        self,
        db: AsyncSession,
        workspace_id: str,
        conversation_id: str,
    ) -> str | None:
        """
        Consolidate conversation into long-term memory.

        Takes a conversation and creates a summary that can be
        stored for future reference.
        """
        # Get all messages from conversation
        messages = await self.get_recent_messages(
            db=db,
            conversation_id=conversation_id,
            limit=100,
        )

        if not messages:
            return None

        # Build summary prompt
        conversation_text = "\n".join([
            f"{m.role}: {m.content}" for m in messages
        ])

        summary_prompt = f"""Summarize the key points and decisions from this conversation.
Focus on:
- Main topics discussed
- Decisions made
- Important information shared
- Action items or next steps

Conversation:
{conversation_text}

Summary:"""

        # Use GPT to create summary
        if self.openai_client:
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-5.2",
                    messages=[{"role": "user", "content": summary_prompt}],
                    max_tokens=500,
                )
                summary = response.choices[0].message.content

                # Store as memory
                memory_id = await self.store_memory(
                    db=db,
                    workspace_id=workspace_id,
                    content=summary,
                    role="memory",
                    conversation_id=conversation_id,
                    metadata={
                        "type": "conversation_summary",
                        "message_count": len(messages),
                    },
                )

                return memory_id

            except Exception as e:
                logger.error("Memory consolidation failed", error=str(e))

        return None


# Singleton instance
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Get singleton memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
