"""Twenty CRM integration tools."""

import json
import re
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _sanitize_phone(phone: str) -> str:
    """Sanitize phone number - keep only digits and +."""
    return re.sub(r"[^\d+]", "", phone)[:20]


def _sanitize_filter_value(value: Any) -> Any:
    """
    Sanitize a filter value to prevent injection.

    Only allows: strings (alphanumeric, spaces, basic punctuation), numbers, booleans.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        # Remove any JSON-breaking characters and limit length
        sanitized = re.sub(r'["\\\x00-\x1f]', "", value)[:200]
        return sanitized
    return str(value)[:200]


def _build_filter_json(filters: dict[str, Any]) -> str:
    """
    Safely build a JSON filter string for Twenty CRM API.

    Uses json.dumps to ensure proper escaping instead of string interpolation.
    """
    if not filters:
        return "{}"

    filter_obj = {}
    for key, value in filters.items():
        # Sanitize key (alphanumeric and underscore only)
        safe_key = re.sub(r"[^\w]", "", key)[:50]
        if not safe_key:
            continue

        # Sanitize value
        safe_value = _sanitize_filter_value(value)
        filter_obj[safe_key] = {"eq": safe_value}

    return json.dumps(filter_obj)


class TwentyCRMClient:
    """Client for Twenty CRM API."""

    def __init__(self):
        self.api_url = settings.twenty_api_url
        self.api_key = settings.twenty_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make an HTTP request to Twenty CRM API."""
        url = f"{self.api_url}/rest/{endpoint}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data,
                params=params,
            )
            response.raise_for_status()
            return response.json()


_client = TwentyCRMClient()


async def buscar_lead(telefone: str) -> dict | None:
    """
    Search for a lead by phone number.

    Args:
        telefone: Phone number to search

    Returns:
        Lead data if found, None otherwise
    """
    try:
        # Sanitize phone number before using in filter
        safe_phone = _sanitize_phone(telefone)
        if not safe_phone:
            logger.warning("Invalid phone number provided")
            return None

        # Use safe JSON building instead of string interpolation
        params = {
            "filter": _build_filter_json({"phone": safe_phone}),
            "limit": 1,
        }

        result = await _client._request("GET", "people", params=params)
        people = result.get("data", {}).get("people", [])

        if people:
            logger.info("Lead found", phone_masked=safe_phone[:4] + "****")
            return people[0]

        logger.info("Lead not found", phone_masked=safe_phone[:4] + "****")
        return None

    except Exception as e:
        logger.error("Failed to search lead", error=type(e).__name__)
        return None


async def criar_lead(dados: dict[str, Any]) -> dict | None:
    """
    Create a new lead in CRM.

    Args:
        dados: Lead data (name, phone, email, etc.)

    Returns:
        Created lead data if successful, None otherwise
    """
    try:
        payload = {
            "name": {
                "firstName": dados.get("nome", "").split()[0] if dados.get("nome") else "",
                "lastName": " ".join(dados.get("nome", "").split()[1:]) if dados.get("nome") else "",
            },
            "phones": {
                "primaryPhoneNumber": dados.get("telefone"),
            },
            "emails": {
                "primaryEmail": dados.get("email"),
            },
        }

        # Add custom fields if present
        if dados.get("origem"):
            payload["origem"] = dados["origem"]
        if dados.get("cliente_id"):
            payload["cliente_id"] = dados["cliente_id"]

        result = await _client._request("POST", "people", json_data=payload)

        logger.info("Lead created", lead_id=result.get("data", {}).get("id"))
        return result.get("data")

    except Exception as e:
        logger.error("Failed to create lead", error=str(e))
        return None


async def atualizar_lead(lead_id: str, dados: dict[str, Any]) -> dict | None:
    """
    Update an existing lead.

    Args:
        lead_id: Lead ID to update
        dados: Fields to update

    Returns:
        Updated lead data if successful, None otherwise
    """
    try:
        result = await _client._request("PATCH", f"people/{lead_id}", json_data=dados)

        logger.info("Lead updated", lead_id=lead_id)
        return result.get("data")

    except Exception as e:
        logger.error("Failed to update lead", lead_id=lead_id, error=str(e))
        return None


async def mover_pipeline(lead_id: str, etapa: str) -> bool:
    """
    Move a lead to a different pipeline stage.

    Args:
        lead_id: Lead ID
        etapa: New pipeline stage

    Returns:
        True if successful, False otherwise
    """
    try:
        # In Twenty CRM, pipeline stages are managed via opportunities
        # This maps the lead to an opportunity with the new stage
        payload = {
            "stage": etapa,
        }

        await _client._request("PATCH", f"people/{lead_id}", json_data=payload)

        logger.info("Pipeline moved", lead_id=lead_id, etapa=etapa)
        return True

    except Exception as e:
        logger.error("Failed to move pipeline", lead_id=lead_id, error=str(e))
        return False


async def listar_leads(
    filtros: dict[str, Any] | None = None,
    limite: int = 50,
    offset: int = 0,
) -> list[dict]:
    """
    List leads with optional filters.

    Args:
        filtros: Optional filters (etapa_pipeline, cliente_id, etc.)
        limite: Maximum number of results
        offset: Pagination offset

    Returns:
        List of leads
    """
    try:
        params = {
            "limit": limite,
            "offset": offset,
        }

        if filtros:
            params["filter"] = _build_filter_json(filtros)

        result = await _client._request("GET", "people", params=params)
        leads = result.get("data", {}).get("people", [])

        logger.info("Leads listed", count=len(leads))
        return leads

    except Exception as e:
        logger.error("Failed to list leads", error=str(e))
        return []
