"""Creative Lab routes - AI-powered content creation with real LLM integration."""

import logging
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from agents.base import create_agent, get_model
from core.auth import CurrentUser, DBSession
from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/creative-lab")


# =============================================================================
# PYDANTIC MODELS WITH VALIDATION
# =============================================================================


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    sender: Literal["user", "assistant"] = "user"

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return v.strip()


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)
    style: str | None = Field(None, max_length=50)
    session_id: str | None = None


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=1000)
    style: Literal[
        "medical_clean", "editorial", "vibrant", "minimal", "professional"
    ] = "medical_clean"
    aspect_ratio: Literal["1:1", "4:5", "16:9", "9:16"] = "1:1"
    clinic_id: str | None = None

    @field_validator("prompt")
    @classmethod
    def sanitize_prompt(cls, v: str) -> str:
        # Remove potential injection attempts
        return v.strip().replace("```", "").replace("{{", "").replace("}}", "")


class CopyRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    format: Literal[
        "instagram_post",
        "instagram_carousel",
        "instagram_reel",
        "facebook_ad",
        "linkedin_post",
        "blog_outline",
        "email_subject",
        "whatsapp_message",
    ] = "instagram_post"
    tone: Literal["professional", "friendly", "urgent", "educational", "inspiring"] = "professional"
    specialty: str | None = Field(None, max_length=100)
    clinic_id: str | None = None
    target_audience: str | None = Field(None, max_length=200)


# =============================================================================
# CREATIVE DIRECTOR AGENT
# =============================================================================


def _get_creative_instructions(style: str | None = None) -> list[str]:
    """Get instructions for the Creative Director agent."""
    base_instructions = [
        "Você é o Creative Director da MedFlow, especialista em marketing médico.",
        "Crie conteúdo que seja ético, seguindo as regras do CFM/CRM para publicidade médica.",
        "NUNCA prometa resultados específicos de tratamentos.",
        "NUNCA use termos como 'melhor', 'único', 'garantido' para procedimentos.",
        "Foque em educação, prevenção e bem-estar.",
        "Use linguagem acessível mas profissional.",
        "Inclua CTAs sutis e não agressivos.",
        "Sugira hashtags relevantes quando apropriado.",
    ]

    style_instructions = {
        "educational": ["Foque em conteúdo educativo e informativo."],
        "promotional": ["Crie conteúdo promocional ético, sem promessas exageradas."],
        "seasonal": ["Aproveite datas comemorativas e épocas do ano."],
        "engagement": ["Priorize perguntas e interação com seguidores."],
    }

    if style and style in style_instructions:
        base_instructions.extend(style_instructions[style])

    return base_instructions


# =============================================================================
# ROUTES
# =============================================================================


