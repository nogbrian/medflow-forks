from typing import Literal, Optional
from pydantic import BaseModel, field_validator
import uuid


class TriggerScrapeRequest(BaseModel):
    action: Literal["full", "posts_only", "reels_only", "profile_only"]
    profile_id: Optional[str] = None
    username: Optional[str] = None
    workspace_id: Optional[str] = None
    save_profile: bool = True
    session_cookie: Optional[str] = None

    @field_validator("profile_id", "workspace_id")
    @classmethod
    def validate_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Invalid UUID format")
        return v

    def model_post_init(self, __context):
        if not self.profile_id and not self.username:
            raise ValueError("Either profile_id or username is required")
        if self.username and not self.workspace_id:
            raise ValueError("workspace_id is required when using username")


class TriggerScrapeResponse(BaseModel):
    success: bool
    scrape_run_id: Optional[str] = None
    profile_id: Optional[str] = None
    action: Optional[str] = None
    error: Optional[str] = None


class ScrapeStatusResponse(BaseModel):
    scrape_run_id: str
    status: str
    scrape_type: Optional[str] = None
    posts_scraped: int = 0
    reels_scraped: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
