"""Atendente de Médicos - Handles patient inquiries for medical clients."""

from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.tools import tool

from config import get_settings
from tools import (
    WhatsAppService,
    agendar_consulta,
    buscar_contexto_cliente,
    buscar_lead,
    cancelar_consulta,
    criar_lead,
    listar_consultas,
    mover_pipeline,
    verificar_disponibilidade,
)

from .base import get_db, get_model

settings = get_settings()

# Load directive template
directive_path = Path(__file__).parent.parent / "config" / "directives" / "atendente_medicos.md"
directive_template = directive_path.read_text() if directive_path.exists() else ""


def create_atendente_medicos(
    cliente_id: str,
    contexto: dict[str, Any] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> Agent:
    """
    Create a patient attendant agent customized for a specific medical client.

    Args:
        cliente_id: The medical client's UUID
        contexto: Optional pre-loaded context (to avoid extra DB call)
        user_id: User ID for memory (typically phone number)
        session_id: Session ID for conversation history

    Returns:
        Configured Agent instance
    """
    import asyncio

    # Load context if not provided
    if contexto is None:
        contexto = asyncio.get_event_loop().run_until_complete(
            buscar_contexto_cliente(cliente_id)
        )

    if not contexto:
        raise ValueError(f"Client context not found for {cliente_id}")

    # Inject context into directive
    ctx = contexto.get("contexto", {})
    atendimento = ctx.get("atendimento", {})

    directive = directive_template.format(
        tratamento=atendimento.get("tratamento", "Dr(a)."),
        assinatura=atendimento.get("assinatura", "Consultório"),
        tom_voz=atendimento.get("tom_voz", "acolhedor_profissional"),
        mensagem_boas_vindas=atendimento.get("mensagem_boas_vindas", ""),
        instrucoes_especiais=atendimento.get("instrucoes_especiais", ""),
        consultas=ctx.get("consultas", []),
        horarios=ctx.get("horarios", {}),
        bloqueios=ctx.get("bloqueios", []),
    )

    evolution_instance = contexto.get("evolution_instance", "")
    calcom_event_type_id = contexto.get("calcom_event_type_id")

    # Define tools with client context
    @tool
    def enviar_mensagem_whatsapp(destinatario: str, mensagem: str) -> dict:
        """
        Envia uma mensagem WhatsApp para um paciente.

        Args:
            destinatario: Número de telefone do paciente (formato: 5511999999999)
            mensagem: Texto da mensagem a ser enviada

        Returns:
            Resultado com success e message_id
        """
        service = WhatsAppService()
        result = asyncio.get_event_loop().run_until_complete(
            service.enviar_mensagem(
                instance=evolution_instance,
                destinatario=destinatario,
                mensagem=mensagem,
            )
        )
        return {"success": result.success, "message_id": result.message_id}

    @tool(cache_results=True, cache_ttl=60)
    def buscar_paciente(telefone: str) -> dict | None:
        """
        Busca um paciente no CRM pelo número de telefone.

        Args:
            telefone: Número de telefone do paciente (formato: 5511999999999)

        Returns:
            Dados do paciente se encontrado, None se não existir
        """
        return asyncio.get_event_loop().run_until_complete(buscar_lead(telefone))

    @tool
    def criar_paciente(
        nome: str,
        telefone: str,
        email: str | None = None,
    ) -> dict | None:
        """
        Cria um novo registro de paciente no CRM.

        Args:
            nome: Nome completo do paciente
            telefone: Número de telefone (formato: 5511999999999)
            email: Email do paciente (opcional)

        Returns:
            Dados do paciente criado se sucesso, None se falhou
        """
        return asyncio.get_event_loop().run_until_complete(
            criar_lead({
                "nome": nome,
                "telefone": telefone,
                "email": email,
                "origem": "whatsapp_organico",
                "cliente_id": cliente_id,
            })
        )

    @tool(cache_results=True, cache_ttl=300)
    def verificar_agenda(data: str) -> list:
        """
        Verifica horários disponíveis para agendamento em uma data.

        Args:
            data: Data desejada no formato YYYY-MM-DD

        Returns:
            Lista de horários disponíveis
        """
        return asyncio.get_event_loop().run_until_complete(
            verificar_disponibilidade(
                event_type_id=calcom_event_type_id,
                data=data,
            )
        )

    @tool
    def agendar(
        lead_id: str,
        horario: str,
        nome: str,
        email: str,
        telefone: str,
        tipo_consulta: str,
    ) -> dict | None:
        """
        Agenda uma consulta para um paciente.

        Args:
            lead_id: ID do lead/paciente no CRM
            horario: Data e hora no formato ISO (YYYY-MM-DDTHH:MM:SS)
            nome: Nome do paciente
            email: Email do paciente
            telefone: Telefone do paciente
            tipo_consulta: Nome do tipo de consulta

        Returns:
            Dados do agendamento se sucesso, None se falhou
        """
        # Find consultation type for notes
        consultas = ctx.get("consultas", [])
        consulta = next((c for c in consultas if c["nome"] == tipo_consulta), {})
        notas = f"Tipo: {tipo_consulta}\nValor: R$ {consulta.get('preco', 0):.2f}"

        return asyncio.get_event_loop().run_until_complete(
            agendar_consulta(
                lead_id=lead_id,
                horario=horario,
                nome=nome,
                email=email,
                telefone=telefone,
                event_type_id=calcom_event_type_id,
                notas=notas,
            )
        )

    @tool(requires_confirmation=True)
    def cancelar(booking_id: int | None = None, uid: str | None = None, motivo: str = "") -> bool:
        """
        Cancela um agendamento.

        Args:
            booking_id: ID do agendamento no Cal.com
            uid: UID do agendamento (alternativa ao booking_id)
            motivo: Motivo do cancelamento

        Returns:
            True se cancelado com sucesso, False se falhou
        """
        return asyncio.get_event_loop().run_until_complete(
            cancelar_consulta(booking_id=booking_id, uid=uid, motivo=motivo)
        )

    @tool(cache_results=True, cache_ttl=120)
    def listar_agendamentos(data_inicio: str, data_fim: str) -> list:
        """
        Lista agendamentos em um período.

        Args:
            data_inicio: Data inicial no formato YYYY-MM-DD
            data_fim: Data final no formato YYYY-MM-DD

        Returns:
            Lista de agendamentos
        """
        return asyncio.get_event_loop().run_until_complete(
            listar_consultas(data_inicio=data_inicio, data_fim=data_fim)
        )

    @tool
    def obter_informacoes_consulta() -> dict:
        """
        Obtém informações sobre tipos de consulta, preços e formas de pagamento.

        Returns:
            Dicionário com tipos de consulta, formas de pagamento e horários
        """
        pagamentos = ctx.get("pagamentos", {})
        return {
            "tipos_consulta": ctx.get("consultas", []),
            "formas_pagamento": {
                "pix": pagamentos.get("aceita_pix", True),
                "cartao": pagamentos.get("aceita_cartao", True),
                "parcelas": pagamentos.get("parcela_ate", 3),
                "convenio": pagamentos.get("aceita_convenio", False),
            },
            "horarios_atendimento": ctx.get("horarios", {}),
        }

    # Create the agent
    return Agent(
        name=f"Atendente {atendimento.get('assinatura', 'Consultório')}",
        model=get_model("smart"),
        db=get_db(),
        instructions=directive,
        tools=[
            enviar_mensagem_whatsapp,
            buscar_paciente,
            criar_paciente,
            verificar_agenda,
            agendar,
            cancelar,
            listar_agendamentos,
            obter_informacoes_consulta,
        ],
        # Memory & Storage
        user_id=user_id,
        session_id=session_id,
        add_history_to_context=True,
        num_history_runs=10,
        # Display options
    )
