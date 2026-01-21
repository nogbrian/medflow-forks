"""
Appointment Scheduler Agent.

Intelligently schedules appointments by:
- Detecting scheduling intent in conversations
- Checking available slots
- Handling rescheduling and cancellations
- Sending confirmations
"""

from datetime import datetime, timedelta
from typing import Any

from agno.agent import Agent
from agno.tools import tool

from agents.base import get_db, get_model
from core.logging import get_logger

logger = get_logger(__name__)

APPOINTMENT_SCHEDULER_PROMPT = """Você é um assistente especializado em agendamento de consultas médicas.

## Suas Responsabilidades

1. **Detectar Intenção de Agendamento**
   - Identificar quando o paciente quer marcar consulta
   - Entender preferências de data/horário
   - Detectar pedidos de remarcação ou cancelamento

2. **Verificar Disponibilidade**
   - Use a ferramenta `check_availability` para ver horários disponíveis
   - Ofereça 3-5 opções de horário
   - Considere preferências do paciente (manhã/tarde/noite)

3. **Criar Agendamento**
   - Use `create_appointment` após confirmação do paciente
   - Sempre confirme os detalhes antes de finalizar
   - Envie mensagem de confirmação

4. **Gerenciar Mudanças**
   - Processe pedidos de remarcação
   - Trate cancelamentos com empatia
   - Ofereça alternativas quando possível

## Fluxo de Agendamento

1. Paciente expressa interesse em agendar
2. Pergunte tipo de consulta se não especificado
3. Verifique disponibilidade
4. Apresente opções de horário
5. Confirme escolha do paciente
6. Crie agendamento
7. Envie confirmação com detalhes

## Tipos de Consulta
- first_visit: Primeira consulta/avaliação
- follow_up: Retorno
- procedure: Procedimento
- exam: Exame
- online: Teleconsulta

## Respostas

Seja sempre:
- Cordial e profissional
- Claro sobre horários disponíveis
- Flexível para acomodar preferências
- Proativo em confirmar detalhes

Evite:
- Agendar sem confirmação explícita
- Oferecer horários muito distantes sem necessidade
- Ser robótico nas interações
"""


@tool(name="check_availability")
async def check_availability(
    clinic_id: str,
    date_from: str,
    date_to: str,
    appointment_type: str = "first_visit",
) -> dict[str, Any]:
    """
    Check available appointment slots for a clinic.

    Args:
        clinic_id: The clinic UUID
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        appointment_type: Type of appointment

    Returns:
        Dictionary with available slots
    """
    # This would integrate with Google Calendar or internal scheduling
    # For now, return mock data
    from datetime import datetime, timedelta

    slots = []
    start = datetime.fromisoformat(date_from)
    end = datetime.fromisoformat(date_to)

    current = start
    while current <= end:
        # Skip weekends
        if current.weekday() < 5:
            # Morning slots
            for hour in [9, 10, 11]:
                slots.append({
                    "datetime": current.replace(hour=hour, minute=0).isoformat(),
                    "duration_minutes": 30,
                    "available": True,
                })
            # Afternoon slots
            for hour in [14, 15, 16, 17]:
                slots.append({
                    "datetime": current.replace(hour=hour, minute=0).isoformat(),
                    "duration_minutes": 30,
                    "available": True,
                })
        current += timedelta(days=1)

    return {
        "clinic_id": clinic_id,
        "date_range": {"from": date_from, "to": date_to},
        "appointment_type": appointment_type,
        "available_slots": slots[:10],  # Limit to 10 slots
        "total_available": len(slots),
    }


@tool(name="create_appointment")
async def create_appointment(
    clinic_id: str,
    contact_id: str,
    scheduled_at: str,
    appointment_type: str,
    title: str | None = None,
    notes: str | None = None,
    duration_minutes: int = 30,
) -> dict[str, Any]:
    """
    Create a new appointment.

    Args:
        clinic_id: The clinic UUID
        contact_id: The contact UUID
        scheduled_at: ISO datetime string
        appointment_type: Type (first_visit, follow_up, procedure, exam, online)
        title: Optional title
        notes: Optional notes
        duration_minutes: Duration in minutes

    Returns:
        Created appointment details
    """
    from uuid import uuid4

    # This would create in database and sync with Google Calendar
    appointment_id = str(uuid4())

    return {
        "success": True,
        "appointment": {
            "id": appointment_id,
            "clinic_id": clinic_id,
            "contact_id": contact_id,
            "scheduled_at": scheduled_at,
            "appointment_type": appointment_type,
            "title": title,
            "notes": notes,
            "duration_minutes": duration_minutes,
            "status": "scheduled",
        },
        "message": f"Consulta agendada com sucesso para {scheduled_at}",
    }


@tool(name="cancel_appointment")
async def cancel_appointment(
    appointment_id: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Cancel an existing appointment.

    Args:
        appointment_id: The appointment UUID
        reason: Optional cancellation reason

    Returns:
        Cancellation result
    """
    return {
        "success": True,
        "appointment_id": appointment_id,
        "status": "cancelled",
        "reason": reason,
        "message": "Consulta cancelada com sucesso.",
    }


@tool(name="reschedule_appointment")
async def reschedule_appointment(
    appointment_id: str,
    new_datetime: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Reschedule an existing appointment.

    Args:
        appointment_id: The appointment UUID
        new_datetime: New ISO datetime string
        reason: Optional reason for rescheduling

    Returns:
        Rescheduling result
    """
    return {
        "success": True,
        "appointment_id": appointment_id,
        "old_datetime": "previous_datetime",  # Would come from DB
        "new_datetime": new_datetime,
        "status": "rescheduled",
        "message": f"Consulta remarcada para {new_datetime}",
    }


def create_appointment_scheduler(clinic_id: str) -> Agent:
    """Create appointment scheduler agent for a specific clinic."""
    return Agent(
        name="appointment_scheduler",
        model=get_model("smart"),
        instructions=APPOINTMENT_SCHEDULER_PROMPT,
        tools=[
            check_availability,
            create_appointment,
            cancel_appointment,
            reschedule_appointment,
        ],
        db=get_db(),
        add_history_to_context=True,
        num_history_runs=10,
        session_id=f"appointment_scheduler_{clinic_id}",
    )


async def detect_scheduling_intent(message: str) -> dict[str, Any]:
    """
    Detect if a message contains scheduling intent.

    Returns:
        Dictionary with intent analysis
    """
    scheduling_keywords = [
        "agendar",
        "marcar",
        "consulta",
        "horário",
        "disponibilidade",
        "atendimento",
        "remarcar",
        "cancelar",
        "desmarcar",
        "quando posso",
        "qual dia",
        "tem vaga",
    ]

    message_lower = message.lower()
    detected_keywords = [kw for kw in scheduling_keywords if kw in message_lower]

    has_intent = len(detected_keywords) > 0

    # Detect specific intent type
    intent_type = None
    if has_intent:
        if any(kw in message_lower for kw in ["cancelar", "desmarcar"]):
            intent_type = "cancel"
        elif any(kw in message_lower for kw in ["remarcar", "mudar", "trocar"]):
            intent_type = "reschedule"
        else:
            intent_type = "schedule"

    return {
        "has_intent": has_intent,
        "intent_type": intent_type,
        "detected_keywords": detected_keywords,
        "confidence": min(len(detected_keywords) * 0.3, 1.0),
    }
