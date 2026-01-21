"""
Agents module - MedFlow Orchestration Layer

All Agno agents and teams for the marketing agency.

Agents:
- SDR: atendente_agencia (qualifica leads da agência)
- Support: atendente_medicos (atende pacientes de clínicas)
- Researcher: pesquisador (pesquisa tendências e virais)
- Copywriter: criador_instagram (cria conteúdo)
- Reviewer: revisor (valida compliance CFM)
- SEO Analyst: seo_analyst (otimização para buscas)
- Strategist: strategist (planejamento e calendário)
- BI: bi_agent (analytics e relatórios)
- Designer: designer (geração de visuais)

CRM Agents:
- Lead Qualifier: lead_qualifier (qualificação automática de leads)
- Appointment Scheduler: appointment_scheduler (agendamento inteligente)
- Follow-up: follow_up (reengajamento automatizado)
- Coordinator: coordinator (roteamento por complexidade)

Orchestration Agents:
- Campaign Manager: campaign_manager (decomposição de objetivos complexos)
- MedFlow Agency: medflow_agency (Eigent/Workforce orchestration)

Teams:
- team_atendimento: Atendimento de leads e pacientes
- team_conteudo: Criação de conteúdo completa
- medflow_agency: Agência de Marketing Autônoma (Eigent pattern)

Tools:
- note_taking: Inter-agent communication via shared notes
- human_toolkit: Human-in-the-loop interactions
"""

from .atendente_agencia import atendente_agencia
from .atendente_medicos import create_atendente_medicos
from .criador_instagram import criador_instagram
from .pesquisador import pesquisador
from .revisor import revisor
from .seo_analyst import seo_analyst
from .strategist import strategist
from .bi_agent import bi_agent
from .designer import designer
from .team_atendimento import team_atendimento
from .team_conteudo import team_conteudo

# MedFlow Agency - Autonomous Marketing Agency (Eigent/Workforce pattern)
from .medflow_agency import (
    medflow_agency,
    create_medflow_agency,
    run_agency_task,
    run_agency_task_sync,
)

# CRM Agents
from .lead_qualifier import lead_qualifier, qualify_lead, create_lead_qualifier
from .appointment_scheduler import (
    create_appointment_scheduler,
    detect_scheduling_intent,
)
from .follow_up import (
    create_follow_up_agent,
    determine_follow_up_action,
    get_pending_follow_ups,
)
from .coordinator import (
    coordinator,
    route_message,
    should_qualify_after_response,
    AgentType,
)

# Orchestration Agents
from .campaign_manager import (
    campaign_manager,
    decompose_goal,
    decompose_goal_async,
    validate_decomposition,
    AVAILABLE_AGENTS,
)

# Agent Tools
from .tools import (
    # Note-taking
    write_note,
    append_note,
    read_note,
    list_notes,
    # Human-in-the-loop
    ask_human,
    send_message_to_user,
    request_approval,
    escalate_to_human,
    set_human_loop_controller,
)

__all__ = [
    # SDR & Support Agents
    "atendente_agencia",
    "create_atendente_medicos",
    # Content Agents
    "pesquisador",
    "criador_instagram",
    "revisor",
    "seo_analyst",
    "designer",
    # Strategy & Analytics Agents
    "strategist",
    "bi_agent",
    # CRM Agents
    "lead_qualifier",
    "qualify_lead",
    "create_lead_qualifier",
    "create_appointment_scheduler",
    "detect_scheduling_intent",
    "create_follow_up_agent",
    "determine_follow_up_action",
    "get_pending_follow_ups",
    "coordinator",
    "route_message",
    "should_qualify_after_response",
    "AgentType",
    # Orchestration Agents
    "campaign_manager",
    "decompose_goal",
    "decompose_goal_async",
    "validate_decomposition",
    "AVAILABLE_AGENTS",
    # MedFlow Agency (Eigent/Workforce)
    "medflow_agency",
    "create_medflow_agency",
    "run_agency_task",
    "run_agency_task_sync",
    # Teams
    "team_atendimento",
    "team_conteudo",
    # Agent Tools - Note-taking
    "write_note",
    "append_note",
    "read_note",
    "list_notes",
    # Agent Tools - Human-in-the-loop
    "ask_human",
    "send_message_to_user",
    "request_approval",
    "escalate_to_human",
    "set_human_loop_controller",
]
