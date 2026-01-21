"""Creative Lab routes - AI-powered content creation."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.auth import CurrentUser, DBSession

router = APIRouter(prefix="/creative-lab")


class ChatMessage(BaseModel):
    content: str
    sender: str = "user"


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    style: str | None = None


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    style: str = "medical_clean"
    aspect_ratio: str = "1:1"
    clinic_id: str | None = None


class CopyRequest(BaseModel):
    topic: str
    format: str = "instagram_post"
    tone: str = "professional"
    specialty: str | None = None
    clinic_id: str | None = None


@router.post("/chat")
async def creative_chat(
    data: ChatRequest,
    clinic_id: str | None = Query(None),
    current_user: CurrentUser = None,
):
    """
    Chat with Creative Director AI.

    Can generate:
    - Social media posts (Instagram, Facebook, LinkedIn)
    - Carousels
    - Stories
    - Ad copies
    - Blog outlines
    """
    if clinic_id and not current_user.can_access_clinic(clinic_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Get the last user message
    last_message = data.messages[-1].content if data.messages else ""

    # TODO: Integrate with LLM
    return {
        "text": f"Resposta criativa para: {last_message[:50]}...",
        "suggestions": [
            "Gerar variações",
            "Criar carrossel",
            "Adaptar para Stories",
        ],
        "functionCalls": [],
    }


@router.post("/image")
async def generate_image(
    data: ImageGenerationRequest,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Generate an image using AI.

    Styles:
    - medical_clean: Clean, professional medical aesthetic
    - editorial: Magazine-style editorial
    - vibrant: Colorful and engaging
    - minimal: Minimalist design
    """
    if data.clinic_id and not current_user.can_access_clinic(data.clinic_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # TODO: Integrate with image generation service
    return {
        "success": True,
        "image_url": "https://placeholder.com/generated-image.png",
        "prompt_used": data.prompt,
        "style": data.style,
    }


@router.post("/copy")
async def generate_copy(
    data: CopyRequest,
    current_user: CurrentUser = None,
):
    """
    Generate marketing copy.

    Formats:
    - instagram_post: Single image post
    - instagram_carousel: Multi-slide carousel
    - instagram_reel: Reel script
    - facebook_ad: Facebook ad copy
    - linkedin_post: Professional LinkedIn post
    - blog_outline: Blog post outline
    """
    if data.clinic_id and not current_user.can_access_clinic(data.clinic_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # TODO: Integrate with copywriting agent
    return {
        "success": True,
        "copy": f"Copy gerado sobre {data.topic}...",
        "format": data.format,
        "hashtags": ["#saude", "#medicina", "#bemestar"],
        "cta": "Agende sua consulta!",
    }


@router.get("/conversations")
async def list_conversations(
    current_user: CurrentUser = None,
    db: DBSession = None,
    clinic_id: str | None = Query(None),
    limit: int = Query(20, le=100),
):
    """List creative lab conversations."""
    # TODO: Fetch from database
    return {
        "conversations": [],
        "total": 0,
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Get messages from a conversation."""
    # TODO: Fetch from database
    return {
        "messages": [],
        "total": 0,
    }


@router.post("/conversations/{conversation_id}/messages")
async def add_message_to_conversation(
    conversation_id: str,
    data: ChatMessage,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Add a message to a conversation and get AI response."""
    # TODO: Process message and get response
    return {
        "user_message": data.content,
        "ai_response": "Resposta do Creative Director...",
    }
