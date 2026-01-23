from app.schemas.scrape import TriggerScrapeRequest, TriggerScrapeResponse, ScrapeStatusResponse
from app.schemas.ads import (
    MetaAdSearchRequest,
    MetaAdSearchResponse,
    MetaAdByPageRequest,
    GoogleAdsSearchRequest,
    GoogleAdsSearchResponse,
    AdvertiserOut,
    AdCreativeOut,
    AdOut,
    AdsListResponse,
)
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ConversationOut,
    ConversationListResponse,
    BrandProfileOut,
    BrandProfileListResponse,
    ProvidersResponse,
)

__all__ = [
    "TriggerScrapeRequest",
    "TriggerScrapeResponse",
    "ScrapeStatusResponse",
    # Ads schemas
    "MetaAdSearchRequest",
    "MetaAdSearchResponse",
    "MetaAdByPageRequest",
    "GoogleAdsSearchRequest",
    "GoogleAdsSearchResponse",
    "AdvertiserOut",
    "AdCreativeOut",
    "AdOut",
    "AdsListResponse",
    # AI schemas
    "ChatRequest",
    "ChatResponse",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
    "ConversationOut",
    "ConversationListResponse",
    "BrandProfileOut",
    "BrandProfileListResponse",
    "ProvidersResponse",
]
