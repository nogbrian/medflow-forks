"""API endpoints for AI chat and image generation."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import structlog
import json

from app.models import get_db, AIConversation, AIMessage, GeneratedImage, BrandProfile
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ConversationCreate,
    ConversationUpdate,
    ConversationOut,
    ConversationListResponse,
    BrandProfileCreate,
    BrandProfileUpdate,
    BrandProfileOut,
    BrandProfileListResponse,
    ProvidersResponse,
    ProviderInfoOut,
    MessageOut,
)
from app.services.ai import get_provider, get_available_providers
from app.services.ai.base import ChatMessage, MessageRole, ImageGenerationRequest as AIImageRequest

logger = structlog.get_logger()

router = APIRouter()


# ============================================================
# Provider Endpoints
# ============================================================

@router.get("/providers", response_model=ProvidersResponse)
async def list_providers():
    """List available AI providers."""
    try:
        providers = get_available_providers()
        return ProvidersResponse(
            success=True,
            providers=[
                ProviderInfoOut(
                    name=p.name,
                    display_name=p.display_name,
                    supports_chat=p.supports_chat,
                    supports_image_generation=p.supports_image_generation,
                    supports_vision=p.supports_vision,
                    text_models=p.text_models,
                    image_models=p.image_models,
                )
                for p in providers
            ],
        )
    except Exception as e:
        logger.error("Failed to list providers", error=str(e))
        return ProvidersResponse(success=False, providers=[])


# ============================================================
# Chat Endpoints
# ============================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to AI and get a response.

    If conversation_id is provided, continues existing conversation.
    Otherwise creates a new conversation.
    """
    logger.info(
        "Chat request received",
        workspace_id=request.workspace_id,
        agent_type=request.agent_type,
        provider=request.provider,
    )

    try:
        # Get or create conversation
        if request.conversation_id:
            result = await db.execute(
                select(AIConversation).where(AIConversation.id == UUID(request.conversation_id))
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = AIConversation(
                workspace_id=UUID(request.workspace_id),
                agent_type=request.agent_type,
                provider=request.provider,
                system_prompt=request.system_prompt,
                brand_profile_id=UUID(request.brand_profile_id) if request.brand_profile_id else None,
            )
            db.add(conversation)
            await db.flush()

        # Build system prompt
        system_prompt = request.system_prompt or conversation.system_prompt

        # If brand profile, inject synthesis
        if conversation.brand_profile_id:
            result = await db.execute(
                select(BrandProfile).where(BrandProfile.id == conversation.brand_profile_id)
            )
            brand = result.scalar_one_or_none()
            if brand and brand.ai_synthesis:
                system_prompt = f"{system_prompt or ''}\n\n## Brand Context:\n{brand.ai_synthesis}"

        # Convert messages to ChatMessage format
        messages = [
            ChatMessage(
                role=MessageRole(msg.role),
                content=msg.content,
                images=msg.images,
            )
            for msg in request.messages
        ]

        # Get provider and send message
        provider = get_provider(request.provider)

        if request.stream:
            # Return streaming response
            async def generate():
                full_response = ""
                async for chunk in provider.chat_stream(
                    messages=messages,
                    system_prompt=system_prompt,
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                # Save messages after streaming complete
                # Save user message
                user_msg = request.messages[-1]
                db_user_msg = AIMessage(
                    conversation_id=conversation.id,
                    role=user_msg.role,
                    content=user_msg.content,
                    images=user_msg.images,
                )
                db.add(db_user_msg)

                # Save assistant message
                db_assistant_msg = AIMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                )
                db.add(db_assistant_msg)
                await db.commit()

                yield f"data: {json.dumps({'done': True, 'conversation_id': str(conversation.id)})}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
            )

        else:
            # Non-streaming response
            response_text = await provider.chat(
                messages=messages,
                system_prompt=system_prompt,
            )

            # Save user message
            user_msg = request.messages[-1]
            db_user_msg = AIMessage(
                conversation_id=conversation.id,
                role=user_msg.role,
                content=user_msg.content,
                images=user_msg.images,
            )
            db.add(db_user_msg)

            # Save assistant message
            db_assistant_msg = AIMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
            )
            db.add(db_assistant_msg)

            await db.commit()

            return ChatResponse(
                success=True,
                conversation_id=str(conversation.id),
                message=response_text,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat failed", error=str(e))
        return ChatResponse(
            success=False,
            conversation_id=request.conversation_id or "",
            error=str(e),
        )


# ============================================================
# Image Generation Endpoints
# ============================================================

@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate an image using AI."""
    logger.info(
        "Image generation requested",
        provider=request.provider,
        aspect_ratio=request.aspect_ratio,
    )

    try:
        provider = get_provider(request.provider)

        if not provider.supports_image_generation:
            raise HTTPException(
                status_code=400,
                detail=f"Provider {request.provider} does not support image generation",
            )

        # Generate image
        ai_request = AIImageRequest(
            style_prompt=request.style_prompt,
            content_prompt=request.content_prompt,
            aspect_ratio=request.aspect_ratio,
        )

        image_url = await provider.generate_image(ai_request)

        # Save to database
        generated = GeneratedImage(
            workspace_id=UUID(request.workspace_id),
            conversation_id=UUID(request.conversation_id) if request.conversation_id else None,
            provider=request.provider,
            style_prompt=request.style_prompt,
            content_prompt=request.content_prompt,
            aspect_ratio=request.aspect_ratio,
            image_url=image_url,
        )
        db.add(generated)
        await db.commit()

        return ImageGenerationResponse(
            success=True,
            image_id=str(generated.id),
            image_url=image_url,
        )

    except HTTPException:
        raise
    except NotImplementedError as e:
        return ImageGenerationResponse(success=False, error=str(e))
    except Exception as e:
        logger.error("Image generation failed", error=str(e))
        return ImageGenerationResponse(success=False, error=str(e))


# ============================================================
# Conversation Endpoints
# ============================================================

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    workspace_id: str,
    agent_type: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List conversations for a workspace."""
    try:
        query = select(AIConversation).where(
            AIConversation.workspace_id == UUID(workspace_id)
        ).order_by(AIConversation.updated_at.desc())

        if agent_type:
            query = query.where(AIConversation.agent_type == agent_type)

        result = await db.execute(query)
        conversations = result.scalars().all()

        return ConversationListResponse(
            success=True,
            conversations=[
                ConversationOut(
                    id=str(c.id),
                    workspace_id=str(c.workspace_id),
                    brand_profile_id=str(c.brand_profile_id) if c.brand_profile_id else None,
                    title=c.title,
                    agent_type=c.agent_type,
                    provider=c.provider,
                    is_archived=c.is_archived,
                    context=c.context,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
                for c in conversations
            ],
            total=len(conversations),
        )
    except Exception as e:
        logger.error("Failed to list conversations", error=str(e))
        return ConversationListResponse(success=False, conversations=[], total=0)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with messages."""
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == UUID(conversation_id))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    msg_result = await db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == UUID(conversation_id))
        .order_by(AIMessage.created_at)
    )
    messages = msg_result.scalars().all()

    return ConversationOut(
        id=str(conversation.id),
        workspace_id=str(conversation.workspace_id),
        brand_profile_id=str(conversation.brand_profile_id) if conversation.brand_profile_id else None,
        title=conversation.title,
        agent_type=conversation.agent_type,
        provider=conversation.provider,
        is_archived=conversation.is_archived,
        context=conversation.context,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageOut(
                id=str(m.id),
                role=m.role,
                content=m.content,
                images=m.images or [],
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation."""
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == UUID(conversation_id))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conversation)
    await db.commit()

    return {"success": True}


