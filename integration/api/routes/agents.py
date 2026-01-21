"""AI Agents routes - orchestration and execution."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from core.auth import CurrentUser, DBSession, require_clinic_access
from core.models import Clinic

router = APIRouter(prefix="/agents")
logger = logging.getLogger(__name__)


class GoalRequest(BaseModel):
    """Request to handle a complex goal."""
    goal: str = Field(..., min_length=5)
    context: dict[str, Any] | None = None


class WorkflowRequest(BaseModel):
    """Request to run a workflow."""
    workflow_id: str
    input_data: dict[str, Any] | None = None


class MessageRequest(BaseModel):
    """Request to process a message."""
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None
    contact_data: dict[str, Any] | None = None


class AgentResponse(BaseModel):
    """Response from an agent."""
    success: bool
    content: str
    agent: str
    needs_human: bool = False
    function_calls: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}


# =============================================================================
# MESSAGE ROUTING (Main Entry Point)
# =============================================================================


@router.post("/message", response_model=AgentResponse)
async def process_message(
    data: MessageRequest,
    clinic_id: str | None = Query(None),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Process a message through the agent coordinator.

    Routes to appropriate agent based on content and context.
    This is the main entry point for AI-powered message handling.
    """
    if clinic_id:
        require_clinic_access(current_user, clinic_id)

    try:
        # Import here to avoid circular imports
        from agents.coordinator import route_message, AgentType

        # Route the message to determine which agent should handle it
        routing = await route_message(
            message=data.message,
            contact_data=data.contact_data,
            conversation_context={"conversation_id": data.conversation_id} if data.conversation_id else None,
        )

        agent_type = routing.get("agent", AgentType.SDR)
        confidence = routing.get("confidence", 0.7)
        reasoning = routing.get("reasoning", "")

        logger.info(f"Routed message to {agent_type} with confidence {confidence}: {reasoning}")

        # Check if we need human escalation
        if agent_type == AgentType.ESCALATION:
            return AgentResponse(
                success=True,
                content="Esta conversa será transferida para um atendente humano.",
                agent="escalation",
                needs_human=True,
                metadata={"routing": routing},
            )

        # Execute the appropriate agent
        response_content = await _execute_agent(
            agent_type=agent_type,
            message=data.message,
            clinic_id=clinic_id,
            contact_data=data.contact_data,
            db=db,
        )

        return AgentResponse(
            success=True,
            content=response_content,
            agent=str(agent_type),
            needs_human=False,
            metadata={
                "routing": routing,
                "should_qualify": routing.get("should_qualify", False),
            },
        )

    except Exception as e:
        logger.error(f"Agent processing error: {e}")
        return AgentResponse(
            success=False,
            content="Desculpe, não consegui processar sua mensagem. Um atendente irá ajudá-lo.",
            agent="error",
            needs_human=True,
            metadata={"error": str(e)},
        )


# =============================================================================
# GOAL HANDLING (Complex Tasks)
# =============================================================================


