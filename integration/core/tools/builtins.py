"""Register existing tool functions into the global tool registry.

This module bridges the existing tool implementations in integration/tools/
with the new ToolRegistry system used by the AgenticLoop.
"""

from __future__ import annotations

from core.tools.registry import get_global_registry
from core.logging import get_logger

logger = get_logger(__name__)


def register_all_tools() -> None:
    """Register all available tools in the global registry.

    Called during app startup to make tools available to the agentic loop.
    """
    registry = get_global_registry()

    _register_crm_tools(registry)
    _register_calendar_tools(registry)
    _register_communication_tools(registry)
    _register_content_tools(registry)

    logger.info("tools_registered", count=registry.count)


def _register_crm_tools(registry) -> None:
    """Register CRM (Twenty) tools."""
    try:
        from tools.crm import (
            buscar_leads,
            criar_lead,
            atualizar_lead,
        )

        registry.register(
            name="buscar_leads",
            description="Buscar leads no CRM por nome, telefone ou email",
            category="crm",
            idempotent=True,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Termo de busca (nome, telefone ou email)"},
                    "limit": {"type": "integer", "description": "Máximo de resultados", "default": 10},
                },
                "required": ["query"],
            },
        )(buscar_leads)

        registry.register(
            name="criar_lead",
            description="Criar novo lead no CRM com dados do contato",
            category="crm",
            parameters={
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome completo"},
                    "telefone": {"type": "string", "description": "Telefone com DDD"},
                    "email": {"type": "string", "description": "Email (opcional)"},
                    "origem": {"type": "string", "description": "Origem do lead (whatsapp, site, instagram)"},
                },
                "required": ["nome", "telefone"],
            },
        )(criar_lead)

        registry.register(
            name="atualizar_lead",
            description="Atualizar dados de um lead existente no CRM",
            category="crm",
            parameters={
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string", "description": "ID do lead no CRM"},
                    "dados": {"type": "object", "description": "Dados a atualizar"},
                },
                "required": ["lead_id", "dados"],
            },
        )(atualizar_lead)

    except (ImportError, AttributeError) as e:
        logger.debug("crm_tools_not_available", error=str(e))


def _register_calendar_tools(registry) -> None:
    """Register Calendar (Cal.com) tools."""
    try:
        from tools.calendar import (
            verificar_disponibilidade,
            criar_agendamento,
            cancelar_agendamento,
            listar_agendamentos,
        )

        registry.register(
            name="verificar_disponibilidade",
            description="Verificar horários disponíveis para agendamento",
            category="calendar",
            idempotent=True,
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                    "profissional": {"type": "string", "description": "Nome ou ID do profissional"},
                },
                "required": ["data"],
            },
        )(verificar_disponibilidade)

        registry.register(
            name="criar_agendamento",
            description="Criar um novo agendamento de consulta",
            category="calendar",
            parameters={
                "type": "object",
                "properties": {
                    "paciente_nome": {"type": "string", "description": "Nome do paciente"},
                    "paciente_telefone": {"type": "string", "description": "Telefone do paciente"},
                    "paciente_email": {"type": "string", "description": "Email do paciente"},
                    "data_hora": {"type": "string", "description": "Data e hora ISO 8601"},
                    "tipo_consulta": {"type": "string", "description": "Tipo da consulta"},
                },
                "required": ["paciente_nome", "paciente_telefone", "data_hora"],
            },
        )(criar_agendamento)

        registry.register(
            name="cancelar_agendamento",
            description="Cancelar um agendamento existente",
            category="calendar",
            requires_confirmation=True,
            parameters={
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "ID do agendamento"},
                    "motivo": {"type": "string", "description": "Motivo do cancelamento"},
                },
                "required": ["booking_id"],
            },
        )(cancelar_agendamento)

        registry.register(
            name="listar_agendamentos",
            description="Listar agendamentos de um período",
            category="calendar",
            idempotent=True,
            parameters={
                "type": "object",
                "properties": {
                    "data_inicio": {"type": "string", "description": "Data início YYYY-MM-DD"},
                    "data_fim": {"type": "string", "description": "Data fim YYYY-MM-DD"},
                },
                "required": ["data_inicio", "data_fim"],
            },
        )(listar_agendamentos)

    except (ImportError, AttributeError) as e:
        logger.debug("calendar_tools_not_available", error=str(e))


def _register_communication_tools(registry) -> None:
    """Register Communication (WhatsApp/Chatwoot) tools."""
    try:
        from tools.chatwoot import (
            sincronizar_mensagem_chatwoot,
            transferir_para_humano,
        )

        registry.register(
            name="enviar_mensagem_whatsapp",
            description="Enviar mensagem de texto via WhatsApp",
            category="communication",
            parameters={
                "type": "object",
                "properties": {
                    "telefone": {"type": "string", "description": "Número do telefone"},
                    "mensagem": {"type": "string", "description": "Conteúdo da mensagem"},
                },
                "required": ["telefone", "mensagem"],
            },
        )(sincronizar_mensagem_chatwoot)

        registry.register(
            name="transferir_para_humano",
            description="Transferir conversa para atendente humano",
            category="communication",
            requires_confirmation=True,
            parameters={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "integer", "description": "ID da conversa no Chatwoot"},
                    "motivo": {"type": "string", "description": "Motivo da transferência"},
                },
                "required": ["conversation_id", "motivo"],
            },
        )(transferir_para_humano)

    except (ImportError, AttributeError) as e:
        logger.debug("communication_tools_not_available", error=str(e))


def _register_content_tools(registry) -> None:
    """Register Content creation tools."""
    try:
        from tools.image_gen import gerar_imagem

        registry.register(
            name="gerar_imagem",
            description="Gerar imagem para post de rede social",
            category="content",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Descrição da imagem desejada"},
                    "estilo": {"type": "string", "description": "Estilo visual (moderno, clean, profissional)"},
                    "formato": {"type": "string", "enum": ["square", "story", "landscape"], "description": "Formato"},
                },
                "required": ["prompt"],
            },
        )(gerar_imagem)

    except (ImportError, AttributeError) as e:
        logger.debug("content_tools_not_available", error=str(e))
