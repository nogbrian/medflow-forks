"""
Follow-up Agent.

Manages automated follow-up sequences for leads and patients:
- Sends timely reminders
- Re-engages cold leads
- Nurtures warm leads
- Post-appointment follow-ups
"""

from datetime import datetime, timedelta
from typing import Any

from agno.agent import Agent
from agno.tools import tool

from agents.base import get_db, get_model
from core.logging import get_logger

logger = get_logger(__name__)

FOLLOW_UP_PROMPT = """Você é um especialista em follow-up e reativação de leads para clínicas médicas.

## Objetivo
Criar mensagens de follow-up personalizadas que reengajem leads de forma natural e não invasiva.

## Tipos de Follow-up

### 1. Lead Frio (Sem resposta há 3+ dias)
- Tom: Amigável, sem pressão
- Objetivo: Verificar se ainda há interesse
- Exemplo: "Olá [Nome]! Tudo bem? 😊 Vi que conversamos sobre [procedimento] há alguns dias. Surgiu alguma dúvida que posso ajudar?"

### 2. Lead Morno (Mostrou interesse mas não agendou)
- Tom: Consultivo, agregando valor
- Objetivo: Oferecer mais informações e facilitar decisão
- Exemplo: "Oi [Nome]! Lembrei de você quando um paciente compartilhou os resultados do [procedimento]. Ficou incrível! Quer que eu envie algumas fotos de antes e depois?"

### 3. Lead Quente (Quase agendou)
- Tom: Urgente mas respeitoso
- Objetivo: Facilitar o agendamento
- Exemplo: "Oi [Nome]! Vi que você estava interessado em agendar sua avaliação. Consegui uma vaga especial para [dia]. Quer que eu reserve para você?"

### 4. Pós-consulta (Após atendimento)
- Tom: Cuidadoso, atencioso
- Objetivo: Garantir satisfação e próximos passos
- Exemplo: "Olá [Nome]! Como você está se sentindo após a consulta? O Dr. [Nome] pediu para eu verificar se surgiu alguma dúvida sobre o tratamento."

### 5. Reativação (Há 30+ dias sem contato)
- Tom: Casual, não invasivo
- Objetivo: Reconectar sem pressão
- Exemplo: "Oi [Nome]! Faz um tempinho que não nos falamos. Espero que esteja tudo bem! 🙂 Se ainda tiver interesse em [procedimento], temos novidades que podem te interessar."

## Regras

1. **Personalização**: Sempre use o nome e mencione detalhes específicos da conversa anterior
2. **Timing**: Não envie mais de 1 follow-up por semana para o mesmo lead
3. **Valor**: Cada mensagem deve agregar algo (informação, oferta, conteúdo)
4. **Opt-out**: Respeite quando o lead disser que não tem interesse
5. **Horário**: Evite enviar fora do horário comercial

## Output

Retorne um JSON com:
```json
{
  "should_follow_up": true,
  "follow_up_type": "warm_lead",
  "message": "Mensagem personalizada aqui",
  "timing": "now",
  "channel": "whatsapp",
  "template_id": null,
  "reasoning": "Explicação da escolha"
}
```
"""


@tool(name="get_contact_history")
async def get_contact_history(contact_id: str) -> dict[str, Any]:
    """
    Get contact's conversation and activity history.

    Args:
        contact_id: The contact UUID

    Returns:
        Contact history including messages and activities
    """
    # This would fetch from database
    return {
        "contact_id": contact_id,
        "last_message_at": (datetime.now() - timedelta(days=3)).isoformat(),
        "last_message_direction": "inbound",
        "total_messages": 8,
        "temperature": "warm",
        "interests": ["rinoplastia", "avaliação"],
        "objections": ["preço"],
        "follow_ups_sent": 1,
        "last_follow_up_at": (datetime.now() - timedelta(days=7)).isoformat(),
    }