@router.post("/goal")
async def handle_goal(
    data: GoalRequest,
    clinic_id: str = Query(..., description="Clinic UUID"),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Handle a complex high-level goal.

    Decomposes the goal into subtasks and creates an execution plan.
    Uses the Campaign Manager agent for orchestration.

    Example goals:
    - "Criar uma campanha de Dia das Mães para clínica de dermatologia"
    - "Pesquisar tendências de saúde no TikTok"
    - "Gerar 5 posts educativos sobre hipertensão"
    """
    require_clinic_access(current_user, clinic_id)

    # Get clinic info for context
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    try:
        from agents.campaign_manager import create_campaign_manager

        # Create campaign manager with clinic context
        campaign_context = {
            "clinic_name": clinic.name,
            "specialty": clinic.specialty,
            "city": clinic.city,
            "ai_persona": clinic.ai_persona or {},
        }

        manager = create_campaign_manager()

        # Generate execution plan
        plan_prompt = f"""
        Objetivo: {data.goal}

        Contexto da Clínica:
        - Nome: {campaign_context['clinic_name']}
        - Especialidade: {campaign_context['specialty'] or 'Geral'}
        - Cidade: {campaign_context['city'] or 'Brasil'}

        Contexto adicional: {data.context or {}}

        Crie um plano de execução detalhado com subtarefas e agentes responsáveis.
        """

        # This would actually run the agent - for now return structured plan
        return {
            "success": True,
            "plan_id": f"plan-{clinic_id[:8]}",
            "goal": data.goal,
            "status": "created",
            "clinic": {
                "id": clinic_id,
                "name": clinic.name,
            },
            "message": "Plano de execução criado. Subtarefas serão processadas.",
            "subtasks": [
                {"id": "1", "agent": "researcher", "task": "Pesquisar tema", "status": "pending"},
                {"id": "2", "agent": "copywriter", "task": "Criar copies", "status": "pending", "depends_on": ["1"]},
                {"id": "3", "agent": "designer", "task": "Criar artes", "status": "pending", "depends_on": ["2"]},
                {"id": "4", "agent": "reviewer", "task": "Revisar conteúdo", "status": "pending", "depends_on": ["3"]},
            ],
        }

    except ImportError:
        logger.warning("Campaign manager agent not available")
        return {
            "success": True,
            "plan_id": f"plan-{clinic_id[:8]}",
            "goal": data.goal,
            "status": "pending",
            "message": "Goal received. Execution plan will be created.",
        }


@router.get("/plans/{plan_id}")
async def get_plan_status(
    plan_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Get execution plan status."""
    # TODO: Fetch from database
    return {
        "plan_id": plan_id,
        "goal": "Example goal",
        "status": "in_progress",
        "progress": 0.5,
        "subtasks": [
            {"id": "1", "agent": "researcher", "task": "Pesquisar tema", "status": "completed"},
            {"id": "2", "agent": "copywriter", "task": "Criar copies", "status": "in_progress"},
            {"id": "3", "agent": "designer", "task": "Criar artes", "status": "pending"},
        ],
    }


# =============================================================================
# WORKFLOWS (Predefined Pipelines)
# =============================================================================


@router.post("/workflow")
async def run_workflow(
    data: WorkflowRequest,
    clinic_id: str = Query(..., description="Clinic UUID"),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Run a predefined workflow.

    Available workflows:
    - content_creation: Research → Copy → Design → Review
    - lead_qualification: Qualify lead and schedule if hot
    - clinic_onboarding: Setup new clinic
    - follow_up_sequence: Automated follow-up messages
    """
    require_clinic_access(current_user, clinic_id)

    # Validate workflow exists
    valid_workflows = {
        "content_creation": {
            "name": "Criação de Conteúdo",
            "agents": ["researcher", "copywriter", "designer", "reviewer"],
        },
        "lead_qualification": {
            "name": "Qualificação de Lead",
            "agents": ["sdr", "qualifier"],
        },
        "clinic_onboarding": {
            "name": "Onboarding de Clínica",
            "agents": ["onboarding"],
        },
        "follow_up_sequence": {
            "name": "Sequência de Follow-up",
            "agents": ["follow_up"],
        },
    }

    if data.workflow_id not in valid_workflows:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow. Valid: {list(valid_workflows.keys())}",
        )

    workflow = valid_workflows[data.workflow_id]

    return {
        "success": True,
        "execution_id": f"exec-{clinic_id[:8]}-{data.workflow_id[:8]}",
        "workflow_id": data.workflow_id,
        "workflow_name": workflow["name"],
        "status": "started",
        "agents": workflow["agents"],
        "input_data": data.input_data,
    }


# =============================================================================
# AGENT CATALOG
# =============================================================================


@router.get("/available")
async def list_available_agents(current_user: CurrentUser = None):
    """List available agents and workflows."""
    return {
        "agents": [
            {
                "id": "coordinator",
                "name": "Coordenador",
                "description": "Roteia mensagens para o agente correto",
                "capabilities": ["Message routing", "Intent detection", "Escalation"],
            },
            {
                "id": "sdr",
                "name": "SDR (Sales Development)",
                "description": "Atendimento inicial e qualificação de leads",
                "capabilities": ["Lead engagement", "Pricing questions", "Service info"],
            },
            {
                "id": "appointment_scheduler",
                "name": "Agendador",
                "description": "Gerencia agendamentos de consultas",
                "capabilities": ["Schedule appointments", "Reschedule", "Cancel"],
            },
            {
                "id": "support",
                "name": "Suporte ao Paciente",
                "description": "Atende dúvidas de pacientes existentes",
                "capabilities": ["Post-consultation", "Treatment info", "Admin questions"],
            },
            {
                "id": "researcher",
                "name": "Pesquisador",
                "description": "Pesquisa tendências e virais",
                "capabilities": ["Trend research", "Competitor analysis", "Content ideas"],
            },
            {
                "id": "copywriter",
                "name": "Copywriter",
                "description": "Cria copies para redes sociais",
                "capabilities": ["Instagram posts", "Carousels", "Reels scripts", "Ad copy"],
            },
            {
                "id": "designer",
                "name": "Designer",
                "description": "Gera imagens e artes",
                "capabilities": ["Social media posts", "Stories", "Ads", "Thumbnails"],
            },
            {
                "id": "follow_up",
                "name": "Follow-up",
                "description": "Reengajamento de leads frios",
                "capabilities": ["Re-engagement", "Cold lead nurturing", "Sequence automation"],
            },
        ],
        "workflows": [
            {
                "id": "content_creation",
                "name": "Criação de Conteúdo",
                "description": "Pipeline completo: Pesquisa → Copy → Design → Revisão",
                "agents": ["researcher", "copywriter", "designer", "reviewer"],
            },
            {
                "id": "lead_qualification",
                "name": "Qualificação de Lead",
                "description": "Qualifica lead automaticamente e agenda se quente",
                "agents": ["sdr", "qualifier", "scheduler"],
            },
            {
                "id": "follow_up_sequence",
                "name": "Sequência de Follow-up",
                "description": "Mensagens automáticas para reengajamento",
                "agents": ["follow_up"],
            },
        ],
    }


# =============================================================================
# INTERNAL HELPERS
# =============================================================================


async def _execute_agent(
    agent_type: str,
    message: str,
    clinic_id: str | None,
    contact_data: dict[str, Any] | None,
    db: DBSession,
) -> str:
    """Execute the appropriate agent and return response."""
    from agents.coordinator import AgentType

    # Map agent type to actual agent execution
    agent_responses = {
        AgentType.SDR: _run_sdr_agent,
        AgentType.SUPPORT: _run_support_agent,
        AgentType.SCHEDULER: _run_scheduler_agent,
        AgentType.QUALIFIER: _run_qualifier_agent,
        AgentType.FOLLOW_UP: _run_follow_up_agent,
    }

    handler = agent_responses.get(agent_type, _run_default_agent)
    return await handler(message, clinic_id, contact_data, db)


async def _run_sdr_agent(
    message: str,
    clinic_id: str | None,
    contact_data: dict[str, Any] | None,
    db: DBSession,
) -> str:
    """Run SDR agent for sales inquiries."""
    try:
        from agents.atendente_medicos import create_medical_receptionist

        agent = create_medical_receptionist()
        # In a real implementation, we'd run the agent
        # response = await agent.run(message, context=...)
        return f"Olá! Terei prazer em ajudá-lo. {message[:20]}..."
    except ImportError:
        return "Olá! Como posso ajudá-lo hoje? Gostaria de saber mais sobre nossos serviços?"


async def _run_support_agent(
    message: str,
    clinic_id: str | None,
    contact_data: dict[str, Any] | None,
    db: DBSession,
) -> str:
    """Run support agent for existing patients."""
    return "Obrigado por entrar em contato! Vou verificar suas informações e ajudá-lo."


async def _run_scheduler_agent(
    message: str,
    clinic_id: str | None,
    contact_data: dict[str, Any] | None,
    db: DBSession,
) -> str:
    """Run scheduler agent for appointment handling."""
    try:
        from agents.appointment_scheduler import create_appointment_scheduler

        agent = create_appointment_scheduler()
        return "Claro! Vou verificar nossa disponibilidade. Qual dia e horário seria melhor para você?"
    except ImportError:
        return "Entendi que você gostaria de agendar uma consulta. Qual sua preferência de data e horário?"


async def _run_qualifier_agent(
    message: str,
    clinic_id: str | None,
    contact_data: dict[str, Any] | None,
    db: DBSession,
) -> str:
    """Run lead qualifier agent."""
    return "Obrigado pelas informações! Vou analisar seu perfil."


async def _run_follow_up_agent(
    message: str,
    clinic_id: str | None,
    contact_data: dict[str, Any] | None,
    db: DBSession,
) -> str:
    """Run follow-up agent for re-engagement."""
    return "Olá! Notamos que você demonstrou interesse anteriormente. Ainda posso ajudar?"


async def _run_default_agent(
    message: str,
    clinic_id: str | None,
    contact_data: dict[str, Any] | None,
    db: DBSession,
) -> str:
    """Default fallback agent."""
    return "Olá! Como posso ajudá-lo hoje?"
