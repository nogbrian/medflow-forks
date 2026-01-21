"""Cal.com calendar integration tools."""

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CalComService:
    """Cal.com API client for scheduling."""

    def __init__(self):
        self.base_url = "https://api.cal.com/v1"
        self.api_key = settings.calcom_api_key
        self.default_event_type_id = settings.calcom_event_type_id_default

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict:
        """Make authenticated request to Cal.com API."""
        base_params = {"apiKey": self.api_key}
        if params:
            base_params.update(params)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                params=base_params,
                json=json_data,
            )

            if response.status_code >= 400:
                logger.error(
                    "Cal.com API error",
                    status=response.status_code,
                    response=response.text,
                )
                response.raise_for_status()

            return response.json()

    async def verificar_disponibilidade(
        self,
        event_type_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        timezone: str = "America/Sao_Paulo",
    ) -> list[dict[str, Any]]:
        """
        Check available time slots for scheduling.

        Args:
            event_type_id: Cal.com event type ID (uses default if not provided)
            date_from: Start date (YYYY-MM-DD), defaults to today
            date_to: End date (YYYY-MM-DD), defaults to 7 days from today
            timezone: Timezone for availability (default: America/Sao_Paulo)

        Returns:
            List of available time slots
        """
        try:
            if not date_from:
                date_from = datetime.now().strftime("%Y-%m-%d")
            if not date_to:
                date_to = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

            result = await self._request(
                method="GET",
                endpoint="/availability",
                params={
                    "eventTypeId": event_type_id or self.default_event_type_id,
                    "dateFrom": date_from,
                    "dateTo": date_to,
                    "timeZone": timezone,
                },
            )

            # Transform Cal.com response to our format
            slots = []
            for day in result.get("slots", {}):
                for slot in result["slots"][day]:
                    slots.append({
                        "data": day,
                        "inicio": slot.get("time"),
                        "disponivel": True,
                    })

            logger.info(
                "Availability checked",
                event_type_id=event_type_id or self.default_event_type_id,
                date_from=date_from,
                date_to=date_to,
                available_slots=len(slots),
            )

            return slots

        except Exception as e:
            logger.error("Failed to check availability", error=str(e))
            return []

    async def criar_agendamento(
        self,
        start: str,
        name: str,
        email: str,
        phone: str,
        event_type_id: int | None = None,
        notes: str = "",
        metadata: dict | None = None,
        timezone: str = "America/Sao_Paulo",
    ) -> dict | None:
        """
        Create a booking in Cal.com.

        Args:
            start: Start datetime (ISO format)
            name: Attendee name
            email: Attendee email
            phone: Attendee phone
            event_type_id: Cal.com event type ID (uses default if not provided)
            notes: Additional notes for the booking
            metadata: Custom metadata (e.g., lead_id)
            timezone: Timezone for the booking

        Returns:
            Created booking data if successful, None otherwise
        """
        try:
            booking_data = {
                "eventTypeId": event_type_id or self.default_event_type_id,
                "start": start,
                "responses": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "notes": notes,
                },
                "timeZone": timezone,
                "language": "pt-BR",
            }

            if metadata:
                booking_data["metadata"] = metadata

            result = await self._request(
                method="POST",
                endpoint="/bookings",
                json_data=booking_data,
            )

            logger.info(
                "Booking created",
                booking_id=result.get("id"),
                uid=result.get("uid"),
                attendee=name,
            )

            return {
                "id": result.get("id"),
                "uid": result.get("uid"),
                "titulo": result.get("title"),
                "inicio": result.get("startTime"),
                "fim": result.get("endTime"),
                "link": result.get("metadata", {}).get("videoCallUrl"),
                "status": result.get("status"),
            }

        except Exception as e:
            logger.error("Failed to create booking", error=str(e))
            return None

    async def cancelar_agendamento(
        self,
        booking_id: int | None = None,
        uid: str | None = None,
        cancellation_reason: str = "",
    ) -> bool:
        """
        Cancel a booking.

        Args:
            booking_id: Cal.com booking ID
            uid: Cal.com booking UID (alternative to booking_id)
            cancellation_reason: Reason for cancellation

        Returns:
            True if successful, False otherwise
        """
        try:
            if not booking_id and not uid:
                logger.error("Either booking_id or uid is required")
                return False

            endpoint = f"/bookings/{booking_id}" if booking_id else f"/bookings/{uid}"

            await self._request(
                method="DELETE",
                endpoint=endpoint,
                json_data={"cancellationReason": cancellation_reason},
            )

            logger.info("Booking cancelled", booking_id=booking_id, uid=uid)
            return True

        except Exception as e:
            logger.error("Failed to cancel booking", error=str(e))
            return False

    async def reagendar(
        self,
        booking_id: int | None = None,
        uid: str | None = None,
        new_start: str = "",
        reschedule_reason: str = "",
    ) -> dict | None:
        """
        Reschedule a booking.

        Args:
            booking_id: Cal.com booking ID
            uid: Cal.com booking UID
            new_start: New start datetime (ISO format)
            reschedule_reason: Reason for rescheduling

        Returns:
            Updated booking data if successful, None otherwise
        """
        try:
            if not booking_id and not uid:
                logger.error("Either booking_id or uid is required")
                return None

            endpoint = f"/bookings/{booking_id}" if booking_id else f"/bookings/{uid}"

            result = await self._request(
                method="PATCH",
                endpoint=endpoint,
                json_data={
                    "start": new_start,
                    "reschedulingReason": reschedule_reason,
                },
            )

            logger.info(
                "Booking rescheduled",
                booking_id=booking_id,
                uid=uid,
                new_start=new_start,
            )

            return {
                "id": result.get("id"),
                "uid": result.get("uid"),
                "inicio": result.get("startTime"),
                "fim": result.get("endTime"),
                "status": result.get("status"),
            }

        except Exception as e:
            logger.error("Failed to reschedule booking", error=str(e))
            return None

    async def listar_agendamentos(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List bookings in a date range.

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            status: Filter by status (ACCEPTED, PENDING, CANCELLED, REJECTED)

        Returns:
            List of bookings
        """
        try:
            params = {}
            if date_from:
                params["dateFrom"] = date_from
            if date_to:
                params["dateTo"] = date_to
            if status:
                params["status"] = status

            result = await self._request(
                method="GET",
                endpoint="/bookings",
                params=params,
            )

            bookings = []
            for booking in result.get("bookings", []):
                bookings.append({
                    "id": booking.get("id"),
                    "uid": booking.get("uid"),
                    "titulo": booking.get("title"),
                    "inicio": booking.get("startTime"),
                    "fim": booking.get("endTime"),
                    "status": booking.get("status"),
                    "attendees": [
                        {"nome": a.get("name"), "email": a.get("email")}
                        for a in booking.get("attendees", [])
                    ],
                    "metadata": booking.get("metadata", {}),
                })

            logger.info("Bookings listed", count=len(bookings))
            return bookings

        except Exception as e:
            logger.error("Failed to list bookings", error=str(e))
            return []

    async def buscar_event_types(self) -> list[dict[str, Any]]:
        """
        List available event types (consultation types).

        Returns:
            List of event types with their IDs and configurations
        """
        try:
            result = await self._request(
                method="GET",
                endpoint="/event-types",
            )

            event_types = []
            for et in result.get("event_types", []):
                event_types.append({
                    "id": et.get("id"),
                    "titulo": et.get("title"),
                    "slug": et.get("slug"),
                    "duracao_minutos": et.get("length"),
                    "descricao": et.get("description"),
                    "preco": et.get("price"),
                })

            logger.info("Event types listed", count=len(event_types))
            return event_types

        except Exception as e:
            logger.error("Failed to list event types", error=str(e))
            return []


@lru_cache
def get_calcom_service() -> CalComService:
    """Get cached CalComService instance."""
    return CalComService()


# Convenience functions for tools
async def verificar_disponibilidade(
    event_type_id: int | None = None,
    data: str | None = None,
) -> list[dict[str, Any]]:
    """
    Check available time slots for a given date.

    Args:
        event_type_id: Cal.com event type ID
        data: Date to check (YYYY-MM-DD)

    Returns:
        List of available time slots
    """
    service = get_calcom_service()
    return await service.verificar_disponibilidade(
        event_type_id=event_type_id,
        date_from=data,
        date_to=data,
    )


async def agendar_consulta(
    lead_id: str,
    horario: str,
    nome: str,
    email: str,
    telefone: str,
    event_type_id: int | None = None,
    notas: str = "",
) -> dict | None:
    """
    Schedule an appointment.

    Args:
        lead_id: Lead ID for reference
        horario: Appointment datetime (ISO format)
        nome: Patient name
        email: Patient email
        telefone: Patient phone
        event_type_id: Cal.com event type ID
        notas: Additional notes

    Returns:
        Created booking data if successful, None otherwise
    """
    service = get_calcom_service()
    return await service.criar_agendamento(
        start=horario,
        name=nome,
        email=email,
        phone=telefone,
        event_type_id=event_type_id,
        notes=notas,
        metadata={"lead_id": lead_id},
    )


async def cancelar_consulta(
    booking_id: int | None = None,
    uid: str | None = None,
    motivo: str = "",
) -> bool:
    """
    Cancel an appointment.

    Args:
        booking_id: Cal.com booking ID
        uid: Cal.com booking UID
        motivo: Cancellation reason

    Returns:
        True if successful, False otherwise
    """
    service = get_calcom_service()
    return await service.cancelar_agendamento(
        booking_id=booking_id,
        uid=uid,
        cancellation_reason=motivo,
    )


async def listar_consultas(
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> list[dict[str, Any]]:
    """
    List appointments in a date range.

    Args:
        data_inicio: Start date (YYYY-MM-DD)
        data_fim: End date (YYYY-MM-DD)

    Returns:
        List of appointments
    """
    service = get_calcom_service()
    return await service.listar_agendamentos(
        date_from=data_inicio,
        date_to=data_fim,
    )
