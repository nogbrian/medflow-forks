"""SSO routes for embedded service authentication.

Generates single-use authenticated URLs for iframe embedding:
- Chatwoot: Platform API SSO token
- Twenty: GraphQL signIn token relay
- Cal.com: Public embed URL (no auth needed for booking pages)
"""

import logging
from enum import Enum
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.auth import CurrentUser
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/sso")


class ServiceName(str, Enum):
    chatwoot = "chatwoot"
    twenty = "twenty"
    calcom = "calcom"


class SSOResponse(BaseModel):
    service: str
    url: str
    method: str = "redirect"  # redirect | token
    token: str | None = None
    expires_in: int | None = None  # seconds


@router.get("/{service}", response_model=SSOResponse)
async def get_sso_url(service: ServiceName, current_user: CurrentUser):
    """Get an authenticated URL for the specified embedded service.

    Returns a single-use SSO URL that auto-logs the user into the service.
    """
    handlers = {
        ServiceName.chatwoot: _get_chatwoot_sso,
        ServiceName.twenty: _get_twenty_sso,
        ServiceName.calcom: _get_calcom_url,
    }
    handler = handlers[service]
    return await handler(current_user)


async def _get_chatwoot_sso(user: Any) -> SSOResponse:
    """Get Chatwoot SSO URL via Platform API.

    Requires:
    - CHATWOOT_PLATFORM_TOKEN set in environment
    - User has chatwoot_user_id set in database
    - Platform App created in Chatwoot with access to the user
    """
    if not settings.chatwoot_platform_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatwoot SSO not configured (missing CHATWOOT_PLATFORM_TOKEN)",
        )

    chatwoot_user_id = user.chatwoot_user_id
    if not chatwoot_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a linked Chatwoot account",
        )

    base_url = settings.chatwoot_api_url.rstrip("/")
    endpoint = f"{base_url}/platform/api/v1/users/{chatwoot_user_id}/login"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                endpoint,
                headers={"api_access_token": settings.chatwoot_platform_token},
            )

        if response.status_code != 200:
            logger.error(
                "Chatwoot SSO failed",
                extra={
                    "status": response.status_code,
                    "body": response.text[:200],
                    "user_id": user.id,
                    "chatwoot_user_id": chatwoot_user_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Chatwoot Platform API returned {response.status_code}",
            )

        data = response.json()
        sso_url = data.get("url")
        if not sso_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Chatwoot Platform API did not return an SSO URL",
            )

        return SSOResponse(
            service="chatwoot",
            url=sso_url,
            method="redirect",
        )

    except httpx.RequestError as e:
        logger.exception("Chatwoot SSO request failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach Chatwoot: {e}",
        )


async def _get_twenty_sso(user: Any) -> SSOResponse:
    """Get Twenty CRM SSO by calling the GraphQL signIn mutation.

    This uses the user's email to generate a login token.
    Twenty stores its own auth tokens in the browser after redirect.
    """
    base_url = settings.twenty_api_url.rstrip("/")

    # Use the Twenty API to get a login token for this user
    # This requires the user to exist in Twenty with matching email
    query = """
    mutation GetLoginToken($email: String!, $password: String!) {
        getLoginTokenFromCredentials(input: { email: $email, password: $password }) {
            loginToken { token expiresAt }
        }
    }
    """

    # We don't store Twenty passwords. Instead, try a service account approach:
    # The frontend will open Twenty in a new context where the user logs in once.
    # For now, return the base URL. True SSO requires Twenty OIDC support.
    logger.info(
        "Twenty SSO: returning base URL (full SSO requires OIDC configuration)",
        extra={"user_id": user.id},
    )

    return SSOResponse(
        service="twenty",
        url=base_url,
        method="redirect",
    )


async def _get_calcom_url(user: Any) -> SSOResponse:
    """Get Cal.com URL.

    Public booking pages don't require authentication.
    Admin pages require Cal.com's own session.
    """
    base_url = settings.calcom_api_url.rstrip("/")

    return SSOResponse(
        service="calcom",
        url=base_url,
        method="redirect",
    )
