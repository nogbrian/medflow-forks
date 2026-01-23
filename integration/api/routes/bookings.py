"""API routes for bookings - proxies to Cal.com."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import require_auth
from core.logging import get_logger
from tools.calendar import (
    verificar_disponibilidade,
    agendar_consulta,
    cancelar_consulta,
    listar_consultas,
    get_calcom_service,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/bookings", tags=["Bookings"], dependencies=[Depends(require_auth)])


class BookingCreate(BaseModel):
    lead_id: str
    horario: str  # ISO format datetime
    nome: str
    email: str
    telefone: str
    event_type_id: int | None = None
    notas: str = ""


class BookingReschedule(BaseModel):
    new_start: str  # ISO format datetime
    motivo: str = ""


class BookingCancel(BaseModel):
    motivo: str = ""


@router.get("/availability")
async def get_availability(
    data: str | None = Query(None, description="Date (YYYY-MM-DD)"),
    event_type_id: int | None = Query(None, description="Event type ID"),
) -> dict:
    """Get available time slots for scheduling."""
    slots = await verificar_disponibilidade(
        event_type_id=event_type_id,
        data=data,
    )
    return {"data": slots, "total": len(slots)}


@router.get("/event-types")
async def list_event_types() -> dict:
    """List available consultation types."""
    service = get_calcom_service()
    event_types = await service.buscar_event_types()
    return {"data": event_types}


@router.get("")
async def list_bookings(
    data_inicio: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    data_fim: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status"),
) -> dict:
    """List bookings in a date range."""
    service = get_calcom_service()
    bookings = await service.listar_agendamentos(
        date_from=data_inicio,
        date_to=data_fim,
        status=status,
    )
    return {"data": bookings, "total": len(bookings)}


@router.post("", status_code=201)
async def create_booking(body: BookingCreate) -> dict:
    """Create a new appointment."""
    booking = await agendar_consulta(
        lead_id=body.lead_id,
        horario=body.horario,
        nome=body.nome,
        email=body.email,
        telefone=body.telefone,
        event_type_id=body.event_type_id,
        notas=body.notas,
    )
    if not booking:
        raise HTTPException(status_code=500, detail="Failed to create booking")
    return {"data": booking}


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    body: BookingCancel | None = None,
) -> dict:
    """Cancel a booking."""
    motivo = body.motivo if body else ""
    success = await cancelar_consulta(booking_id=booking_id, motivo=motivo)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel booking")
    return {"status": "cancelled", "booking_id": booking_id}


@router.patch("/{booking_id}/reschedule")
async def reschedule_booking(
    booking_id: int,
    body: BookingReschedule,
) -> dict:
    """Reschedule a booking."""
    service = get_calcom_service()
    result = await service.reagendar(
        booking_id=booking_id,
        new_start=body.new_start,
        reschedule_reason=body.motivo,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to reschedule booking")
    return {"data": result}
