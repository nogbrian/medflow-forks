"""Webhook signature verification utilities.

Supports HMAC-SHA256 signatures used by Chatwoot, Cal.com, Twenty, and Evolution API.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)


def verify_hmac_sha256(
    payload: bytes,
    signature: str,
    secret: str,
    timestamp: str | None = None,
) -> bool:
    """Verify HMAC-SHA256 webhook signature.

    Supports multiple signature formats:
    - Raw hex: 'abc123...'
    - Prefixed: 'sha256=abc123...'
    - With timestamp: HMAC(timestamp:payload, secret)

    Args:
        payload: Raw request body bytes
        signature: Signature from webhook header
        secret: Webhook secret key
        timestamp: Optional timestamp for time-based signatures

    Returns:
        True if signature is valid
    """
    if not signature or not secret:
        return False

    # Strip common prefixes
    clean_sig = signature
    for prefix in ("sha256=", "sha256:", "hmac-sha256="):
        if clean_sig.lower().startswith(prefix):
            clean_sig = clean_sig[len(prefix):]
            break

    # Build the message to sign
    if timestamp:
        message = f"{timestamp}:{payload.decode('utf-8', errors='replace')}".encode()
    else:
        message = payload

    # Compute expected signature
    expected = hmac.HMAC(
        key=secret.encode(),
        msg=message,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected.lower(), clean_sig.lower())


def verify_evolution_signature(
    payload: bytes,
    signature: str | None,
    api_key: str | None,
) -> bool:
    """Verify Evolution API webhook authenticity.

    Evolution API uses API key-based verification rather than HMAC signatures.
    The webhook includes the instance API key in headers.

    Args:
        payload: Raw request body
        signature: Value from x-api-key or Authorization header
        api_key: Expected API key

    Returns:
        True if authenticated
    """
    if not api_key:
        return True  # No key configured, accept all

    if not signature:
        return False

    # Strip "Bearer " prefix if present
    clean = signature.strip()
    if clean.lower().startswith("bearer "):
        clean = clean[7:]

    return hmac.compare_digest(clean, api_key)
