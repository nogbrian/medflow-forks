"""Streaming chat endpoint for the agentic loop.

Provides a Server-Sent Events (SSE) interface for real-time agent
interaction with tool execution visibility.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.auth import OptionalCurrentUser, DBSession

router = APIRouter(prefix="/chat")
logger = logging.getLogger(__name__)


class ChatContext(BaseModel):
    """Optional context from the frontend."""

    pathname: str | None = None
    activeTenant: str | None = None
    activeContext: str | None = None


class ChatRequest(BaseModel):
    """Request to start a chat interaction."""

    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None
    agent_type: str = "general"  # general, sdr, support, content, scheduler
    clinic_id: str | None = None
    tools: list[str] | None = None  # Specific tools to enable
    context: ChatContext | None = None
    stream: bool = True


class ChatResponse(BaseModel):
    """Non-streaming response."""

    success: bool
    content: str
    agent: str
    session_id: str
    turns: int
    tools_called: list[str]
    cost_usd: float


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: OptionalCurrentUser = None,
    db: DBSession = None,
):
    """Stream an agent response via Server-Sent Events.

    Events:
    - text: Streamed text content
    - tool_start: Tool execution beginning
    - tool_result: Tool execution complete
    - turn: New loop turn
    - usage: Cost/token update
    - done: Final result
    - error: Error occurred
    """
    from core.agentic.config import AgenticConfig
    from core.agentic.loop import AgenticLoop
    from core.llm_router import LLMRouter

    # Build system prompt based on agent type
    system_prompt = _get_system_prompt(request.agent_type, request.clinic_id)

    # Get tools for this agent type
    tools = _get_tools_for_agent(request.agent_type, request.tools)

    # Configure the loop
    config = AgenticConfig(
        max_turns=15,
        timeout_seconds=120,
        max_cost_usd=0.5,
        tier="smart",
        stream=True,
        enable_compaction=True,
    )

    llm = LLMRouter()
    loop = AgenticLoop(
        system_prompt=system_prompt,
        tools=tools,
        config=config,
        llm=llm,
    )

    async def event_generator():
        """Generate SSE events from the agentic loop."""
        try:
            async for event in loop.run_streaming(request.message):
                event_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_data}\n\n"

                # Stop on done or error
                if event.get("type") in ("done", "error"):
                    break

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            error_event = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_event}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    current_user: OptionalCurrentUser = None,
    db: DBSession = None,
):
    """Non-streaming chat endpoint.

    Runs the agentic loop to completion and returns the final response.
    """
    from core.agentic.config import AgenticConfig
    from core.agentic.loop import AgenticLoop
    from core.llm_router import LLMRouter

    system_prompt = _get_system_prompt(request.agent_type, request.clinic_id)
    tools = _get_tools_for_agent(request.agent_type, request.tools)

    config = AgenticConfig(
        max_turns=15,
        timeout_seconds=120,
        max_cost_usd=0.5,
        tier="smart",
        stream=False,
        enable_compaction=True,
    )

    llm = LLMRouter()
    loop = AgenticLoop(
        system_prompt=system_prompt,
        tools=tools,
        config=config,
        llm=llm,
    )

    result = await loop.run(request.message)

    return ChatResponse(
        success=result.success,
        content=result.final_response,
        agent=request.agent_type,
        session_id=result.context.session_id,
        turns=result.turns_used,
        tools_called=result.tools_called,
        cost_usd=round(result.total_cost_usd, 6),
    )


# =============================================================================
# HELPERS
# =============================================================================


def _get_system_prompt(agent_type: str, clinic_id: str | None = None) -> str:
    """Get system prompt for the given agent type."""
    prompts = {
        "general": (
            "Você é o MedFlow, assistente de marketing médico para consultórios brasileiros. "
            "Ajude com agendamentos, dúvidas sobre serviços, e atendimento ao paciente. "
            "Sempre responda em português brasileiro. Seja profissional e empático."
        ),
        "sdr": (
            "Você é um SDR (Sales Development Representative) especializado em clínicas médicas. "
            "Sua função é qualificar leads, responder sobre serviços, e agendar consultas. "
            "Seja cordial, profissional, e nunca prometa resultados médicos (CFM). "
            "Responda em português brasileiro."
        ),
        "support": (
            "Você é um atendente de suporte para pacientes de clínicas médicas. "
            "Ajude com informações sobre consultas, preparativos para exames, "
            "e dúvidas administrativas. Seja empático e claro. Português brasileiro."
        ),
        "content": (
            "Você é um especialista em criação de conteúdo para marketing médico. "
            "Crie copies, posts, legendas e roteiros seguindo as normas do CFM. "
            "Sem antes/depois não autorizado, sem garantia de resultados, sem preços públicos. "
            "Português brasileiro, tom profissional e educativo."
        ),
        "scheduler": (
            "Você é um assistente de agendamento para clínicas médicas. "
            "Verifique disponibilidade, crie agendamentos, e confirme com o paciente. "
            "Seja eficiente e claro nas opções de horário. Português brasileiro."
        ),
    }
    return prompts.get(agent_type, prompts["general"])


def _get_tools_for_agent(
    agent_type: str,
    explicit_tools: list[str] | None = None,
) -> dict[str, Any]:
    """Get tools available for a given agent type.

    Returns tools in AgenticLoop format: {name: {"definition": ..., "handler": ...}}
    """
    try:
        from core.tools.registry import get_global_registry
        registry = get_global_registry()

        if explicit_tools:
            return registry.get_for_loop(names=explicit_tools)

        # Map agent types to tool categories
        category_map = {
            "general": None,  # All tools
            "sdr": ["crm", "communication", "calendar"],
            "support": ["communication", "calendar"],
            "content": ["content", "research"],
            "scheduler": ["calendar", "communication"],
        }

        categories = category_map.get(agent_type)
        return registry.get_for_loop(categories=categories)

    except Exception:
        # Registry not populated yet - return empty
        return {}
