"""Google Ads API client for search and display campaigns.

Provides campaign, ad group, keyword, and bidding management
for medical clinic marketing campaigns.
"""

from __future__ import annotations

from typing import Any

import httpx

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Google Ads API endpoint
GOOGLE_ADS_API = "https://googleads.googleapis.com/v18"


class GoogleAdsClient:
    """Client for Google Ads API operations.

    Uses REST API directly via httpx for simplicity.
    For production, consider using the official google-ads Python client.
    """

    def __init__(
        self,
        developer_token: str | None = None,
        customer_id: str | None = None,
        refresh_token: str | None = None,
    ):
        self.developer_token = developer_token or ""
        self.customer_id = customer_id or ""
        self.refresh_token = refresh_token or ""
        self._access_token: str = ""
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=GOOGLE_ADS_API,
                timeout=30.0,
                headers={
                    "developer-token": self.developer_token,
                    "Authorization": f"Bearer {self._access_token}",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _query(self, query: str) -> list[dict[str, Any]]:
        """Execute a Google Ads Query Language (GAQL) query.

        Args:
            query: GAQL query string

        Returns:
            List of result rows
        """
        client = await self._get_client()
        response = await client.post(
            f"/customers/{self.customer_id}/googleAds:searchStream",
            json={"query": query},
        )
        if response.status_code >= 400:
            logger.error("google_ads_query_error", status=response.status_code, body=response.text[:500])
            response.raise_for_status()

        results = response.json()
        rows = []
        for batch in results:
            rows.extend(batch.get("results", []))
        return rows

    async def _mutate(
        self,
        resource_type: str,
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Execute a mutate operation.

        Args:
            resource_type: Resource type (campaigns, adGroups, ads, etc.)
            operations: List of create/update/remove operations

        Returns:
            Mutate results
        """
        client = await self._get_client()
        response = await client.post(
            f"/customers/{self.customer_id}/{resource_type}:mutate",
            json={"operations": operations},
        )
        if response.status_code >= 400:
            logger.error("google_ads_mutate_error", status=response.status_code, body=response.text[:500])
            response.raise_for_status()

        return response.json().get("results", [])

    async def criar_campanha(
        self,
        nome: str,
        tipo: str = "SEARCH",
        orcamento_diario_micros: int = 50_000_000,
        estrategia_lance: str = "MAXIMIZE_CONVERSIONS",
        status: str = "PAUSED",
    ) -> dict[str, Any]:
        """Create a new campaign.

        Args:
            nome: Campaign name
            tipo: Campaign type (SEARCH, DISPLAY, VIDEO, SHOPPING)
            orcamento_diario_micros: Daily budget in micros (1 BRL = 1,000,000 micros)
            estrategia_lance: Bidding strategy
            status: Initial status (PAUSED or ENABLED)

        Returns:
            Created campaign resource info
        """
        # First create budget
        budget_op = {
            "create": {
                "name": f"Budget - {nome}",
                "amount_micros": orcamento_diario_micros,
                "delivery_method": "STANDARD",
            }
        }
        budget_results = await self._mutate("campaignBudgets", [budget_op])
        budget_resource = budget_results[0].get("resourceName", "")

        # Then create campaign
        campaign_op = {
            "create": {
                "name": nome,
                "advertising_channel_type": tipo,
                "status": status,
                "campaign_budget": budget_resource,
                "bidding_strategy_type": estrategia_lance,
            }
        }
        results = await self._mutate("campaigns", [campaign_op])
        logger.info("google_campaign_created", name=nome, type=tipo)
        return results[0] if results else {}

    async def criar_grupo_anuncios(
        self,
        campaign_resource: str,
        nome: str,
        cpc_max_micros: int | None = None,
    ) -> dict[str, Any]:
        """Create an ad group within a campaign.

        Args:
            campaign_resource: Parent campaign resource name
            nome: Ad group name
            cpc_max_micros: Max CPC bid in micros

        Returns:
            Created ad group resource info
        """
        ad_group: dict[str, Any] = {
            "name": nome,
            "campaign": campaign_resource,
            "type": "SEARCH_STANDARD",
            "status": "ENABLED",
        }
        if cpc_max_micros:
            ad_group["cpc_bid_micros"] = cpc_max_micros

        results = await self._mutate("adGroups", [{"create": ad_group}])
        return results[0] if results else {}

    async def adicionar_keywords(
        self,
        ad_group_resource: str,
        keywords: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Add keywords to an ad group.

        Args:
            ad_group_resource: Parent ad group resource name
            keywords: List of {"text": "...", "match_type": "BROAD|PHRASE|EXACT"}

        Returns:
            Created keyword criteria
        """
        operations = []
        for kw in keywords:
            operations.append({
                "create": {
                    "ad_group": ad_group_resource,
                    "keyword": {
                        "text": kw["text"],
                        "match_type": kw.get("match_type", "BROAD"),
                    },
                    "status": "ENABLED",
                }
            })
        return await self._mutate("adGroupCriteria", operations)

    async def criar_anuncio_responsivo(
        self,
        ad_group_resource: str,
        titulos: list[str],
        descricoes: list[str],
        url_final: str,
        path1: str = "",
        path2: str = "",
    ) -> dict[str, Any]:
        """Create a responsive search ad.

        Args:
            ad_group_resource: Parent ad group resource
            titulos: List of headlines (3-15, max 30 chars each)
            descricoes: List of descriptions (2-4, max 90 chars each)
            url_final: Final URL
            path1: Display URL path 1
            path2: Display URL path 2

        Returns:
            Created ad resource info
        """
        headlines = [{"text": t} for t in titulos[:15]]
        descriptions = [{"text": d} for d in descricoes[:4]]

        ad_op = {
            "create": {
                "ad_group": ad_group_resource,
                "ad": {
                    "responsive_search_ad": {
                        "headlines": headlines,
                        "descriptions": descriptions,
                        "path1": path1,
                        "path2": path2,
                    },
                    "final_urls": [url_final],
                },
                "status": "ENABLED",
            }
        }
        results = await self._mutate("adGroupAds", [ad_op])
        return results[0] if results else {}

    async def obter_metricas(
        self,
        campaign_id: str | None = None,
        periodo_dias: int = 7,
    ) -> list[dict[str, Any]]:
        """Get campaign performance metrics.

        Args:
            campaign_id: Specific campaign ID (None = all campaigns)
            periodo_dias: Number of days to look back

        Returns:
            List of metric rows
        """
        where_clause = ""
        if campaign_id:
            where_clause = f"AND campaign.id = {campaign_id}"

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.average_cpm
            FROM campaign
            WHERE segments.date DURING LAST_{periodo_dias}_DAYS
            {where_clause}
            ORDER BY metrics.cost_micros DESC
        """
        return await self._query(query)

    async def pausar_campanha(self, campaign_resource: str) -> dict[str, Any]:
        """Pause a campaign."""
        results = await self._mutate("campaigns", [{
            "update": {
                "resource_name": campaign_resource,
                "status": "PAUSED",
            },
            "update_mask": "status",
        }])
        return results[0] if results else {}

    async def listar_campanhas(self, status: str | None = None) -> list[dict[str, Any]]:
        """List all campaigns.

        Args:
            status: Filter by status (ENABLED, PAUSED, REMOVED)

        Returns:
            List of campaign data
        """
        where = f"WHERE campaign.status = '{status}'" if status else ""
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros
            FROM campaign
            {where}
            ORDER BY campaign.name
        """
        return await self._query(query)
