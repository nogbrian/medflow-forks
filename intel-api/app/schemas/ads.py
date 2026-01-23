"""Pydantic schemas for Meta Ad Library and Google Ads Transparency."""

from typing import Literal, Optional
from pydantic import BaseModel, field_validator
import uuid


# ============================================================
# Meta Ad Library Schemas
# ============================================================

class MetaAdSearchRequest(BaseModel):
    """Request to search Meta Ad Library."""
    search_terms: Optional[str] = None
    ad_reached_countries: list[str] = ["BR"]  # ISO country codes
    ad_active_status: Literal["ALL", "ACTIVE", "INACTIVE"] = "ALL"
    ad_type: Literal["ALL", "POLITICAL_AND_ISSUE_ADS", "HOUSING_ADS", "CREDIT_ADS", "EMPLOYMENT_ADS"] = "ALL"
    publisher_platforms: list[str] = ["facebook", "instagram"]
    search_page_ids: Optional[list[str]] = None  # Facebook page IDs
    limit: int = 50
    workspace_id: str

    @field_validator("workspace_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid UUID format")
        return v


class MetaAdSearchResponse(BaseModel):
    """Response from Meta Ad Library search."""
    success: bool
    ads_found: int = 0
    ads_saved: int = 0
    advertisers_found: int = 0
    error: Optional[str] = None


class MetaAdByPageRequest(BaseModel):
    """Request to get ads by advertiser/page."""
    page_id: str  # Facebook page ID
    workspace_id: str
    ad_active_status: Literal["ALL", "ACTIVE", "INACTIVE"] = "ALL"
    limit: int = 100

    @field_validator("workspace_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid UUID format")
        return v


# ============================================================
# Google Ads Transparency Schemas
# ============================================================

class GoogleAdsSearchRequest(BaseModel):
    """Request to search Google Ads Transparency Center."""
    advertiser_name: Optional[str] = None
    advertiser_id: Optional[str] = None  # Google advertiser ID
    domain: Optional[str] = None  # Website domain
    region: str = "BR"  # ISO country code
    date_range: Literal["LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", "ALL_TIME"] = "LAST_30_DAYS"
    ad_format: Optional[Literal["TEXT", "IMAGE", "VIDEO"]] = None
    limit: int = 50
    workspace_id: str

    @field_validator("workspace_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid UUID format")
        return v

    def model_post_init(self, __context):
        if not self.advertiser_name and not self.advertiser_id and not self.domain:
            raise ValueError("At least one of advertiser_name, advertiser_id, or domain is required")


class GoogleAdsSearchResponse(BaseModel):
    """Response from Google Ads Transparency search."""
    success: bool
    ads_found: int = 0
    ads_saved: int = 0
    advertisers_found: int = 0
    error: Optional[str] = None


# ============================================================
# Ad Response Schemas (for API responses)
# ============================================================

class AdvertiserOut(BaseModel):
    """Advertiser output schema."""
    id: str
    platform: str
    platform_id: Optional[str] = None
    name: str
    page_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    disclaimer: Optional[str] = None
    country: Optional[str] = None

    class Config:
        from_attributes = True


class AdCreativeOut(BaseModel):
    """Ad creative output schema."""
    id: str
    creative_type: str
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    position: int = 0

    class Config:
        from_attributes = True


class AdOut(BaseModel):
    """Ad output schema."""
    id: str
    platform: str
    platform_ad_id: Optional[str] = None
    title: Optional[str] = None
    body_text: Optional[str] = None
    link_url: Optional[str] = None
    link_title: Optional[str] = None
    link_description: Optional[str] = None
    call_to_action: Optional[str] = None
    ad_type: Optional[str] = None
    status: Optional[str] = None
    impressions_lower: Optional[int] = None
    impressions_upper: Optional[int] = None
    spend_lower: Optional[int] = None
    spend_upper: Optional[int] = None
    currency: Optional[str] = None
    reached_countries: Optional[list[str]] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    advertiser: Optional[AdvertiserOut] = None
    creatives: list[AdCreativeOut] = []

    class Config:
        from_attributes = True


class AdsListResponse(BaseModel):
    """Response for listing ads."""
    success: bool
    ads: list[AdOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 50
    error: Optional[str] = None
