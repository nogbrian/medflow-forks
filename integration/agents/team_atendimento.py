"""Team Atendimento - Routes messages to appropriate attendant agents."""

from agno.agent import Agent
from agno.team import Team

from config import get_settings
from tools import buscar_contexto_cliente

from .atendente_agencia import atendente_agencia, create_atendente_agencia
from .atendente_medicos import create_atendente_medicos
from .base import get_db, get_model

settings = get_settings()


def create_team_atendimento(
    instance: str,
    cliente_id: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> Agent:
    """
    Create an attendance team that routes to the appropriate agent.

    For the agency instance, routes to atendente_agencia.
    For medical client instances, creates a contextualized atendente_medicos.

    Args:
        instance: WhatsApp instance name
        cliente_id: Optional client ID (for medical client instances)
        user_id: User ID for memory (typically phone number)
        session_id: Session ID for conversation history

    Returns:
        The appropriate agent for the instance
    """
    import asyncio

    # If it's the agency instance, return the agency attendant
    if instance == settings.evolution_instance_agencia:
        return create_atendente_agencia(user_id=user_id, session_id=session_id)

    # For medical client instances, we need the context
    if cliente_id:
        contexto = asyncio.get_event_loop().run_until_complete(
            buscar_contexto_cliente(cliente_id)
        )
        if contexto:
            return create_atendente_medicos(
                cliente_id=cliente_id,
                contexto=contexto,
                user_id=user_id,
                session_id=session_id,
            )

    # Fallback: return agency attendant
    return create_atendente_agencia(user_id=user_id, session_id=session_id)


# Team for routing
team_atendimento = Team(
    name="Team Atendimento",
    model=get_model("fast"),  # Fast model for routing decisions
    db=get_db(),
    members=[atendente_agencia],  # Base member, others added dynamically
    instructions="""Você é o roteador do time de atendimento.

Sua função é determinar qual agente deve atender a mensagem.

Regras de roteamento:
1. Se a instância do WhatsApp for da agência → atendente_agencia
2. Se a instância for de um médico cliente → atendente_medicos (com contexto do médico)

O contexto do médico inclui:
- Nome e especialidade
- Tom de voz personalizado
- Horários de atendimento
- Tipos de consulta e preços
- Formas de pagamento

Sempre verifique a instância antes de rotear.""",
)
