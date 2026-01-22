"""
Cross-service synchronization orchestrator.

Handles bidirectional sync between:
- Twenty CRM ↔ Cal.com (contacts with appointments)
- Twenty CRM ↔ Chatwoot (contacts with conversations)
- Cal.com ↔ Chatwoot (booking notifications)

This is the glue that makes the three platforms work together.
"""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.models import Clinic

from .twenty import TwentyClient, TwentyAPIError
from .calcom import CalcomClient, CalcomAPIError
from .chatwoot import ChatwootClient, ChatwootAPIError

logger = logging.getLogger(__name__)
settings = get_settings()


class SyncError(Exception):
    """Sync operation failed."""
    pass


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256",
    timestamp: str | None = None,
) -> bool:
    """
    Verify webhook signature using HMAC.

    Supports common formats:
    - sha256=<hex>
    - <hex>
    - Twenty CRM format: timestamp:payload
    """
    if not secret or not signature:
        return False

    # Parse signature format (some services prefix with algorithm=)
    if "=" in signature and not signature.startswith("sha"):
        # Format: sha256=<hex>
        parts = signature.split("=", 1)
        if len(parts) == 2:
            algorithm = parts[0]
            signature = parts[1]

    # Build the string to sign
    # Twenty CRM uses timestamp:payload format
    if timestamp:
        string_to_sign = f"{timestamp}:".encode() + payload
    else:
        string_to_sign = payload

    # Compute expected signature
    if algorithm == "sha256":
        expected = hmac.new(
            secret.encode(),
            string_to_sign,
            hashlib.sha256,
        ).hexdigest()
    elif algorithm == "sha1":
        expected = hmac.new(
            secret.encode(),
            string_to_sign,
            hashlib.sha1,
        ).hexdigest()
    else:
        return False

    logger.info(f"Signature verification: expected={expected[:16]}..., received={signature[:16]}...")
    return hmac.compare_digest(expected, signature)


