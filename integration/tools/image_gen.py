"""Image generation tools using NanoBanana/MoviAPI."""

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ImageGenClient:
    """Client for image generation API."""

    def __init__(self):
        self.api_key = settings.nanobanana_api_key
        self.base_url = "https://api.nanobanana.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
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
    ) -> dict:
        """Make an HTTP request to the image generation API."""
        url = f"{self.base_url}/{endpoint}"

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()


_client = ImageGenClient()


async def gerar_imagem(
    prompt: str,
    estilo: str = "realistic",
    tamanho: str = "1024x1024",
    modelo: str = "flux-pro",
) -> dict[str, Any] | None:
    """
    Generate an image from a text prompt.

    Args:
        prompt: Text description of the image
        estilo: Style preset (realistic, artistic, cartoon, etc.)
        tamanho: Image dimensions (1024x1024, 1024x1792, 1792x1024)
        modelo: Model to use for generation

    Returns:
        Generated image data with URL, or None if failed
    """
    try:
        # Add style modifier to prompt
        style_modifiers = {
            "realistic": "photorealistic, high quality, 8k",
            "artistic": "artistic, painterly style, creative",
            "cartoon": "cartoon style, vibrant colors, illustrated",
            "minimal": "minimalist design, clean, simple",
            "medical": "professional medical imagery, clean, clinical",
        }

        enhanced_prompt = f"{prompt}, {style_modifiers.get(estilo, '')}"

        payload = {
            "prompt": enhanced_prompt,
            "model": modelo,
            "size": tamanho,
            "n": 1,
        }

        result = await _client._request("POST", "images/generations", json_data=payload)

        if result.get("data") and len(result["data"]) > 0:
            image_data = result["data"][0]
            logger.info(
                "Image generated",
                prompt=prompt[:50],
                style=estilo,
            )
            return {
                "url": image_data.get("url"),
                "revised_prompt": image_data.get("revised_prompt"),
            }

        return None

    except Exception as e:
        logger.error("Failed to generate image", error=str(e))
        return None


async def gerar_variantes(
    imagem_url: str,
    quantidade: int = 3,
    estilo: str | None = None,
) -> list[str]:
    """
    Generate variations of an existing image.

    Args:
        imagem_url: URL of the base image
        quantidade: Number of variants to generate (max 4)
        estilo: Optional style to apply to variants

    Returns:
        List of URLs for generated variants
    """
    try:
        quantidade = min(quantidade, 4)

        payload = {
            "image": imagem_url,
            "n": quantidade,
        }

        if estilo:
            payload["style"] = estilo

        result = await _client._request("POST", "images/variations", json_data=payload)

        urls = []
        for item in result.get("data", []):
            if item.get("url"):
                urls.append(item["url"])

        logger.info(
            "Variants generated",
            base_image=imagem_url[:50],
            count=len(urls),
        )

        return urls

    except Exception as e:
        logger.error("Failed to generate variants", error=str(e))
        return []


# Aliases for backwards compatibility with designer agent
async def gerar_imagem_nanobanana(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str | None = None,
) -> dict[str, Any] | None:
    """Generate image using NanoBanana API (alias for gerar_imagem)."""
    tamanho = f"{width}x{height}"
    return await gerar_imagem(prompt=prompt, tamanho=tamanho)


async def gerar_variacao_nanobanana(
    image_url: str,
    variation_type: str = "cor",
) -> dict[str, Any] | None:
    """Generate image variation (alias for gerar_variantes)."""
    urls = await gerar_variantes(imagem_url=image_url, quantidade=1, estilo=variation_type)
    if urls:
        return {"url": urls[0]}
    return None


async def editar_imagem(
    imagem_url: str,
    prompt: str,
    mascara_url: str | None = None,
) -> dict[str, Any] | None:
    """
    Edit an image based on a text prompt.

    Args:
        imagem_url: URL of the image to edit
        prompt: Description of the desired edit
        mascara_url: Optional mask image URL for localized edits

    Returns:
        Edited image data with URL, or None if failed
    """
    try:
        payload = {
            "image": imagem_url,
            "prompt": prompt,
        }

        if mascara_url:
            payload["mask"] = mascara_url

        result = await _client._request("POST", "images/edits", json_data=payload)

        if result.get("data") and len(result["data"]) > 0:
            image_data = result["data"][0]
            logger.info("Image edited", prompt=prompt[:50])
            return {
                "url": image_data.get("url"),
                "revised_prompt": image_data.get("revised_prompt"),
            }

        return None

    except Exception as e:
        logger.error("Failed to edit image", error=str(e))
        return None
