"""Chatwoot integration for handoff and monitoring."""

from functools import lru_cache
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ChatwootService:
    """Chatwoot API client for human handoff and monitoring."""

    def __init__(self):
        self.base_url = settings.chatwoot_api_url
        self.api_key = settings.chatwoot_api_key
        self.account_id = settings.chatwoot_account_id
        self.inbox_id = settings.chatwoot_inbox_id
        self.human_team_id = settings.chatwoot_human_team_id

    def _get_headers(self) -> dict:
        """Get authentication headers."""
        return {
            "api_access_token": self.api_key,
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make authenticated request to Chatwoot API."""
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=json_data,
                params=params,
            )

            if response.status_code >= 400:
                logger.error(
                    "Chatwoot API error",
                    status=response.status_code,
                    response=response.text,
                )
                response.raise_for_status()

            return response.json() if response.text else {}

    async def buscar_ou_criar_contato(
        self,
        phone: str,
        name: str | None = None,
        email: str | None = None,
        custom_attributes: dict | None = None,
    ) -> dict | None:
        """
        Find or create a contact by phone number.

        Args:
            phone: Contact phone number
            name: Contact name
            email: Contact email
            custom_attributes: Custom attributes for the contact

        Returns:
            Contact data if successful, None otherwise
        """
        try:
            # First, try to find existing contact
            search_result = await self._request(
                method="GET",
                endpoint="/contacts/search",
                params={"q": phone},
            )

            contacts = search_result.get("payload", [])
            if contacts:
                return contacts[0]

            # Create new contact if not found
            contact_data = {
                "inbox_id": self.inbox_id,
                "phone_number": phone,
            }
            if name:
                contact_data["name"] = name
            if email:
                contact_data["email"] = email
            if custom_attributes:
                contact_data["custom_attributes"] = custom_attributes

            result = await self._request(
                method="POST",
                endpoint="/contacts",
                json_data=contact_data,
            )

            logger.info("Contact created", contact_id=result.get("id"), phone=phone)
            return result.get("payload", {}).get("contact", result)

        except Exception as e:
            logger.error("Failed to find/create contact", phone=phone, error=str(e))
            return None

    async def criar_conversa(
        self,
        contact_id: int,
        source_id: str | None = None,
        custom_attributes: dict | None = None,
        status: str = "open",
    ) -> dict | None:
        """
        Create a new conversation for monitoring.

        Args:
            contact_id: Chatwoot contact ID
            source_id: External conversation ID (e.g., Evolution message ID)
            custom_attributes: Custom attributes for the conversation
            status: Conversation status (open, pending, resolved, snoozed)

        Returns:
            Conversation data if successful, None otherwise
        """
        try:
            conversation_data = {
                "inbox_id": self.inbox_id,
                "contact_id": contact_id,
                "status": status,
            }
            if source_id:
                conversation_data["source_id"] = source_id
            if custom_attributes:
                conversation_data["custom_attributes"] = custom_attributes

            result = await self._request(
                method="POST",
                endpoint="/conversations",
                json_data=conversation_data,
            )

            logger.info(
                "Conversation created",
                conversation_id=result.get("id"),
                contact_id=contact_id,
            )
            return result

        except Exception as e:
            logger.error("Failed to create conversation", error=str(e))
            return None

    async def buscar_conversa_por_contato(
        self,
        contact_id: int,
        status: str | None = None,
    ) -> dict | None:
        """
        Find existing conversation for a contact.

        Args:
            contact_id: Chatwoot contact ID
            status: Filter by status

        Returns:
            Conversation data if found, None otherwise
        """
        try:
            params = {}
            if status:
                params["status"] = status

            result = await self._request(
                method="GET",
                endpoint=f"/contacts/{contact_id}/conversations",
                params=params,
            )

            conversations = result.get("payload", [])
            # Return most recent open conversation
            for conv in conversations:
                if conv.get("status") in ["open", "pending"]:
                    return conv

            return conversations[0] if conversations else None

        except Exception as e:
            logger.error("Failed to find conversation", error=str(e))
            return None

    async def enviar_mensagem(
        self,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
        private: bool = False,
        content_attributes: dict | None = None,
    ) -> dict | None:
        """
        Send a message to a conversation.

        Args:
            conversation_id: Chatwoot conversation ID
            content: Message content
            message_type: "incoming" or "outgoing"
            private: If True, message is internal note (not visible to customer)
            content_attributes: Additional message attributes

        Returns:
            Message data if successful, None otherwise
        """
        try:
            message_data = {
                "content": content,
                "message_type": message_type,
                "private": private,
            }
            if content_attributes:
                message_data["content_attributes"] = content_attributes

            result = await self._request(
                method="POST",
                endpoint=f"/conversations/{conversation_id}/messages",
                json_data=message_data,
            )

            logger.info(
                "Message sent to Chatwoot",
                conversation_id=conversation_id,
                private=private,
            )
            return result

        except Exception as e:
            logger.error("Failed to send message", error=str(e))
            return None

    async def transferir_para_humano(
        self,
        conversation_id: int,
        team_id: int | None = None,
        assignee_id: int | None = None,
        message: str | None = None,
    ) -> bool:
        """
        Transfer conversation to human agent.

        Args:
            conversation_id: Chatwoot conversation ID
            team_id: Team ID to assign (uses default if not provided)
            assignee_id: Specific agent ID to assign
            message: Internal note explaining the transfer

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add internal note if message provided
            if message:
                await self.enviar_mensagem(
                    conversation_id=conversation_id,
                    content=f"🤖 Transferência automática: {message}",
                    message_type="outgoing",
                    private=True,
                )

            # Assign to team or agent
            assignment_data = {}
            if assignee_id:
                assignment_data["assignee_id"] = assignee_id
            elif team_id or self.human_team_id:
                assignment_data["team_id"] = team_id or self.human_team_id

            if assignment_data:
                await self._request(
                    method="POST",
                    endpoint=f"/conversations/{conversation_id}/assignments",
                    json_data=assignment_data,
                )

            # Add label to indicate bot handoff
            await self.adicionar_labels(conversation_id, ["human_needed", "bot_handoff"])

            logger.info(
                "Conversation transferred to human",
                conversation_id=conversation_id,
                team_id=team_id or self.human_team_id,
                assignee_id=assignee_id,
            )
            return True

        except Exception as e:
            logger.error("Failed to transfer to human", error=str(e))
            return False

    async def adicionar_labels(
        self,
        conversation_id: int,
        labels: list[str],
    ) -> bool:
        """
        Add labels to a conversation.

        Args:
            conversation_id: Chatwoot conversation ID
            labels: List of label names

        Returns:
            True if successful, False otherwise
        """
        try:
            await self._request(
                method="POST",
                endpoint=f"/conversations/{conversation_id}/labels",
                json_data={"labels": labels},
            )

            logger.info("Labels added", conversation_id=conversation_id, labels=labels)
            return True

        except Exception as e:
            logger.error("Failed to add labels", error=str(e))
            return False

    async def atualizar_status(
        self,
        conversation_id: int,
        status: str,
    ) -> bool:
        """
        Update conversation status.

        Args:
            conversation_id: Chatwoot conversation ID
            status: New status (open, pending, resolved, snoozed)

        Returns:
            True if successful, False otherwise
        """
        try:
            await self._request(
                method="POST",
                endpoint=f"/conversations/{conversation_id}/toggle_status",
                json_data={"status": status},
            )

            logger.info(
                "Status updated",
                conversation_id=conversation_id,
                status=status,
            )
            return True

        except Exception as e:
            logger.error("Failed to update status", error=str(e))
            return False

    async def sincronizar_mensagem(
        self,
        phone: str,
        content: str,
        direction: str,
        name: str | None = None,
        message_id: str | None = None,
    ) -> dict | None:
        """
        Sync a WhatsApp message to Chatwoot for monitoring.

        This is the main method used to keep Chatwoot in sync with Evolution API.

        Args:
            phone: Contact phone number
            content: Message content
            direction: "inbound" or "outbound"
            name: Contact name (for new contacts)
            message_id: External message ID for deduplication

        Returns:
            Synced message data if successful, None otherwise
        """
        try:
            # Find or create contact
            contact = await self.buscar_ou_criar_contato(
                phone=phone,
                name=name,
                custom_attributes={"source": "evolution_api"},
            )
            if not contact:
                return None

            contact_id = contact.get("id")

            # Find or create conversation
            conversation = await self.buscar_conversa_por_contato(contact_id)
            if not conversation:
                conversation = await self.criar_conversa(
                    contact_id=contact_id,
                    source_id=message_id,
                    custom_attributes={
                        "source": "evolution_api",
                        "bot_handling": True,
                    },
                )
            if not conversation:
                return None

            conversation_id = conversation.get("id")

            # Send message
            message_type = "incoming" if direction == "inbound" else "outgoing"
            result = await self.enviar_mensagem(
                conversation_id=conversation_id,
                content=content,
                message_type=message_type,
                content_attributes={"external_id": message_id} if message_id else None,
            )

            # Add bot_handling label for tracking
            if direction == "outbound":
                await self.adicionar_labels(conversation_id, ["bot_handling"])

            return {
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "message": result,
            }

        except Exception as e:
            logger.error("Failed to sync message", phone=phone, error=str(e))
            return None


@lru_cache
def get_chatwoot_service() -> ChatwootService:
    """Get cached ChatwootService instance."""
    return ChatwootService()


# Convenience functions for tools
async def sincronizar_mensagem_chatwoot(
    phone: str,
    content: str,
    direction: str,
    name: str | None = None,
    message_id: str | None = None,
) -> dict | None:
    """
    Sync a message to Chatwoot for monitoring.

    Args:
        phone: Contact phone number
        content: Message content
        direction: "inbound" or "outbound"
        name: Contact name
        message_id: External message ID

    Returns:
        Sync result if successful, None otherwise
    """
    service = get_chatwoot_service()
    return await service.sincronizar_mensagem(
        phone=phone,
        content=content,
        direction=direction,
        name=name,
        message_id=message_id,
    )


async def transferir_para_humano(
    conversation_id: int,
    motivo: str,
    team_id: int | None = None,
) -> bool:
    """
    Transfer conversation to human agent.

    Args:
        conversation_id: Chatwoot conversation ID
        motivo: Reason for transfer
        team_id: Team to assign (uses default if not provided)

    Returns:
        True if successful, False otherwise
    """
    service = get_chatwoot_service()
    return await service.transferir_para_humano(
        conversation_id=conversation_id,
        team_id=team_id,
        message=motivo,
    )
