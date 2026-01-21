"""
Chatwoot API Client.

Handles messaging integration:
- Accounts (multi-tenant)
- Inboxes (channels like WhatsApp, Instagram)
- Conversations
- Messages
- Contacts

Docs: https://www.chatwoot.com/docs/product/others/api
"""

import logging
from typing import Any

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatwootAPIError(Exception):
    """Chatwoot API error."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class ChatwootClient:
    """
    HTTP client for Chatwoot Platform API.

    Usage:
        client = ChatwootClient(api_key="...", account_id=1)
        conversations = await client.list_conversations()
    """

    def __init__(
        self,
        api_key: str | None = None,
        account_id: int | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or settings.chatwoot_api_key
        self.account_id = account_id
        self.base_url = (base_url or settings.chatwoot_api_url).rstrip("/")
        self._client: httpx.AsyncClient | None = None

    def _api_url(self, path: str) -> str:
        """Build API URL with account ID."""
        if path.startswith("/platform"):
            return f"{self.base_url}{path}"
        if self.account_id:
            return f"{self.base_url}/api/v1/accounts/{self.account_id}{path}"
        return f"{self.base_url}/api/v1{path}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["api_access_token"] = self.api_key

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict | list:
        """Make HTTP request to Chatwoot API."""
        client = await self._get_client()
        url = self._api_url(path)

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            return response.json()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            try:
                error_json = e.response.json()
                error_body = error_json.get("message", error_body)
            except Exception:
                pass
            raise ChatwootAPIError(
                f"HTTP {e.response.status_code}: {error_body}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise ChatwootAPIError(f"Request failed: {str(e)}")

    # =========================================================================
    # ACCOUNTS (Platform API)
    # =========================================================================

    async def create_account(
        self,
        name: str,
        locale: str = "pt_BR",
    ) -> dict:
        """Create a new account (platform API)."""
        payload = {"name": name, "locale": locale}
        result = await self._request("POST", "/platform/api/v1/accounts", json_data=payload)
        return result if isinstance(result, dict) else {}

    async def get_account(self, account_id: int | None = None) -> dict:
        """Get account details."""
        aid = account_id or self.account_id
        result = await self._request("GET", f"/platform/api/v1/accounts/{aid}")
        return result if isinstance(result, dict) else {}

    # =========================================================================
    # INBOXES
    # =========================================================================

    async def list_inboxes(self) -> list[dict]:
        """List all inboxes in the account."""
        result = await self._request("GET", "/inboxes")
        if isinstance(result, dict):
            return result.get("payload", [])
        return result

    async def get_inbox(self, inbox_id: int) -> dict:
        """Get inbox by ID."""
        result = await self._request("GET", f"/inboxes/{inbox_id}")
        return result if isinstance(result, dict) else {}

    async def create_inbox(
        self,
        name: str,
        channel_type: str = "web_widget",
        website_url: str | None = None,
        **extra_fields,
    ) -> dict:
        """
        Create a new inbox.

        Channel types: web_widget, api, email, telegram, whatsapp, etc.
        """
        payload = {
            "name": name,
            "channel": {
                "type": f"Channel::{channel_type.title().replace('_', '')}",
                **extra_fields,
            },
        }
        if website_url:
            payload["channel"]["website_url"] = website_url

        result = await self._request("POST", "/inboxes", json_data=payload)
        return result if isinstance(result, dict) else {}

    # =========================================================================
    # CONVERSATIONS
    # =========================================================================

    async def list_conversations(
        self,
        inbox_id: int | None = None,
        status: str = "open",
        page: int = 1,
    ) -> dict:
        """
        List conversations.

        Status: open, resolved, pending, snoozed, all
        """
        params: dict[str, Any] = {"status": status, "page": page}
        if inbox_id:
            params["inbox_id"] = inbox_id

        result = await self._request("GET", "/conversations", params=params)
        return result if isinstance(result, dict) else {}

    async def get_conversation(self, conversation_id: int) -> dict:
        """Get conversation by ID."""
        result = await self._request("GET", f"/conversations/{conversation_id}")
        return result if isinstance(result, dict) else {}

    async def create_conversation(
        self,
        inbox_id: int,
        contact_id: int,
        source_id: str | None = None,
        custom_attributes: dict | None = None,
    ) -> dict:
        """Create a new conversation."""
        payload: dict[str, Any] = {
            "inbox_id": inbox_id,
            "contact_id": contact_id,
        }
        if source_id:
            payload["source_id"] = source_id
        if custom_attributes:
            payload["custom_attributes"] = custom_attributes

        result = await self._request("POST", "/conversations", json_data=payload)
        return result if isinstance(result, dict) else {}

    async def update_conversation_status(
        self,
        conversation_id: int,
        status: str,
    ) -> dict:
        """Update conversation status (open, resolved, pending, snoozed)."""
        result = await self._request(
            "POST",
            f"/conversations/{conversation_id}/toggle_status",
            json_data={"status": status},
        )
        return result if isinstance(result, dict) else {}

    async def assign_conversation(
        self,
        conversation_id: int,
        assignee_id: int | None = None,
        team_id: int | None = None,
    ) -> dict:
        """Assign conversation to agent or team."""
        payload: dict[str, Any] = {}
        if assignee_id is not None:
            payload["assignee_id"] = assignee_id
        if team_id is not None:
            payload["team_id"] = team_id

        result = await self._request(
            "POST",
            f"/conversations/{conversation_id}/assignments",
            json_data=payload,
        )
        return result if isinstance(result, dict) else {}

    # =========================================================================
    # MESSAGES
    # =========================================================================

    async def list_messages(
        self,
        conversation_id: int,
        before: int | None = None,
    ) -> list[dict]:
        """List messages in a conversation."""
        params = {}
        if before:
            params["before"] = before

        result = await self._request(
            "GET",
            f"/conversations/{conversation_id}/messages",
            params=params,
        )
        if isinstance(result, dict):
            return result.get("payload", [])
        return result

    async def send_message(
        self,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
        private: bool = False,
        content_attributes: dict | None = None,
    ) -> dict:
        """
        Send a message in a conversation.

        Message types: outgoing, activity, incoming (for API channels)
        """
        payload: dict[str, Any] = {
            "content": content,
            "message_type": message_type,
            "private": private,
        }
        if content_attributes:
            payload["content_attributes"] = content_attributes

        result = await self._request(
            "POST",
            f"/conversations/{conversation_id}/messages",
            json_data=payload,
        )
        return result if isinstance(result, dict) else {}

    async def send_template_message(
        self,
        conversation_id: int,
        template_name: str,
        template_params: list[str],
    ) -> dict:
        """Send a WhatsApp template message."""
        payload = {
            "content_type": "template",
            "content_attributes": {
                "template_name": template_name,
                "template_params": template_params,
            },
        }
        result = await self._request(
            "POST",
            f"/conversations/{conversation_id}/messages",
            json_data=payload,
        )
        return result if isinstance(result, dict) else {}

    # =========================================================================
    # CONTACTS
    # =========================================================================

    async def list_contacts(
        self,
        page: int = 1,
        sort: str = "-last_activity_at",
    ) -> dict:
        """List contacts with pagination."""
        params = {"page": page, "sort": sort}
        result = await self._request("GET", "/contacts", params=params)
        return result if isinstance(result, dict) else {}

    async def get_contact(self, contact_id: int) -> dict:
        """Get contact by ID."""
        result = await self._request("GET", f"/contacts/{contact_id}")
        return result if isinstance(result, dict) else {}

    async def search_contacts(
        self,
        query: str,
        page: int = 1,
    ) -> dict:
        """Search contacts by name, email, or phone."""
        params = {"q": query, "page": page}
        result = await self._request("GET", "/contacts/search", params=params)
        return result if isinstance(result, dict) else {}

    async def create_contact(
        self,
        name: str,
        email: str | None = None,
        phone_number: str | None = None,
        inbox_id: int | None = None,
        custom_attributes: dict | None = None,
    ) -> dict:
        """Create a new contact."""
        payload: dict[str, Any] = {"name": name}
        if email:
            payload["email"] = email
        if phone_number:
            payload["phone_number"] = phone_number
        if inbox_id:
            payload["inbox_id"] = inbox_id
        if custom_attributes:
            payload["custom_attributes"] = custom_attributes

        result = await self._request("POST", "/contacts", json_data=payload)
        return result if isinstance(result, dict) else {}

    async def update_contact(
        self,
        contact_id: int,
        **fields,
    ) -> dict:
        """Update contact fields."""
        result = await self._request("PATCH", f"/contacts/{contact_id}", json_data=fields)
        return result if isinstance(result, dict) else {}

    # =========================================================================
    # AGENTS/USERS
    # =========================================================================

    async def list_agents(self) -> list[dict]:
        """List agents in the account."""
        result = await self._request("GET", "/agents")
        return result if isinstance(result, list) else []

    async def create_agent(
        self,
        name: str,
        email: str,
        role: str = "agent",
    ) -> dict:
        """Create a new agent."""
        payload = {"name": name, "email": email, "role": role}
        result = await self._request("POST", "/agents", json_data=payload)
        return result if isinstance(result, dict) else {}

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    async def list_webhooks(self) -> list[dict]:
        """List registered webhooks."""
        result = await self._request("GET", "/webhooks")
        if isinstance(result, dict):
            return result.get("payload", [])
        return result

    async def create_webhook(
        self,
        url: str,
        subscriptions: list[str],
    ) -> dict:
        """
        Register a webhook.

        Subscriptions:
        - message_created
        - message_updated
        - conversation_created
        - conversation_status_changed
        - conversation_updated
        - contact_created
        - contact_updated
        """
        payload = {
            "url": url,
            "subscriptions": subscriptions,
        }
        result = await self._request("POST", "/webhooks", json_data=payload)
        return result if isinstance(result, dict) else {}

    # =========================================================================
    # AUTOMATION (Agentic)
    # =========================================================================

    async def add_label(
        self,
        conversation_id: int,
        labels: list[str],
    ) -> dict:
        """Add labels to a conversation."""
        result = await self._request(
            "POST",
            f"/conversations/{conversation_id}/labels",
            json_data={"labels": labels},
        )
        return result if isinstance(result, dict) else {}

    async def get_reports(
        self,
        report_type: str = "account",
        since: str | None = None,
        until: str | None = None,
    ) -> dict:
        """Get account or agent reports."""
        params: dict[str, Any] = {"type": report_type}
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        result = await self._request("GET", "/reports", params=params)
        return result if isinstance(result, dict) else {}
