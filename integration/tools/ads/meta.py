"""Meta Marketing API client for Facebook/Instagram Ads.

Provides campaign, ad set, ad, and audience management
for medical clinic marketing campaigns.
"""

from __future__ import annotations

from typing import Any

import httpx

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

META_GRAPH_API = "https://graph.facebook.com/v21.0"


class MetaAdsClient:
    """Client for Meta Marketing API operations."""

    def __init__(
        self,
        access_token: str | None = None,
        ad_account_id: str | None = None,
    ):
        self.access_token = access_token or settings.meta_access_token or ""
        self.ad_account_id = ad_account_id or ""
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=META_GRAPH_API,
                timeout=30.0,
                params={"access_token": self.access_token},
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated request to Meta Graph API."""
        client = await self._get_client()
        response = await client.request(
            method=method,
            url=endpoint,
            params=params,
            json=json_data,
        )
        if response.status_code >= 400:
            logger.error("meta_api_error", status=response.status_code, body=response.text[:500])
            response.raise_for_status()
        return response.json()

    async def criar_campanha(
        self,
        nome: str,
        objetivo: str,
        orcamento_diario_centavos: int,
        status: str = "PAUSED",
    ) -> dict[str, Any]:
        """Create a new campaign.

        Args:
            nome: Campaign name
            objetivo: Campaign objective (REACH, TRAFFIC, CONVERSIONS, LEAD_GENERATION, etc.)
            orcamento_diario_centavos: Daily budget in cents (BRL)
            status: Initial status (PAUSED or ACTIVE)

        Returns:
            Created campaign data with ID
        """
        payload = {
            "name": nome,
            "objective": objetivo,
            "status": status,
            "special_ad_categories": ["NONE"],
            "daily_budget": orcamento_diario_centavos,
        }

        result = await self._request(
            "POST",
            f"/act_{self.ad_account_id}/campaigns",
            json_data=payload,
        )
        logger.info("meta_campaign_created", campaign_id=result.get("id"), name=nome)
        return result

    async def criar_conjunto_anuncios(
        self,
        campaign_id: str,
        nome: str,
        targeting: dict[str, Any],
        orcamento_diario_centavos: int | None = None,
        optimization_goal: str = "LEAD_GENERATION",
        billing_event: str = "IMPRESSIONS",
        bid_amount_centavos: int | None = None,
    ) -> dict[str, Any]:
        """Create an ad set within a campaign.

        Args:
            campaign_id: Parent campaign ID
            nome: Ad set name
            targeting: Targeting specification (location, age, interests, etc.)
            orcamento_diario_centavos: Optional ad set level budget
            optimization_goal: Optimization goal
            billing_event: Billing event type
            bid_amount_centavos: Optional bid amount

        Returns:
            Created ad set data
        """
        payload: dict[str, Any] = {
            "name": nome,
            "campaign_id": campaign_id,
            "targeting": targeting,
            "optimization_goal": optimization_goal,
            "billing_event": billing_event,
            "status": "PAUSED",
        }
        if orcamento_diario_centavos:
            payload["daily_budget"] = orcamento_diario_centavos
        if bid_amount_centavos:
            payload["bid_amount"] = bid_amount_centavos

        return await self._request(
            "POST",
            f"/act_{self.ad_account_id}/adsets",
            json_data=payload,
        )

    async def criar_anuncio(
        self,
        adset_id: str,
        nome: str,
        creative_id: str,
        status: str = "PAUSED",
    ) -> dict[str, Any]:
        """Create an ad within an ad set.

        Args:
            adset_id: Parent ad set ID
            nome: Ad name
            creative_id: Creative ID to use
            status: Initial status

        Returns:
            Created ad data
        """
        payload = {
            "name": nome,
            "adset_id": adset_id,
            "creative": {"creative_id": creative_id},
            "status": status,
        }
        return await self._request(
            "POST",
            f"/act_{self.ad_account_id}/ads",
            json_data=payload,
        )

    async def criar_publico_lookalike(
        self,
        source_audience_id: str,
        pais: str = "BR",
        ratio: float = 0.01,
        nome: str | None = None,
    ) -> dict[str, Any]:
        """Create a lookalike audience.

        Args:
            source_audience_id: Source custom audience ID
            pais: Country code (default: Brazil)
            ratio: Lookalike ratio (0.01 = top 1%)
            nome: Audience name

        Returns:
            Created audience data
        """
        payload = {
            "name": nome or f"Lookalike {ratio*100:.0f}% - {pais}",
            "subtype": "LOOKALIKE",
            "origin_audience_id": source_audience_id,
            "lookalike_spec": {
                "country": pais,
                "ratio": ratio,
                "type": "similarity",
            },
        }
        return await self._request(
            "POST",
            f"/act_{self.ad_account_id}/customaudiences",
            json_data=payload,
        )

    async def obter_metricas_campanha(
        self,
        campaign_id: str,
        date_preset: str = "last_7d",
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get campaign performance metrics.

        Args:
            campaign_id: Campaign ID
            date_preset: Date range (today, yesterday, last_7d, last_30d, etc.)
            fields: Specific fields to retrieve

        Returns:
            Campaign insights/metrics
        """
        default_fields = [
            "impressions", "reach", "clicks", "spend",
            "cpc", "cpm", "ctr", "actions", "cost_per_action_type",
        ]
        params = {
            "date_preset": date_preset,
            "fields": ",".join(fields or default_fields),
        }
        return await self._request("GET", f"/{campaign_id}/insights", params=params)

    async def pausar_campanha(self, campaign_id: str) -> dict[str, Any]:
        """Pause a campaign."""
        return await self._request(
            "POST",
            f"/{campaign_id}",
            json_data={"status": "PAUSED"},
        )

    async def ativar_campanha(self, campaign_id: str) -> dict[str, Any]:
        """Activate a campaign."""
        return await self._request(
            "POST",
            f"/{campaign_id}",
            json_data={"status": "ACTIVE"},
        )

    async def listar_campanhas(
        self,
        status: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """List campaigns for the ad account.

        Args:
            status: Filter by status (ACTIVE, PAUSED, ARCHIVED)
            limit: Max results

        Returns:
            List of campaign data
        """
        params: dict[str, Any] = {
            "fields": "id,name,status,objective,daily_budget,created_time",
            "limit": limit,
        }
        if status:
            params["effective_status"] = f'["{status}"]'

        result = await self._request(
            "GET",
            f"/act_{self.ad_account_id}/campaigns",
            params=params,
        )
        return result.get("data", [])