@tool(name="get_follow_up_templates")
async def get_follow_up_templates(
    clinic_id: str,
    category: str,
) -> list[dict[str, Any]]:
    """
    Get available follow-up templates for a clinic.

    Args:
        clinic_id: The clinic UUID
        category: Template category (reactivation, follow_up, etc.)

    Returns:
        List of available templates
    """
    # This would fetch from message_templates table
    return [
        {
            "id": "tpl_1",
            "name": "Follow-up Interesse",
            "content": "Olá {{nome}}! Tudo bem? 😊 Vi que conversamos sobre {{procedimento}}. Surgiu alguma dúvida?",
            "variables": ["nome", "procedimento"],
        },
        {
            "id": "tpl_2",
            "name": "Reativação Suave",
            "content": "Oi {{nome}}! Faz um tempinho que não conversamos. Se ainda tiver interesse, temos novidades!",
            "variables": ["nome"],
        },
    ]


@tool(name="send_follow_up")
async def send_follow_up(
    contact_id: str,
    message: str,
    channel: str = "whatsapp",
    template_id: str | None = None,
    schedule_for: str | None = None,
) -> dict[str, Any]:
    """
    Send or schedule a follow-up message.

    Args:
        contact_id: The contact UUID
        message: Message content
        channel: Communication channel (whatsapp, email)
        template_id: Optional template ID for WhatsApp
        schedule_for: Optional ISO datetime to schedule

    Returns:
        Send result
    """
    return {
        "success": True,
        "contact_id": contact_id,
        "message_id": "msg_" + contact_id[:8],
        "channel": channel,
        "scheduled": schedule_for is not None,
        "scheduled_for": schedule_for,
    }


def create_follow_up_agent(clinic_id: str) -> Agent:
    """Create follow-up agent for a specific clinic."""
    return Agent(
        name="follow_up",
        model=get_model("smart"),
        instructions=FOLLOW_UP_PROMPT,
        tools=[
            get_contact_history,
            get_follow_up_templates,
            send_follow_up,
        ],
        db=get_db(),
        add_history_to_context=True,
        num_history_runs=5,
        session_id=f"follow_up_{clinic_id}",
    )


async def determine_follow_up_action(
    contact_id: str,
    contact_data: dict,
    last_messages: list[dict],
) -> dict[str, Any]:
    """
    Determine the best follow-up action for a contact.

    Args:
        contact_id: Contact UUID
        contact_data: Contact information
        last_messages: Recent messages from conversation

    Returns:
        Follow-up recommendation
    """
    now = datetime.now()
    last_contact = contact_data.get("last_contact_at")

    if last_contact:
        if isinstance(last_contact, str):
            last_contact = datetime.fromisoformat(last_contact.replace("Z", "+00:00"))
        days_since_contact = (now - last_contact.replace(tzinfo=None)).days
    else:
        days_since_contact = 999

    temperature = contact_data.get("temperature", "cold")
    has_appointment = contact_data.get("has_appointment", False)

    # Determine follow-up type
    if has_appointment:
        return {
            "should_follow_up": False,
            "reason": "Contact has scheduled appointment",
        }

    if days_since_contact < 1:
        return {
            "should_follow_up": False,
            "reason": "Recent contact, wait before following up",
        }

    if temperature == "hot" and days_since_contact >= 1:
        return {
            "should_follow_up": True,
            "follow_up_type": "hot_lead",
            "urgency": "high",
            "recommended_timing": "immediate",
        }

    if temperature == "warm" and days_since_contact >= 3:
        return {
            "should_follow_up": True,
            "follow_up_type": "warm_lead",
            "urgency": "medium",
            "recommended_timing": "today",
        }

    if temperature == "cold" and days_since_contact >= 7:
        return {
            "should_follow_up": True,
            "follow_up_type": "reactivation",
            "urgency": "low",
            "recommended_timing": "this_week",
        }

    return {
        "should_follow_up": False,
        "reason": f"Wait until {7 - days_since_contact} more days",
    }


async def get_pending_follow_ups(clinic_id: str, limit: int = 50) -> list[dict]:
    """
    Get contacts that need follow-up for a clinic.

    Args:
        clinic_id: Clinic UUID
        limit: Maximum number of contacts to return

    Returns:
        List of contacts needing follow-up with recommendations
    """
    # This would query the database for contacts
    # that haven't been contacted recently and don't have appointments
    return []
