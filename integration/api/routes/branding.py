"""
Branding API Routes

Endpoints para customização de temas white-label dinâmicos.
"""

from typing import Optional

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from services.branding import branding_service, get_default_branding, BrandingConfig


router = APIRouter()


@router.get(
    "/branding/theme.css",
    response_class=PlainTextResponse,
    summary="Get Industrial theme CSS",
    description="Returns the default Industrial design system CSS",
)
async def get_default_theme():
    """
    Retorna CSS do tema Industrial padrão.

    Use este endpoint para obter o CSS base que pode ser aplicado
    aos white-labels (Twenty, Cal.com, Chatwoot).
    """
    css = await branding_service.get_theme_css()

    return Response(
        content=css,
        media_type="text/css",
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Theme": "industrial",
        },
    )


@router.get(
    "/branding/{agency_id}/theme.css",
    response_class=PlainTextResponse,
    summary="Get agency-specific theme CSS",
    description="Returns customized CSS based on agency branding settings",
)
async def get_agency_theme(agency_id: str):
    """
    Retorna CSS customizado para uma agency específica.

    O CSS é gerado dinamicamente baseado nas configurações de branding
    da agency (cores, fontes, logo, etc.).

    Args:
        agency_id: ID da agency
    """
    css = await branding_service.get_theme_css(agency_id)

    return Response(
        content=css,
        media_type="text/css",
        headers={
            "Cache-Control": "public, max-age=300",
            "X-Theme": "industrial",
            "X-Agency": agency_id,
        },
    )


@router.get(
    "/branding/config",
    response_model=BrandingConfig,
    summary="Get default branding config",
    description="Returns the default branding configuration object",
)
async def get_branding_config():
    """
    Retorna configuração de branding padrão.

    Útil para o frontend saber quais valores padrão usar.
    """
    return get_default_branding()


@router.get(
    "/branding/{agency_id}/config",
    response_model=BrandingConfig,
    summary="Get agency branding config",
    description="Returns branding configuration for specific agency",
)
async def get_agency_branding_config(agency_id: str):
    """
    Retorna configuração de branding de uma agency específica.

    Args:
        agency_id: ID da agency
    """
    branding = await branding_service.get_agency_branding(agency_id)
    return branding


@router.get(
    "/branding/fonts",
    summary="Get font imports HTML",
    description="Returns HTML link tags for Google Fonts",
)
async def get_font_imports(agency_id: Optional[str] = None):
    """
    Retorna HTML para importar as fontes do Google Fonts.

    Útil para adicionar ao <head> do documento.
    """
    if agency_id:
        branding = await branding_service.get_agency_branding(agency_id)
    else:
        branding = get_default_branding()

    fonts_html = branding_service.generate_font_imports(branding)

    return {"html": fonts_html}


@router.get(
    "/branding/tokens",
    summary="Get design tokens as JSON",
    description="Returns design tokens in JSON format for use in JS/TS",
)
async def get_design_tokens(agency_id: Optional[str] = None):
    """
    Retorna tokens de design em formato JSON.

    Útil para aplicações JavaScript/TypeScript que precisam
    dos valores em runtime.
    """
    if agency_id:
        branding = await branding_service.get_agency_branding(agency_id)
    else:
        branding = get_default_branding()

    return {
        "colors": {
            "paper": branding.colors.background,
            "ink": branding.colors.text,
            "graphite": branding.colors.border,
            "accentOrange": branding.colors.primary,
            "accentBlue": branding.colors.secondary,
            "steel": branding.colors.muted,
        },
        "fonts": {
            "display": branding.fonts.display,
            "mono": branding.fonts.mono,
            "body": branding.fonts.body,
        },
        "shadows": {
            "hard": f"4px 4px 0px 0px {branding.colors.border}",
            "hardSm": f"2px 2px 0px 0px {branding.colors.border}",
            "hardPrimary": f"4px 4px 0px 0px {branding.colors.primary}",
        },
        "borders": {
            "width": "2px",
            "radius": "0px",
            "color": branding.colors.border,
        },
    }