class SyncService:
    """
    Orchestrates data sync between Twenty CRM, Cal.com, and Chatwoot.

    Usage:
        sync = SyncService(db, clinic)
        await sync.setup_webhooks()
        await sync.sync_contact_to_chatwoot(contact_id)
    """

    def __init__(
        self,
        db: AsyncSession,
        clinic: Clinic | None = None,
    ):
        self.db = db
        self.clinic = clinic

        # Initialize clients with clinic-specific credentials if available
        self._twenty: TwentyClient | None = None
        self._calcom: CalcomClient | None = None
        self._chatwoot: ChatwootClient | None = None

    async def _get_twenty(self) -> TwentyClient:
        if self._twenty is None:
            workspace_id = self.clinic.twenty_workspace_id if self.clinic else None
            self._twenty = TwentyClient(workspace_id=workspace_id)
        return self._twenty

    async def _get_calcom(self) -> CalcomClient:
        if self._calcom is None:
            # Cal.com uses team-based isolation
            self._calcom = CalcomClient()
        return self._calcom

    async def _get_chatwoot(self) -> ChatwootClient:
        if self._chatwoot is None:
            # Get account ID from clinic settings
            account_id = None
            if self.clinic and self.clinic.settings:
                account_id = self.clinic.settings.get("chatwoot_account_id")
            self._chatwoot = ChatwootClient(account_id=account_id)
        return self._chatwoot

    async def close(self) -> None:
        """Close all client connections."""
        if self._twenty:
            await self._twenty.close()
        if self._calcom:
            await self._calcom.close()
        if self._chatwoot:
            await self._chatwoot.close()

    # =========================================================================
    # WEBHOOK SETUP
    # =========================================================================

    async def setup_webhooks(self, base_url: str) -> dict[str, Any]:
        """
        Register webhooks for all services.

        Returns status of each webhook registration.
        """
        results: dict[str, Any] = {}

        # Twenty CRM webhooks
        try:
            twenty = await self._get_twenty()
            result = await twenty.register_webhook(
                url=f"{base_url}/api/sync/webhooks/twenty",
                events=["person.created", "person.updated", "opportunity.updated"],
            )
            results["twenty"] = {"success": True, "webhook_id": result.get("id")}
        except TwentyAPIError as e:
            results["twenty"] = {"success": False, "error": str(e)}

        # Cal.com webhooks
        try:
            calcom = await self._get_calcom()
            result = await calcom.create_webhook(
                subscriber_url=f"{base_url}/api/sync/webhooks/calcom",
                event_triggers=["BOOKING_CREATED", "BOOKING_RESCHEDULED", "BOOKING_CANCELLED"],
            )
            results["calcom"] = {"success": True, "webhook_id": result.get("id")}
        except CalcomAPIError as e:
            results["calcom"] = {"success": False, "error": str(e)}

        # Chatwoot webhooks
        try:
            chatwoot = await self._get_chatwoot()
            result = await chatwoot.create_webhook(
                url=f"{base_url}/api/sync/webhooks/chatwoot",
                subscriptions=[
                    "message_created",
                    "conversation_created",
                    "conversation_status_changed",
                    "contact_created",
                ],
            )
            results["chatwoot"] = {"success": True, "webhook_id": result.get("id")}
        except ChatwootAPIError as e:
            results["chatwoot"] = {"success": False, "error": str(e)}

        return results

    # =========================================================================
    # TWENTY → CHATWOOT SYNC
    # =========================================================================

    async def sync_twenty_contact_to_chatwoot(
        self,
        twenty_contact: dict,
    ) -> dict | None:
        """
        Create or update Chatwoot contact from Twenty CRM contact.

        Returns the Chatwoot contact if successful.
        """
        chatwoot = await self._get_chatwoot()

        # Extract data from Twenty format
        name_data = twenty_contact.get("name", {})
        full_name = f"{name_data.get('firstName', '')} {name_data.get('lastName', '')}".strip()
        email_data = twenty_contact.get("email", {})
        email = email_data.get("primaryEmail")
        phone_data = twenty_contact.get("phone", {})
        phone = phone_data.get("primaryPhoneNumber")

        if not full_name:
            logger.warning("Cannot sync contact without name")
            return None

        try:
            # Check if contact exists by email or phone
            existing = None
            if email:
                search_result = await chatwoot.search_contacts(email)
                contacts = search_result.get("payload", [])
                if contacts:
                    existing = contacts[0]
            elif phone:
                search_result = await chatwoot.search_contacts(phone)
                contacts = search_result.get("payload", [])
                if contacts:
                    existing = contacts[0]

            if existing:
                # Update existing contact
                return await chatwoot.update_contact(
                    existing["id"],
                    name=full_name,
                    email=email,
                    phone_number=phone,
                    custom_attributes={"twenty_id": twenty_contact.get("id")},
                )
            else:
                # Create new contact
                inbox_id = None
                if self.clinic and self.clinic.chatwoot_inbox_id:
                    inbox_id = int(self.clinic.chatwoot_inbox_id)

                return await chatwoot.create_contact(
                    name=full_name,
                    email=email,
                    phone_number=phone,
                    inbox_id=inbox_id,
                    custom_attributes={"twenty_id": twenty_contact.get("id")},
                )
        except ChatwootAPIError as e:
            logger.error(f"Failed to sync contact to Chatwoot: {e}")
            return None

    # =========================================================================
    # TWENTY → CALCOM SYNC
    # =========================================================================

    async def create_calcom_booking_for_opportunity(
        self,
        opportunity: dict,
        event_type_id: int,
        start_time: datetime,
    ) -> dict | None:
        """
        Create a Cal.com booking from a Twenty opportunity.

        Used when an opportunity reaches a stage that requires scheduling.
        """
        calcom = await self._get_calcom()

        # Get contact info from opportunity
        contact = opportunity.get("pointOfContact", {})
        if not contact:
            logger.warning("Opportunity has no contact, cannot create booking")
            return None

        name_data = contact.get("name", {})
        attendee_name = f"{name_data.get('firstName', '')} {name_data.get('lastName', '')}".strip()
        email_data = contact.get("email", {})
        attendee_email = email_data.get("primaryEmail")

        if not attendee_email:
            logger.warning("Contact has no email, cannot create booking")
            return None

        try:
            return await calcom.create_booking(
                event_type_id=event_type_id,
                start=start_time,
                attendee_email=attendee_email,
                attendee_name=attendee_name,
                metadata={
                    "twenty_opportunity_id": opportunity.get("id"),
                    "twenty_contact_id": contact.get("id"),
                },
            )
        except CalcomAPIError as e:
            logger.error(f"Failed to create Cal.com booking: {e}")
            return None

    # =========================================================================
    # CALCOM → TWENTY SYNC
    # =========================================================================

    async def sync_calcom_booking_to_twenty(
        self,
        booking: dict,
    ) -> dict | None:
        """
        Create or update Twenty opportunity/activity from Cal.com booking.
        """
        twenty = await self._get_twenty()

        # Get attendee info
        attendees = booking.get("attendees", [])
        if not attendees:
            logger.warning("Booking has no attendees")
            return None

        attendee = attendees[0]
        email = attendee.get("email")
        name = attendee.get("name", "")

        try:
            # Find or create contact in Twenty
            contacts = await twenty.list_contacts(
                filter_={"email": {"primaryEmail": {"eq": email}}} if email else None
            )

            contact_id = None
            edges = contacts.get("edges", [])
            if edges:
                contact_id = edges[0]["node"]["id"]
            else:
                # Create contact
                name_parts = name.split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                new_contact = await twenty.create_contact(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )
                contact_id = new_contact.get("id")

            if not contact_id:
                return None

            # Check booking metadata for existing opportunity
            metadata = booking.get("metadata", {})
            opportunity_id = metadata.get("twenty_opportunity_id")

            if opportunity_id:
                # Update opportunity stage based on booking status
                status = booking.get("status", "")
                stage = "MEETING_SCHEDULED"
                if status == "CANCELLED":
                    stage = "CANCELLED"
                elif status == "COMPLETED":
                    stage = "MEETING_COMPLETED"

                return await twenty.update_opportunity_stage(opportunity_id, stage)
            else:
                # Create new opportunity
                return await twenty.create_opportunity(
                    name=f"Consulta - {name}",
                    stage="MEETING_SCHEDULED",
                    contact_id=contact_id,
                    closeDate=booking.get("startTime"),
                )
        except TwentyAPIError as e:
            logger.error(f"Failed to sync booking to Twenty: {e}")
            return None

    # =========================================================================
    # CALCOM → CHATWOOT SYNC
    # =========================================================================

    async def send_booking_notification_to_chatwoot(
        self,
        booking: dict,
        event_type: str = "created",
    ) -> dict | None:
        """
        Send booking notification to Chatwoot conversation.

        Creates a notification message about the booking event.
        """
        chatwoot = await self._get_chatwoot()

        attendees = booking.get("attendees", [])
        if not attendees:
            return None

        attendee = attendees[0]
        email = attendee.get("email")
        phone = attendee.get("phone")

        # Find contact in Chatwoot
        try:
            contact = None
            if email:
                search_result = await chatwoot.search_contacts(email)
                contacts = search_result.get("payload", [])
                if contacts:
                    contact = contacts[0]
            elif phone:
                search_result = await chatwoot.search_contacts(phone)
                contacts = search_result.get("payload", [])
                if contacts:
                    contact = contacts[0]

            if not contact:
                logger.info("No Chatwoot contact found for booking notification")
                return None

            # Find open conversation for this contact
            conversations = await chatwoot.list_conversations(status="open")
            contact_conversation = None
            for conv in conversations.get("data", {}).get("payload", []):
                if conv.get("meta", {}).get("contact", {}).get("id") == contact["id"]:
                    contact_conversation = conv
                    break

            if not contact_conversation:
                logger.info("No open conversation for contact")
                return None

            # Build notification message
            start_time = booking.get("startTime", "")
            event_title = booking.get("title", "Consulta")

            if event_type == "created":
                message = f"✅ Agendamento confirmado!\n\n📅 {event_title}\n🕐 {start_time}\n\nAté breve!"
            elif event_type == "rescheduled":
                message = f"🔄 Agendamento reagendado\n\n📅 {event_title}\n🕐 Nova data: {start_time}"
            elif event_type == "cancelled":
                message = f"❌ Agendamento cancelado\n\n📅 {event_title}\n\nCaso queira reagendar, entre em contato."
            else:
                message = f"📅 Atualização: {event_title}"

            return await chatwoot.send_message(
                conversation_id=contact_conversation["id"],
                content=message,
                message_type="outgoing",
            )
        except ChatwootAPIError as e:
            logger.error(f"Failed to send booking notification: {e}")
            return None

    # =========================================================================
    # CHATWOOT → TWENTY SYNC
    # =========================================================================

    async def sync_chatwoot_contact_to_twenty(
        self,
        chatwoot_contact: dict,
    ) -> dict | None:
        """
        Create or update Twenty CRM contact from Chatwoot contact.
        """
        twenty = await self._get_twenty()

        name = chatwoot_contact.get("name", "")
        email = chatwoot_contact.get("email")
        phone = chatwoot_contact.get("phone_number")

        if not name:
            logger.warning("Cannot sync contact without name")
            return None

        try:
            # Check if contact exists by custom attribute
            custom_attrs = chatwoot_contact.get("custom_attributes", {})
            twenty_id = custom_attrs.get("twenty_id")

            if twenty_id:
                # Update existing contact
                return await twenty.update_contact(
                    twenty_id,
                    email={"primaryEmail": email} if email else None,
                    phone={"primaryPhoneNumber": phone} if phone else None,
                )
            else:
                # Try to find by email or create new
                existing = None
                if email:
                    contacts = await twenty.list_contacts(
                        filter_={"email": {"primaryEmail": {"eq": email}}}
                    )
                    edges = contacts.get("edges", [])
                    if edges:
                        existing = edges[0]["node"]

                if existing:
                    return existing

                # Create new contact
                name_parts = name.split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                return await twenty.create_contact(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                )
        except TwentyAPIError as e:
            logger.error(f"Failed to sync contact to Twenty: {e}")
            return None

    # =========================================================================
    # FULL CLINIC SYNC
    # =========================================================================

    async def sync_clinic(self, clinic_id: str) -> dict[str, Any]:
        """
        Full sync of a clinic across all services.

        This is typically run on onboarding or reconciliation.
        """
        # Load clinic
        result = await self.db.execute(select(Clinic).where(Clinic.id == clinic_id))
        clinic = result.scalar_one_or_none()
        if not clinic:
            raise SyncError(f"Clinic {clinic_id} not found")

        self.clinic = clinic
        sync_results: dict[str, Any] = {
            "clinic_id": clinic_id,
            "contacts_synced": 0,
            "errors": [],
        }

        try:
            twenty = await self._get_twenty()

            # Sync contacts from Twenty to Chatwoot
            contacts = await twenty.list_contacts(limit=100)
            for edge in contacts.get("edges", []):
                contact = edge.get("node", {})
                try:
                    await self.sync_twenty_contact_to_chatwoot(contact)
                    sync_results["contacts_synced"] += 1
                except Exception as e:
                    sync_results["errors"].append(f"Contact {contact.get('id')}: {str(e)}")

        except Exception as e:
            sync_results["errors"].append(f"Twenty sync failed: {str(e)}")

        return sync_results
