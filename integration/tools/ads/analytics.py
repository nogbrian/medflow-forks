"""Unified ads analytics across Meta and Google platforms.

Provides normalized metrics (CPA, ROAS, CTR, CPM) and
comparative reporting for medical clinic campaigns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CampaignMetrics:
    """Normalized campaign metrics across platforms."""

    campaign_id: str
    campaign_name: str
    platform: str  # "meta" or "google"
    status: str

    # Core metrics
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    conversions: float = 0.0
    spend_brl: float = 0.0

    # Calculated metrics
    ctr: float = 0.0  # Click-through rate (%)
    cpc_brl: float = 0.0  # Cost per click
    cpm_brl: float = 0.0  # Cost per 1000 impressions
    cpa_brl: float = 0.0  # Cost per acquisition/conversion
    roas: float = 0.0  # Return on ad spend
    conversion_value_brl: float = 0.0

    def calculate_derived(self) -> None:
        """Calculate derived metrics from base values."""
        if self.impressions > 0:
            self.ctr = (self.clicks / self.impressions) * 100
            self.cpm_brl = (self.spend_brl / self.impressions) * 1000
        if self.clicks > 0:
            self.cpc_brl = self.spend_brl / self.clicks
        if self.conversions > 0:
            self.cpa_brl = self.spend_brl / self.conversions
        if self.spend_brl > 0 and self.conversion_value_brl > 0:
            self.roas = self.conversion_value_brl / self.spend_brl

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "platform": self.platform,
            "status": self.status,
            "impressions": self.impressions,
            "reach": self.reach,
            "clicks": self.clicks,
            "conversions": round(self.conversions, 2),
            "spend_brl": round(self.spend_brl, 2),
            "ctr": round(self.ctr, 2),
            "cpc_brl": round(self.cpc_brl, 2),
            "cpm_brl": round(self.cpm_brl, 2),
            "cpa_brl": round(self.cpa_brl, 2),
            "roas": round(self.roas, 2),
        }


class AdsAnalytics:
    """Unified analytics across Meta and Google Ads platforms."""

    def __init__(
        self,
        meta_client: Any | None = None,
        google_client: Any | None = None,
    ):
        self.meta = meta_client
        self.google = google_client

    async def obter_metricas_unificadas(
        self,
        periodo_dias: int = 7,
        platform: str | None = None,
    ) -> list[CampaignMetrics]:
        """Get unified metrics across all platforms.

        Args:
            periodo_dias: Number of days to analyze
            platform: Filter by platform ("meta", "google", or None for all)

        Returns:
            List of normalized campaign metrics
        """
        results: list[CampaignMetrics] = []

        if (platform is None or platform == "meta") and self.meta:
            meta_metrics = await self._get_meta_metrics(periodo_dias)
            results.extend(meta_metrics)

        if (platform is None or platform == "google") and self.google:
            google_metrics = await self._get_google_metrics(periodo_dias)
            results.extend(google_metrics)

        return results

    async def relatorio_periodo(
        self,
        periodo_dias: int = 30,
    ) -> dict[str, Any]:
        """Generate a comprehensive period report.

        Args:
            periodo_dias: Report period in days

        Returns:
            Formatted report with totals, per-platform breakdown, and recommendations
        """
        metrics = await self.obter_metricas_unificadas(periodo_dias)

        # Aggregate totals
        total_spend = sum(m.spend_brl for m in metrics)
        total_impressions = sum(m.impressions for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)

        # Per-platform breakdown
        meta_metrics = [m for m in metrics if m.platform == "meta"]
        google_metrics = [m for m in metrics if m.platform == "google"]

        # Funnel analysis (TOF/MOF/BOF)
        tof_keywords = ["awareness", "reach", "brand", "alcance"]
        mof_keywords = ["consideration", "traffic", "engagement", "trafego"]
        bof_keywords = ["conversion", "lead", "purchase", "conversao"]

        tof_spend = sum(
            m.spend_brl for m in metrics
            if any(kw in m.campaign_name.lower() for kw in tof_keywords)
        )
        mof_spend = sum(
            m.spend_brl for m in metrics
            if any(kw in m.campaign_name.lower() for kw in mof_keywords)
        )
        bof_spend = sum(
            m.spend_brl for m in metrics
            if any(kw in m.campaign_name.lower() for kw in bof_keywords)
        )
        other_spend = total_spend - tof_spend - mof_spend - bof_spend

        report = {
            "periodo_dias": periodo_dias,
            "total": {
                "spend_brl": round(total_spend, 2),
                "impressions": total_impressions,
                "clicks": total_clicks,
                "conversions": round(total_conversions, 2),
                "ctr": round((total_clicks / total_impressions * 100) if total_impressions else 0, 2),
                "cpa_brl": round((total_spend / total_conversions) if total_conversions else 0, 2),
                "campaigns_active": len([m for m in metrics if m.status in ("ACTIVE", "ENABLED")]),
            },
            "por_plataforma": {
                "meta": {
                    "campaigns": len(meta_metrics),
                    "spend_brl": round(sum(m.spend_brl for m in meta_metrics), 2),
                    "conversions": round(sum(m.conversions for m in meta_metrics), 2),
                },
                "google": {
                    "campaigns": len(google_metrics),
                    "spend_brl": round(sum(m.spend_brl for m in google_metrics), 2),
                    "conversions": round(sum(m.conversions for m in google_metrics), 2),
                },
            },
            "funil": {
                "tof_spend_brl": round(tof_spend, 2),
                "mof_spend_brl": round(mof_spend, 2),
                "bof_spend_brl": round(bof_spend, 2),
                "other_spend_brl": round(other_spend, 2),
            },
            "top_campaigns": [
                m.to_dict() for m in sorted(metrics, key=lambda x: x.conversions, reverse=True)[:5]
            ],
        }

        return report

    async def _get_meta_metrics(self, periodo_dias: int) -> list[CampaignMetrics]:
        """Fetch and normalize Meta Ads metrics."""
        try:
            campaigns = await self.meta.listar_campanhas()
            metrics = []

            for campaign in campaigns:
                campaign_id = campaign.get("id", "")
                insights = await self.meta.obter_metricas_campanha(
                    campaign_id,
                    date_preset=f"last_{periodo_dias}d" if periodo_dias <= 30 else "last_30d",
                )

                data = insights.get("data", [{}])
                row = data[0] if data else {}

                cm = CampaignMetrics(
                    campaign_id=campaign_id,
                    campaign_name=campaign.get("name", ""),
                    platform="meta",
                    status=campaign.get("status", ""),
                    impressions=int(row.get("impressions", 0)),
                    reach=int(row.get("reach", 0)),
                    clicks=int(row.get("clicks", 0)),
                    spend_brl=float(row.get("spend", 0)),
                )

                # Extract conversions from actions
                actions = row.get("actions", [])
                for action in actions:
                    if action.get("action_type") in ("lead", "complete_registration", "purchase"):
                        cm.conversions += float(action.get("value", 0))

                cm.calculate_derived()
                metrics.append(cm)

            return metrics
        except Exception as e:
            logger.error("meta_metrics_failed", error=str(e))
            return []

    async def _get_google_metrics(self, periodo_dias: int) -> list[CampaignMetrics]:
        """Fetch and normalize Google Ads metrics."""
        try:
            rows = await self.google.obter_metricas(periodo_dias=periodo_dias)
            metrics = []

            for row in rows:
                campaign = row.get("campaign", {})
                row_metrics = row.get("metrics", {})

                cm = CampaignMetrics(
                    campaign_id=str(campaign.get("id", "")),
                    campaign_name=campaign.get("name", ""),
                    platform="google",
                    status=campaign.get("status", ""),
                    impressions=int(row_metrics.get("impressions", 0)),
                    clicks=int(row_metrics.get("clicks", 0)),
                    conversions=float(row_metrics.get("conversions", 0)),
                    spend_brl=int(row_metrics.get("cost_micros", 0)) / 1_000_000,
                    conversion_value_brl=float(row_metrics.get("conversions_value", 0)),
                )
                cm.calculate_derived()
                metrics.append(cm)

            return metrics
        except Exception as e:
            logger.error("google_metrics_failed", error=str(e))
            return []
