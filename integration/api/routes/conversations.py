"""API routes for conversations - proxies to Chatwoot."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import require_auth
from core.logging import get_logger
from tools.chatwoot import get_chatwoot_service

logger = get_logger(__name__)
router = APIRouter(prefix="/conversations", tags=["Conversations"], dependencies=[Depends(require_auth)])


class MessageSend(BaseModel):
    content: str
    private: bool = False


class TransferRequest(BaseModel):
    motivo: str
    team_id: int | None = None
    assignee_id: int | None = None


class StatusUpdate(BaseModel):
    status: str  # open, pending, resolved, snoozed


class LabelUpdate(BaseModel):
    labels: list[str]


@router.get("")
async def list_conversations(
    status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
) -> dict:
    """List conversations from Chatwoot."""
    service = get_chatwoot_service()
    try:
        params: dict = {"page": page}
        if status:
            params["status"] = status

        result = await service._request(
            method="GET",
            endpoint="/conversations",
            params=params,
        )

        conversations = result.get("data", {}).get("payload", result.get("payload", []))
        meta = result.get("data", {}).get("meta", result.get("meta", {}))

        return {
            "data": conversations,
            "meta": meta,
            "page": page,
        }
    except Exception as e:
        logger.error("Failed to list conversations", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.get("/stats")
async def conversation_stats() -> dict:
    """Get conversation statistics."""
    service = get_chatwoot_service()
    try:
        # Get counts by status
        open_result = await service._request(
            method="GET",
            endpoint="/conversations",
            params={"status": "open", "page": 1},
        )
        pending_result = await service._request(
            method="GET",
            endpoint="/conversations",
            params={"status": "pending", "page": 1},
        )

        open_meta = open_result.get("data", {}).get("meta", open_result.get("meta", {}))
        pending_meta = pending_result.get("data", {}).get("meta", pending_result.get("meta", {}))

        return {
            "open": open_meta.get("all_count", 0),
            "pending": pending_meta.get("all_count", 0),
            "bot_handling": open_meta.get("all_count", 0),  # Approximation
        }
    except Exception as e:
        logger.error("Failed to get conversation stats", error=str(e))
        return {"open": 0, "pending": 0, "bot_handling": 0}


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: int) -> dict:
    """Get a specific conversation."""
    service = get_chatwoot_service()
    try:
        result = await service._request(
            method="GET",
            endpoint=f"/conversations/{conversation_id}",
        )
        return {"data": result}
    except Exception as e:
        logger.error("Failed to get conversation", error=str(e))
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
) -> dict:
    """Get messages for a conversation."""
    service = get_chatwoot_service()
    try:
        result = await service._request(
            method="GET",
            endpoint=f"/conversations/{conversation_id}/messages",
            params={"page": page},
        )

        messages = result.get("payload", [])
        meta = result.get("meta", {})

        return {
            "data": messages,
            "meta": meta,
            "page": page,
        }
    except Exception as e:
        logger.error("Failed to get messages", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get messages")


@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: int, body: MessageSend) -> dict:
    """Send a message to a conversation."""
    service = get_chatwoot_service()
    result = await service.enviar_mensagem(
        conversation_id=conversation_id,
        content=body.content,
        message_type="outgoing",
        private=body.private,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to send message")
    return {"data": result}


@router.post("/{conversation_id}/transfer")
async def transfer_to_human(conversation_id: int, body: TransferRequest) -> dict:
    """Transfer conversation to a human agent."""
    service = get_chatwoot_service()
    success = await service.transferir_para_humano(
        conversation_id=conversation_id,
        team_id=body.team_id,
        assignee_id=body.assignee_id,
        message=body.motivo,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to transfer")
    return {"status": "transferred", "conversation_id": conversation_id}


@router.post("/{conversation_id}/status")
async def update_status(conversation_id: int, body: StatusUpdate) -> dict:
    """Update conversation status."""
    service = get_chatwoot_service()
    success = await service.atualizar_status(
        conversation_id=conversation_id,
        status=body.status,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update status")
    return {"status": body.status, "conversation_id": conversation_id}


@router.post("/{conversation_id}/labels")
async def add_labels(conversation_id: int, body: LabelUpdate) -> dict:
    """Add labels to a conversation."""
    service = get_chatwoot_service()
    success = await service.adicionar_labels(
        conversation_id=conversation_id,
        labels=body.labels,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add labels")
    return {"status": "ok", "labels": body.labels}