# ============================================================
# Brand Profile Endpoints
# ============================================================

@router.get("/brand-profiles", response_model=BrandProfileListResponse)
async def list_brand_profiles(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List brand profiles for a workspace."""
    try:
        result = await db.execute(
            select(BrandProfile)
            .where(BrandProfile.workspace_id == UUID(workspace_id))
            .order_by(BrandProfile.name)
        )
        profiles = result.scalars().all()

        return BrandProfileListResponse(
            success=True,
            profiles=[
                BrandProfileOut(
                    id=str(p.id),
                    workspace_id=str(p.workspace_id),
                    name=p.name,
                    description=p.description,
                    color_palette=p.color_palette,
                    typography=p.typography,
                    visual_style=p.visual_style,
                    logo_url=p.logo_url,
                    brand_manual_url=p.brand_manual_url,
                    ai_synthesis=p.ai_synthesis,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in profiles
            ],
            total=len(profiles),
        )
    except Exception as e:
        logger.error("Failed to list brand profiles", error=str(e))
        return BrandProfileListResponse(success=False, profiles=[], total=0)


@router.post("/brand-profiles", response_model=BrandProfileOut)
async def create_brand_profile(
    request: BrandProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new brand profile."""
    profile = BrandProfile(
        workspace_id=UUID(request.workspace_id),
        name=request.name,
        description=request.description,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return BrandProfileOut(
        id=str(profile.id),
        workspace_id=str(profile.workspace_id),
        name=profile.name,
        description=profile.description,
        color_palette=profile.color_palette,
        typography=profile.typography,
        visual_style=profile.visual_style,
        logo_url=profile.logo_url,
        brand_manual_url=profile.brand_manual_url,
        ai_synthesis=profile.ai_synthesis,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/brand-profiles/{profile_id}", response_model=BrandProfileOut)
async def get_brand_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a brand profile."""
    result = await db.execute(
        select(BrandProfile).where(BrandProfile.id == UUID(profile_id))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    return BrandProfileOut(
        id=str(profile.id),
        workspace_id=str(profile.workspace_id),
        name=profile.name,
        description=profile.description,
        color_palette=profile.color_palette,
        typography=profile.typography,
        visual_style=profile.visual_style,
        logo_url=profile.logo_url,
        brand_manual_url=profile.brand_manual_url,
        ai_synthesis=profile.ai_synthesis,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.patch("/brand-profiles/{profile_id}", response_model=BrandProfileOut)
async def update_brand_profile(
    profile_id: str,
    request: BrandProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a brand profile."""
    result = await db.execute(
        select(BrandProfile).where(BrandProfile.id == UUID(profile_id))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    # Update fields
    if request.name is not None:
        profile.name = request.name
    if request.description is not None:
        profile.description = request.description
    if request.color_palette is not None:
        profile.color_palette = request.color_palette
    if request.typography is not None:
        profile.typography = request.typography
    if request.visual_style is not None:
        profile.visual_style = request.visual_style

    await db.commit()
    await db.refresh(profile)

    return BrandProfileOut(
        id=str(profile.id),
        workspace_id=str(profile.workspace_id),
        name=profile.name,
        description=profile.description,
        color_palette=profile.color_palette,
        typography=profile.typography,
        visual_style=profile.visual_style,
        logo_url=profile.logo_url,
        brand_manual_url=profile.brand_manual_url,
        ai_synthesis=profile.ai_synthesis,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.delete("/brand-profiles/{profile_id}")
async def delete_brand_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a brand profile."""
    result = await db.execute(
        select(BrandProfile).where(BrandProfile.id == UUID(profile_id))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    await db.delete(profile)
    await db.commit()

    return {"success": True}


# ============================================================
# Multi-Model Comparison Endpoints
# ============================================================

@router.get("/models")
async def list_frontier_models():
    """
    List all available frontier models.

    Returns models from all providers (OpenAI, Anthropic, Google, xAI)
    with availability status based on configured API keys.
    """
    from app.services.ai import get_multi_model_service

    service = get_multi_model_service()
    models = service.get_available_models()

    return {
        "success": True,
        "models": models,
        "total": len(models),
        "available_count": len([m for m in models if m["available"]]),
    }


@router.post("/chat/compare")
async def chat_compare(
    workspace_id: str,
    models: list[str],
    message: str,
    images: list[str] | None = None,
    system_prompt: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Send the same message to multiple models and compare responses.

    Useful for:
    - Comparing quality of different models
    - A/B testing prompts
    - Finding the best model for a specific task
    """
    from app.services.ai import get_multi_model_service

    logger.info(
        "Multi-model comparison requested",
        models=models,
        workspace_id=workspace_id,
    )

    service = get_multi_model_service()

    # Run comparison
    responses = await service.chat_multi(
        model_keys=models,
        message=message,
        images=images,
        system_prompt=system_prompt,
    )

    return {
        "success": True,
        "responses": [
            {
                "model_id": r.model_id,
                "provider": r.provider,
                "display_name": r.display_name,
                "content": r.content,
                "images": r.images,
                "error": r.error,
                "latency_ms": r.latency_ms,
            }
            for r in responses
        ],
    }


# ============================================================
# Memory & Context Endpoints
# ============================================================

@router.post("/memory/store")
async def store_memory(
    workspace_id: str,
    content: str,
    role: str = "knowledge",
    conversation_id: str | None = None,
    metadata: dict | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Store a memory entry with embedding for semantic search."""
    from app.services.ai import get_memory_service

    service = get_memory_service()
    memory_id = await service.store_memory(
        db=db,
        workspace_id=workspace_id,
        content=content,
        role=role,
        conversation_id=conversation_id,
        metadata=metadata,
    )

    return {
        "success": memory_id is not None,
        "memory_id": memory_id,
    }


@router.post("/memory/search")
async def search_memories(
    workspace_id: str,
    query: str,
    limit: int = 10,
    similarity_threshold: float = 0.7,
    conversation_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Search memories using semantic similarity."""
    from app.services.ai import get_memory_service

    service = get_memory_service()
    memories = await service.search_memories(
        db=db,
        workspace_id=workspace_id,
        query=query,
        limit=limit,
        similarity_threshold=similarity_threshold,
        conversation_id=conversation_id,
    )

    return {
        "success": True,
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "role": m.role,
                "similarity": m.similarity,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ],
        "count": len(memories),
    }


@router.post("/conversations/{conversation_id}/consolidate")
async def consolidate_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Consolidate a conversation into long-term memory.

    Creates a summary of the conversation that can be retrieved
    in future conversations for context.
    """
    from app.services.ai import get_memory_service

    # Get conversation to find workspace_id
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == UUID(conversation_id))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    service = get_memory_service()
    memory_id = await service.consolidate_memories(
        db=db,
        workspace_id=str(conversation.workspace_id),
        conversation_id=conversation_id,
    )

    return {
        "success": memory_id is not None,
        "memory_id": memory_id,
    }
