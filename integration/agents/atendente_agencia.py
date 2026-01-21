"""Atendente da Agência - Handles agency leads."""

from pathlib import Path

from agno.agent import Agent
from agno.tools import tool

from config import get_settings
from tools import (
    WhatsAppService,
    buscar_lead,
    criar_lead,
    mover_pipeline,
    notificar_esposa,
    verificar_disponibilidade,
)

from .base import get_db, get_model

settings = get_settings()

# Load directive
directive_path = Path(__file__).parent.parent / "config" / "directives" / "atendente_agencia.md"
directive = directive_path.read_text() if directive_path.exists() else ""


# Define tools for the agent
@tool
def enviar_mensagem_whatsapp(destinatario: str, mensagem: str) -> dict:
    """
    Envia uma mensagem WhatsApp para um lead.

    Args:
        destinatario: Número de telefone do destinatário (formato: 5511999999999)
        mensagem: Texto da mensagem a ser enviada

    Returns:
        Resultado com success e message_id
    """
    import asyncio

    service = WhatsAppService()
    result = asyncio.get_event_loop().run_until_complete(
        service.enviar_mensagem(
            instance=settings.evolution_instance_agencia,
            destinatario=destinatario,
            mensagem=mensagem,
        )
    )
    return {"success": result.success, "message_id": result.message_id}


@tool(cache_results=True, cache_ttl=60)
def buscar_lead_crm(telefone: str) -> dict | None:
    """
    Busca um lead no CRM pelo número de telefone.

    Args:
        telefone: Número de telefone do lead (formato: 5511999999999)

    Returns:
        Dados do lead se encontrado, None se não existir
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(buscar_lead(telefone))


@tool
def criar_lead_crm(
    nome: str,
    telefone: str,
    email: str | None = None,
    origem: str = "whatsapp_organico",
) -> dict | None:
    """
    Cria um novo lead no CRM.

    Args:
        nome: Nome completo do lead
        telefone: Número de telefone (formato: 5511999999999)
        email: Email do lead (opcional)
        origem: Origem do lead (whatsapp_organico, lp, indicacao, etc)

    Returns:
        Dados do lead criado se sucesso, None se falhou
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        criar_lead({
            "nome": nome,
            "telefone": telefone,
            "email": email,
            "origem": origem,
        })
    )


@tool(requires_confirmation=True)
def mover_lead_pipeline(lead_id: str, etapa: str) -> bool:
    """
    Move um lead para uma etapa diferente do pipeline.

    Args:
        lead_id: ID do lead no CRM
        etapa: Nova etapa (novo, qualificado, agendado, fechado, perdido)

    Returns:
        True se movido com sucesso, False se falhou
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(mover_pipeline(lead_id, etapa))


@tool(cache_results=True, cache_ttl=300)
def verificar_agenda_disponivel(data: str) -> list:
    """
    Verifica horários disponíveis para agendamento em uma data.

    Args:
        data: Data desejada no formato YYYY-MM-DD

    Returns:
        Lista de horários disponíveis
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        verificar_disponibilidade(data=data)
    )


@tool
def notificar_equipe_comercial(
    mensagem: str,
    lead_id: str | None = None,
    tipo: str = "info",
) -> bool:
    """
    Notifica a equipe comercial sobre um lead.

    Args:
        mensagem: Mensagem para a equipe
        lead_id: ID do lead relacionado (opcional)
        tipo: Tipo de notificação (info, urgente, lead_quente)

    Returns:
        True se notificado com sucesso
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        notificar_esposa(mensagem, lead_id, tipo)
    )


def create_atendente_agencia(
    user_id: str | None = None,
    session_id: str | None = None,
) -> Agent:
    """
    Create an agency attendant agent with memory and storage.

    Args:
        user_id: User ID for memory (typically phone number)
        session_id: Session ID for conversation history

    Returns:
        Configured Agent instance
    """
    return Agent(
        name="Atendente Agência",
        model=get_model("smart"),
        db=get_db(),
        instructions=directive,
        tools=[
            enviar_mensagem_whatsapp,
            buscar_lead_crm,
            criar_lead_crm,
            mover_lead_pipeline,
            verificar_agenda_disponivel,
            notificar_equipe_comercial,
        ],
        # Memory & Storage
        user_id=user_id,
        session_id=session_id,
        add_history_to_context=True,
        num_history_runs=10,
        # Display options
    )


# Default agent instance (for backwards compatibility)
# For production use, prefer create_atendente_agencia() with user_id
atendente_agencia = Agent(
    name="Atendente Agência",
    model=get_model("smart"),
    db=get_db(),
    instructions=directive,
    tools=[
        enviar_mensagem_whatsapp,
        buscar_lead_crm,
        criar_lead_crm,
        mover_lead_pipeline,
        verificar_agenda_disponivel,
        notificar_equipe_comercial,
    ],
    add_history_to_context=True,
    num_history_runs=10,
)