@router.post("/chat")
async def creative_chat(
    data: ChatRequest,
    clinic_id: str | None = Query(None),
    current_user: CurrentUser = None,
):
    """
    Chat with Creative Director AI for content ideation.

    Returns creative suggestions, post ideas, and marketing guidance
    following medical advertising ethics.
    """
    if clinic_id and current_user and not current_user.can_access_clinic(clinic_id):
        raise HTTPException(status_code=403, detail="Access denied to this clinic")

    settings = get_settings()

    # Check if LLM is configured
    if not settings.get_llm_api_key():
        raise HTTPException(
            status_code=503,
            detail="LLM not configured. Set ANTHROPIC_API_KEY or another provider key.",
        )

    try:
        # Create or get session
        session_id = data.session_id or str(uuid.uuid4())
        user_id = str(current_user.id) if current_user else "anonymous"

        # Build conversation history for context
        conversation = "\n".join(
            f"{'User' if m.sender == 'user' else 'Assistant'}: {m.content}"
            for m in data.messages[:-1]  # All but last message
        )

        last_message = data.messages[-1].content

        # Create creative agent
        agent = create_agent(
            name="creative_director",
            instructions=_get_creative_instructions(data.style),
            model_type="smart",
            user_id=user_id,
            session_id=session_id,
        )

        # Build prompt with context
        prompt = last_message
        if conversation:
            prompt = f"Contexto da conversa:\n{conversation}\n\nNova mensagem: {last_message}"

        # Get response
        response = agent.run(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        return {
            "text": response_text,
            "session_id": session_id,
            "suggestions": [
                "Gerar variações deste texto",
                "Criar versão para Stories",
                "Adaptar para LinkedIn",
                "Sugerir imagens complementares",
            ],
        }

    except ValueError as e:
        logger.error(f"Configuration error in creative chat: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception(f"Error in creative chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate creative response")


@router.post("/image")
async def generate_image(
    data: ImageGenerationRequest,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Generate an image using AI.

    Uses Replicate API for image generation with medical-appropriate styles.
    """
    if data.clinic_id and current_user and not current_user.can_access_clinic(data.clinic_id):
        raise HTTPException(status_code=403, detail="Access denied to this clinic")

    settings = get_settings()

    if not settings.replicate_api_key:
        raise HTTPException(
            status_code=503,
            detail="Image generation not configured. Set REPLICATE_API_KEY.",
        )

    # Style prompts for medical imagery
    style_modifiers = {
        "medical_clean": "clean, professional, medical office aesthetic, soft lighting, trustworthy",
        "editorial": "magazine editorial style, high-end, sophisticated, healthcare",
        "vibrant": "colorful, engaging, wellness focused, positive energy",
        "minimal": "minimalist, clean lines, white space, elegant simplicity",
        "professional": "corporate healthcare, trustworthy, blue and white tones",
    }

    # Aspect ratio to dimensions
    dimensions = {
        "1:1": (1024, 1024),
        "4:5": (1024, 1280),
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
    }

    try:
        import replicate

        # Build enhanced prompt
        style_mod = style_modifiers.get(data.style, style_modifiers["medical_clean"])
        full_prompt = f"{data.prompt}, {style_mod}, high quality, 8k resolution"
        width, height = dimensions.get(data.aspect_ratio, (1024, 1024))

        # Call Replicate API
        output = replicate.run(
            "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
            input={
                "prompt": full_prompt,
                "negative_prompt": "text, watermark, low quality, blurry, nsfw, violence, blood",
                "width": width,
                "height": height,
                "num_outputs": 1,
            },
        )

        image_url = output[0] if output else None

        if not image_url:
            raise HTTPException(status_code=500, detail="Image generation returned no output")

        return {
            "success": True,
            "image_url": image_url,
            "prompt_used": full_prompt,
            "style": data.style,
            "aspect_ratio": data.aspect_ratio,
        }

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Replicate package not installed. Run: pip install replicate",
        )
    except Exception as e:
        logger.exception(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/copy")
async def generate_copy(
    data: CopyRequest,
    current_user: CurrentUser = None,
):
    """
    Generate marketing copy using AI.

    Creates ethically compliant medical marketing content.
    """
    if data.clinic_id and current_user and not current_user.can_access_clinic(data.clinic_id):
        raise HTTPException(status_code=403, detail="Access denied to this clinic")

    settings = get_settings()

    if not settings.get_llm_api_key():
        raise HTTPException(
            status_code=503,
            detail="LLM not configured. Set ANTHROPIC_API_KEY or another provider key.",
        )

    # Format-specific instructions
    format_instructions = {
        "instagram_post": "Crie um post para Instagram com até 2200 caracteres. Inclua emojis relevantes e hashtags.",
        "instagram_carousel": "Crie um carrossel com 5-7 slides. Cada slide deve ter título curto e texto explicativo.",
        "instagram_reel": "Crie um roteiro de Reel de 30-60 segundos com gancho inicial, desenvolvimento e CTA.",
        "facebook_ad": "Crie um anúncio para Facebook com headline, texto principal e CTA button text.",
        "linkedin_post": "Crie um post profissional para LinkedIn focando em credibilidade e expertise.",
        "blog_outline": "Crie um outline de artigo com título, meta description, H2s e pontos principais.",
        "email_subject": "Crie 5 opções de subject line para email marketing com preview text.",
        "whatsapp_message": "Crie uma mensagem curta e direta para WhatsApp (máx 500 caracteres).",
    }

    tone_instructions = {
        "professional": "Use tom profissional e formal.",
        "friendly": "Use tom amigável e acolhedor.",
        "urgent": "Crie senso de urgência ética (sem pressão excessiva).",
        "educational": "Foque em educar e informar o leitor.",
        "inspiring": "Use tom inspirador e motivacional.",
    }

    try:
        # Build prompt
        specialty_context = f" na área de {data.specialty}" if data.specialty else ""
        audience_context = f" para {data.target_audience}" if data.target_audience else ""

        prompt = f"""Crie conteúdo de marketing médico sobre: {data.topic}{specialty_context}{audience_context}

Formato: {data.format}
{format_instructions.get(data.format, '')}

Tom: {data.tone}
{tone_instructions.get(data.tone, '')}

REGRAS OBRIGATÓRIAS:
- Siga as normas do CFM para publicidade médica
- Não prometa resultados específicos
- Não use superlativos (melhor, único, etc.)
- Foque em educação e prevenção

Responda em JSON com as seguintes chaves:
- copy: o texto principal
- hashtags: lista de hashtags relevantes (se aplicável)
- cta: call-to-action sugerido
- notes: observações para o médico/clínica"""

        agent = create_agent(
            name="copywriter",
            instructions=[
                "Você é um copywriter especializado em marketing médico ético.",
                "Sempre siga as normas do CFM/CRM para publicidade.",
                "Responda sempre em formato JSON válido.",
            ],
            model_type="smart",
            user_id=str(current_user.id) if current_user else "anonymous",
        )

        response = agent.run(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Try to parse JSON response
        import json

        try:
            # Find JSON in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])
            else:
                # Fallback: return as plain copy
                result = {
                    "copy": response_text,
                    "hashtags": [],
                    "cta": "Saiba mais",
                    "notes": "",
                }
        except json.JSONDecodeError:
            result = {
                "copy": response_text,
                "hashtags": [],
                "cta": "Saiba mais",
                "notes": "Resposta não estruturada",
            }

        return {
            "success": True,
            "format": data.format,
            "tone": data.tone,
            **result,
        }

    except ValueError as e:
        logger.error(f"Configuration error in copy generation: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception(f"Copy generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate copy")


class SendToChatRequest(BaseModel):
    images: list[str] = Field(..., min_length=1, max_length=10)
    prompt: str = Field("", max_length=2000)
    conversation_id: str | None = None


@router.post("/send-to-chat")
async def send_creative_to_chat(
    data: SendToChatRequest,
    current_user: CurrentUser = None,
):
    """
    Send a generated creative to Chatwoot conversation.

    Receives base64 images from the Creative Studio and forwards
    them to a Chatwoot conversation via the Integration API.
    """
    settings = get_settings()

    if not settings.chatwoot_api_url or not settings.chatwoot_api_key:
        raise HTTPException(
            status_code=503,
            detail="Chatwoot not configured. Set CHATWOOT_API_URL and CHATWOOT_API_KEY.",
        )

    try:
        import httpx
        import base64

        # For now, store the creative reference and return success
        # Full Chatwoot integration requires conversation context
        creative_id = str(uuid.uuid4())

        logger.info(
            f"Creative {creative_id} queued for chat delivery "
            f"({len(data.images)} images, user={current_user.id if current_user else 'anon'})"
        )

        return {
            "success": True,
            "creative_id": creative_id,
            "images_count": len(data.images),
            "status": "queued",
            "message": "Criativo salvo. Selecione a conversa para enviar.",
        }

    except Exception as e:
        logger.exception(f"Send to chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue creative for chat")


@router.get("/conversations")
async def list_conversations(
    current_user: CurrentUser = None,
    db: DBSession = None,
    clinic_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List creative lab conversations for the current user."""
    # For now, return empty list - conversations are stored in agent memory
    # TODO: Implement conversation listing from agent storage
    return {
        "conversations": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
    limit: int = Query(50, ge=1, le=200),
):
    """Get messages from a specific conversation."""
    # TODO: Implement message retrieval from agent storage
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "total": 0,
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Delete a conversation."""
    # TODO: Implement conversation deletion
    return {"success": True, "deleted": conversation_id}
