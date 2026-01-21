"""
Service clients for external platforms.

Provides real API integrations with:
- Twenty CRM
- Cal.com
- Chatwoot
- Cross-service sync orchestration
"""

from .twenty import TwentyClient, TwentyAPIError
from .calcom import CalcomClient, CalcomAPIError
from .chatwoot import ChatwootClient, ChatwootAPIError
from .sync_service import SyncService, SyncError, verify_webhook_signature

__all__ = [
    "TwentyClient",
    "TwentyAPIError",
    "CalcomClient",
    "CalcomAPIError",
    "ChatwootClient",
    "ChatwootAPIError",
    "SyncService",
    "SyncError",
    "verify_webhook_signature",
]
