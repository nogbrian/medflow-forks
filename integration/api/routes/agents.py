"""AI Agents routes - orchestration and execution."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.auth import CurrentUser, DBSession

router = APIRouter(prefix="/agents")


class GoalRequest(BaseModel):
    """Request to handle a complex goal."""
    goal: str = Field(..., min_length=5)
    context: dict | None = None


class WorkflowRequest(BaseModel):
    """Request to run a workflow."""
    workflow_id: str
    input_data: dict | None = None


class MessageRequest(BaseModel):
    """Request to process a message."""
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None


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

    Example goals:
    - "Criar uma campanha de Dia das Mães para clínica de dermatologia"
    - "Pesquisar tendências de saúde no TikTok"
    - "Gerar 5 posts educativos sobre hipertensão"
    """
    if not current_user.can_access_clinic(clinic_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # TODO: Integrate with agent orchestration
    return {
        "success": True,
        "plan_id": "plan-001",
        "goal": data.goal,
        "status": "pending",
        "message": "Goal received. Execution plan will be created.",
    }


@router.get("/plans/{plan_id}")
async def get_plan_status(
    plan_id: str,
    current_user: CurrentUser = None,
):
    """Get execution plan status."""
    # TODO: Fetch from database
    return {
        "plan_id": plan_id,
        "goal": "Example goal",
        "status": "completed",
        "subtasks": [
            {"id": "1", "agent": "researcher", "task": "Research", "status": "completed"},
            {"id": "2", "agent": "copywriter", "task": "Write copy", "status": "completed"},
        ],
    }


@router.post("/workflow")
async def run_workflow(
    data: WorkflowRequest,
    clinic_id: str = Query(..., description="Clinic UUID"),
    current_user: CurrentUser = None,
):
    """
    Run a predefined workflow.

    Available workflows:
    - content_creation: Research → Copy → Design → Review
    - lead_qualification: Qualify lead and schedule if hot
    - clinic_onboarding: Setup new clinic
    """
    if not current_user.can_access_clinic(clinic_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # TODO: Execute workflow
    return {
        "success": True,
        "execution_id": "exec-001",
        "workflow_id": data.workflow_id,
        "status": "running",
    }


@router.post("/message")
async def process_message(
    data: MessageRequest,
    clinic_id: str | None = Query(None),
    current_user: CurrentUser = None,
):
    """
    Process a message through the agent coordinator.

    Routes to appropriate agent based on content and context.
    """
    if clinic_id and not current_user.can_access_clinic(clinic_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # TODO: Route to appropriate agent
    return {
        "success": True,
        "content": "Resposta do agente...",
        "agent": "coordinator",
        "needs_human": False,
    }


@router.get("/available")
async def list_available_agents(current_user: CurrentUser = None):
    """List available agents and workflows."""
    return {
        "agents": [
            {
                "name": "researcher",
                "description": "Pesquisa tendências e virais",
                "capabilities": ["Research", "Trend analysis", "Competitor analysis"],
            },
            {
                "name": "copywriter",
                "description": "Cria copies para redes sociais",
                "capabilities": ["Instagram posts", "Carousels", "Reels scripts"],
            },
            {
                "name": "designer",
                "description": "Gera imagens e artes",
                "capabilities": ["Social media posts", "Stories", "Ads"],
            },
            {
                "name": "sdr",
                "description": "Qualifica leads e agenda reuniões",
                "capabilities": ["Lead qualification", "Meeting scheduling", "Follow-up"],
            },
            {
                "name": "support",
                "description": "Atendimento ao paciente",
                "capabilities": ["FAQ", "Appointment info", "Post-consultation"],
            },
        ],
        "workflows": [
            {
                "id": "content_creation",
                "name": "Criação de Conteúdo",
                "description": "Pipeline: Pesquisa → Copy → Design → Revisão",
            },
            {
                "id": "lead_qualification",
                "name": "Qualificação de Lead",
                "description": "Qualifica e agenda se quente",
            },
            {
                "id": "clinic_onboarding",
                "name": "Onboarding de Clínica",
                "description": "Setup completo de nova clínica",
            },
        ],
    }
