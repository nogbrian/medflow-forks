"""Evolution API (WhatsApp) webhook receiver.

Handles incoming WhatsApp messages and status updates from Evolution API,
routes them through the agent coordinator for processing.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pydantic import BaseModel

from core.config import get_settings
from webhooks.signatures import verify_evolution_signature

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


class EvolutionMessage(BaseModel):
    """Parsed Evolution API message payload."""

    instance: str = ""
    phone: str = ""
    name: str = ""
    content: str = ""
    message_id: str = ""
    message_type: str = "text"  # text, image, audio, video, document
    is_group: bool = False
    timestamp: int = 0
    media_url: str | None = None


@router.post("/webhooks/evolution")
async def handle_evolution_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(None, alias="x-api-key"),
    authorization: str | None = Header(None),
):
    """Handle webhooks from Evolution API (WhatsApp).

    Events:
    - messages.upsert: New incoming message
    - messages.update: Message status update (sent, delivered, read)
    - connection.update: Instance connection status
    - qrcode.updated: QR code for new connections
    """
    body = await request.body()

    # Verify authentication
    auth_header = x_api_key or authorization
    if not verify_evolution_signature(body, auth_header, settings.evolution_api_key):
        logger.warning("Evolution webhook auth failed")
        raise HTTPException(status_code=401, detail="Invalid API key")

    payload = await request.json()
    event = payload.get("event", "")
    instance = payload.get("instance", "")
    data = payload.get("data", payload)

    logger.info(f"Evolution webhook: event={event}, instance={instance}")

    if event == "messages.upsert":
        message = _parse_message(data, instance)
        if message and not message.is_group:
            background_tasks.add_task(_process_incoming_message, message)

    elif event == "messages.update":
        # Status updates (delivered, read) - log for metrics
        logger.info(f"Message status update: {data.get('status', 'unknown')}")

    elif event == "connection.update":
        state = data.get("state", "")
        logger.info(f"Evolution instance '{instance}' connection: {state}")

    return {"received": True, "event": event}


def _parse_message(data: Any, instance: str) -> EvolutionMessage | None:
    """Parse Evolution API message payload into structured format."""
    try:
        # Evolution API v2 format
        if isinstance(data, list):
            data = data[0] if data else {}

        key = data.get("key", {})
        message_content = data.get("message", {})

        # Skip outgoing messages
        if key.get("fromMe", False):
            return None

        # Extract phone number (remove @s.whatsapp.net suffix)
        remote_jid = key.get("remoteJid", "")
        phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

        # Check if group
        is_group = "@g.us" in remote_jid

        # Extract message content
        content = ""
        message_type = "text"
        media_url = None

        if "conversation" in message_content:
            content = message_content["conversation"]
        elif "extendedTextMessage" in message_content:
            content = message_content["extendedTextMessage"].get("text", "")
        elif "imageMessage" in message_content:
            message_type = "image"
            content = message_content["imageMessage"].get("caption", "[Imagem]")
            media_url = message_content["imageMessage"].get("url")
        elif "audioMessage" in message_content:
            message_type = "audio"
            content = "[Áudio recebido]"
        elif "videoMessage" in message_content:
            message_type = "video"
            content = message_content["videoMessage"].get("caption", "[Vídeo]")
        elif "documentMessage" in message_content:
            message_type = "document"
            content = message_content["documentMessage"].get("fileName", "[Documento]")

        if not content and not media_url:
            return None

        # Extract sender name
        push_name = data.get("pushName", "")

        return EvolutionMessage(
            instance=instance,
            phone=phone,
            name=push_name,
            content=content,
            message_id=key.get("id", ""),
            message_type=message_type,
            is_group=is_group,
            timestamp=data.get("messageTimestamp", 0),
            media_url=media_url,
        )

    except Exception as e:
        logger.error(f"Failed to parse Evolution message: {e}")
        return None


async def _process_incoming_message(message: EvolutionMessage) -> None:
    """Process an incoming WhatsApp message through the agent system.

    1. Sync to Chatwoot for monitoring
    2. Route through agent coordinator
    3. Send response back via WhatsApp
    """
    logger.info(
        f"Processing WhatsApp message: phone={message.phone}, "
        f"type={message.message_type}, content={message.content[:50]}"
    )

    # Step 1: Sync incoming message to Chatwoot
    try:
        from tools.chatwoot import sincronizar_mensagem_chatwoot
        await sincronizar_mensagem_chatwoot(
            phone=message.phone,
            content=message.content,
            direction="inbound",
            name=message.name,
            message_id=message.message_id,
        )
    except Exception as e:
        logger.error(f"Chatwoot sync failed: {e}")

    # Step 2: Route through agent coordinator
    try:
        from agents.coordinator import route_message

        routing = await route_message(
            message=message.content,
            contact_data={
                "phone": message.phone,
                "name": message.name,
            },
            conversation_context={
                "source": "whatsapp",
                "instance": message.instance,
                "message_type": message.message_type,
            },
        )

        agent_type = routing.get("agent", "sdr")
        logger.info(f"Routed to agent: {agent_type}")

        # Step 3: Run the agent
        from core.agentic.config import AgenticConfig
        from core.agentic.loop import AgenticLoop
        from core.llm_router import LLMRouter
        from api.routes.chat import _get_system_prompt, _get_tools_for_agent

        system_prompt = _get_system_prompt(agent_type)
        tools = _get_tools_for_agent(agent_type)

        config = AgenticConfig(
            max_turns=10,
            timeout_seconds=60,
            max_cost_usd=0.3,
            tier="smart",
        )

        loop = AgenticLoop(
            system_prompt=system_prompt,
            tools=tools,
            config=config,
            llm=LLMRouter(),
        )

        result = await loop.run(message.content)

        if result.success and result.final_response:
            # Step 4: Send response via WhatsApp
            await _send_whatsapp_response(
                instance=message.instance,
                phone=message.phone,
                content=result.final_response,
            )

            # Step 5: Sync outbound message to Chatwoot
            try:
                await sincronizar_mensagem_chatwoot(
                    phone=message.phone,
                    content=result.final_response,
                    direction="outbound",
                    name=message.name,
                )
            except Exception as e:
                logger.error(f"Chatwoot outbound sync failed: {e}")

    except Exception as e:
        logger.error(f"Agent processing failed for {message.phone}: {e}")


async def _send_whatsapp_response(
    instance: str,
    phone: str,
    content: str,
) -> None:
    """Send a response message via Evolution API."""
    import httpx

    if not settings.evolution_api_url:
        logger.warning("Evolution API URL not configured")
        return

    url = f"{settings.evolution_api_url}/message/sendText/{instance}"
    headers = {"apikey": settings.evolution_api_key or ""}

    payload = {
        "number": phone,
        "text": content,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                logger.error(f"Evolution API send failed: {response.status_code} {response.text}")
            else:
                logger.info(f"WhatsApp response sent to {phone}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
