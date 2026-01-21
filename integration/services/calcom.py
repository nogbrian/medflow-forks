"""
Cal.com API Client.

Handles scheduling integration:
- Event types (appointment templates)
- Bookings (appointments)
- Availability
- Teams (multi-tenant)

Docs: https://cal.com/docs/enterprise-features/api/api-reference
"""

import logging
from datetime import datetime
from typing import Any

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CalcomAPIError(Exception):
    """Cal.com API error."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class CalcomClient:
    """
    HTTP client for Cal.com REST API.

    Usage:
        client = CalcomClient(api_key="...")
        bookings = await client.list_bookings()
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or settings.calcom_api_key
        self.base_url = (base_url or settings.calcom_api_url).rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict:
        """Make HTTP request to Cal.com API."""
        client = await self._get_client()
        url = f"{self.api_url}{path}"

        # Add API key to params if using query-based auth
        if params is None:
            params = {}
        if self.api_key and "apiKey" not in params:
            params["apiKey"] = self.api_key

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            try:
                error_json = e.response.json()
                error_body = error_json.get("message", error_body)
            except Exception:
                pass
            raise CalcomAPIError(
                f"HTTP {e.response.status_code}: {error_body}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise CalcomAPIError(f"Request failed: {str(e)}")

    # =========================================================================
    # EVENT TYPES
    # =========================================================================

    async def list_event_types(self, team_id: int | None = None) -> list[dict]:
        """List available event types (appointment templates)."""
        params = {}
        if team_id:
            params["teamId"] = team_id
        data = await self._request("GET", "/event-types", params=params)
        return data.get("event_types", data.get("eventTypes", []))

    async def get_event_type(self, event_type_id: int) -> dict:
        """Get event type by ID."""
        data = await self._request("GET", f"/event-types/{event_type_id}")
        return data.get("event_type", data.get("eventType", data))

    async def create_event_type(
        self,
        title: str,
        slug: str,
        length: int = 30,
        description: str = "",
        team_id: int | None = None,
        **extra_fields,
    ) -> dict:
        """Create a new event type."""
        payload = {
            "title": title,
            "slug": slug,
            "length": length,
            "description": description,
            **extra_fields,
        }
        if team_id:
            payload["teamId"] = team_id

        return await self._request("POST", "/event-types", json_data=payload)

    # =========================================================================
    # BOOKINGS
    # =========================================================================

    async def list_bookings(
        self,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        List bookings with optional filters.

        Status: upcoming, recurring, past, cancelled, unconfirmed
        """
        params: dict[str, Any] = {"take": limit}
        if status:
            params["status"] = status
        if start_date:
            params["afterStart"] = start_date.isoformat()
        if end_date:
            params["beforeEnd"] = end_date.isoformat()

        data = await self._request("GET", "/bookings", params=params)
        return data.get("bookings", [])

    async def get_booking(self, booking_id: int | str) -> dict:
        """Get booking by ID or UID."""
        data = await self._request("GET", f"/bookings/{booking_id}")
        return data.get("booking", data)

    async def create_booking(
        self,
        event_type_id: int,
        start: datetime,
        attendee_email: str,
        attendee_name: str,
        attendee_phone: str | None = None,
        metadata: dict | None = None,
        **extra_fields,
    ) -> dict:
        """Create a new booking."""
        payload = {
            "eventTypeId": event_type_id,
            "start": start.isoformat(),
            "responses": {
                "email": attendee_email,
                "name": attendee_name,
            },
            **extra_fields,
        }
        if attendee_phone:
            payload["responses"]["phone"] = attendee_phone
        if metadata:
            payload["metadata"] = metadata

        return await self._request("POST", "/bookings", json_data=payload)

    async def cancel_booking(
        self,
        booking_id: int | str,
        cancellation_reason: str = "",
    ) -> dict:
        """Cancel a booking."""
        payload = {}
        if cancellation_reason:
            payload["cancellationReason"] = cancellation_reason

        return await self._request("DELETE", f"/bookings/{booking_id}", json_data=payload)

    async def reschedule_booking(
        self,
        booking_id: int | str,
        new_start: datetime,
        reschedule_reason: str = "",
    ) -> dict:
        """Reschedule a booking."""
        payload = {
            "start": new_start.isoformat(),
        }
        if reschedule_reason:
            payload["rescheduleReason"] = reschedule_reason

        return await self._request("PATCH", f"/bookings/{booking_id}", json_data=payload)

    # =========================================================================
    # AVAILABILITY
    # =========================================================================

    async def get_availability(
        self,
        event_type_id: int,
        start_time: datetime,
        end_time: datetime,
        timezone: str = "America/Sao_Paulo",
    ) -> dict:
        """Get available time slots for an event type."""
        params = {
            "eventTypeId": event_type_id,
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "timeZone": timezone,
        }
        return await self._request("GET", "/slots", params=params)

    # =========================================================================
    # TEAMS (Multi-tenant)
    # =========================================================================

    async def list_teams(self) -> list[dict]:
        """List teams the user belongs to."""
        data = await self._request("GET", "/teams")
        return data.get("teams", [])

    async def create_team(
        self,
        name: str,
        slug: str,
        bio: str = "",
    ) -> dict:
        """Create a new team."""
        payload = {
            "name": name,
            "slug": slug,
            "bio": bio,
        }
        return await self._request("POST", "/teams", json_data=payload)

    async def add_team_member(
        self,
        team_id: int,
        user_id: int,
        role: str = "MEMBER",
    ) -> dict:
        """Add a member to a team."""
        payload = {
            "userId": user_id,
            "role": role,
        }
        return await self._request("POST", f"/teams/{team_id}/members", json_data=payload)

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    async def list_webhooks(self) -> list[dict]:
        """List registered webhooks."""
        data = await self._request("GET", "/webhooks")
        return data.get("webhooks", [])

    async def create_webhook(
        self,
        subscriber_url: str,
        event_triggers: list[str],
        active: bool = True,
    ) -> dict:
        """
        Register a webhook.

        Event triggers:
        - BOOKING_CREATED
        - BOOKING_RESCHEDULED
        - BOOKING_CANCELLED
        - MEETING_ENDED
        """
        payload = {
            "subscriberUrl": subscriber_url,
            "eventTriggers": event_triggers,
            "active": active,
        }
        return await self._request("POST", "/webhooks", json_data=payload)
