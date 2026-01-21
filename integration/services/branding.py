"""
Branding Service - Dynamic White-label Theme Generation

Este serviço gera CSS dinâmico baseado nas configurações de branding de cada agency,
permitindo personalização visual por tenant.
"""

from typing import Optional
from pydantic import BaseModel

from core.config import get_settings


class BrandingColors(BaseModel):
    """Esquema de cores para branding"""
    primary: str = "#F24E1E"
    secondary: str = "#0047AB"
    background: str = "#F2F0E9"
    text: str = "#111111"
    border: str = "#000000"
    muted: str = "#666666"


class BrandingFonts(BaseModel):
    """Fontes para branding"""
    display: str = "Inter Tight"
    mono: str = "JetBrains Mono"
    body: str = "Inter"


class BrandingConfig(BaseModel):
    """Configuração completa de branding"""
    name: str = "MedFlow"
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    colors: BrandingColors = BrandingColors()
    fonts: BrandingFonts = BrandingFonts()
    custom_css: Optional[str] = None


# Default Industrial theme
DEFAULT_BRANDING = BrandingConfig()


class BrandingService:
    """Serviço de geração de temas dinâmicos"""

    def __init__(self):
        self.settings = get_settings()

    async def get_agency_branding(self, agency_id: str) -> BrandingConfig:
        """
        Busca configuração de branding da agency.

        Em produção, isso buscaria do banco de dados.
        """
        # TODO: Implementar busca real do banco
        # Por enquanto, retorna o tema Industrial padrão
        return DEFAULT_BRANDING

    def generate_css_variables(self, branding: BrandingConfig) -> str:
        """Gera CSS custom properties baseado no branding"""
        return f"""
/* MedFlow Dynamic Branding - Generated */
:root {{
  /* Cores */
  --color-paper: {branding.colors.background};
  --color-ink: {branding.colors.text};
  --color-graphite: {branding.colors.border};
  --color-accent-orange: {branding.colors.primary};
  --color-accent-blue: {branding.colors.secondary};
  --color-steel: {branding.colors.muted};
  --color-white: #FFFFFF;

  /* Tipografia */
  --font-display: "{branding.fonts.display}", "Inter", system-ui, sans-serif;
  --font-mono: "{branding.fonts.mono}", "Fira Code", monospace;
  --font-body: "{branding.fonts.body}", system-ui, sans-serif;

  /* Sombras - Hard shadows com cor primária */
  --shadow-hard: 4px 4px 0px 0px {branding.colors.border};
  --shadow-hard-sm: 2px 2px 0px 0px {branding.colors.border};
  --shadow-hard-primary: 4px 4px 0px 0px {branding.colors.primary};

  /* Bordas */
  --border-width: 2px;
  --border-color: {branding.colors.border};
  --border-radius: 0px;

  /* Branding específico */
  --brand-name: "{branding.name}";
}}
"""

    def generate_base_styles(self, branding: BrandingConfig) -> str:
        """Gera estilos base Industrial"""
        return f"""
/* Reset border-radius global */
*, *::before, *::after {{
  border-radius: 0 !important;
}}

/* Body */
body {{
  background-color: var(--color-paper) !important;
  font-family: var(--font-body) !important;
  color: var(--color-ink) !important;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em !important;
  text-transform: uppercase !important;
}}

code, pre, .mono {{
  font-family: var(--font-mono) !important;
}}

/* Buttons */
button, [role="button"], .button {{
  background-color: var(--color-ink) !important;
  color: var(--color-white) !important;
  border: var(--border-width) solid var(--border-color) !important;
  box-shadow: var(--shadow-hard) !important;
  font-family: var(--font-display) !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}}

button:hover, [role="button"]:hover {{
  transform: translate(-2px, -2px) !important;
  box-shadow: 6px 6px 0px 0px var(--border-color) !important;
}}

button:active {{
  transform: translate(2px, 2px) !important;
  box-shadow: 2px 2px 0px 0px var(--border-color) !important;
}}

/* Primary button */
button.primary, [class*="primary"] {{
  background-color: var(--color-accent-orange) !important;
  box-shadow: var(--shadow-hard-primary) !important;
}}

/* Inputs */
input, textarea, select {{
  background-color: var(--color-white) !important;
  border: var(--border-width) solid var(--border-color) !important;
  font-family: var(--font-body) !important;
  padding: 0.75rem 1rem !important;
}}

input:focus, textarea:focus, select:focus {{
  outline: none !important;
  box-shadow: var(--shadow-hard-sm) !important;
}}

/* Cards */
.card, [class*="card"] {{
  background-color: var(--color-white) !important;
  border: var(--border-width) solid var(--border-color) !important;
  box-shadow: var(--shadow-hard) !important;
}}

/* Badges */
.badge, [class*="badge"] {{
  font-family: var(--font-mono) !important;
  font-size: 0.625rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
  border: 1px solid var(--border-color) !important;
}}

/* Tables */
table th {{
  background-color: var(--color-ink) !important;
  color: var(--color-white) !important;
  font-family: var(--font-mono) !important;
  text-transform: uppercase !important;
}}

table td {{
  border: 1px solid var(--border-color) !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{
  width: 12px;
  height: 12px;
}}

::-webkit-scrollbar-track {{
  background-color: var(--color-paper);
}}

::-webkit-scrollbar-thumb {{
  background-color: var(--border-color);
  border: 2px solid var(--color-paper);
}}
"""

    def generate_full_theme(self, branding: BrandingConfig) -> str:
        """Gera tema completo (variables + base styles + custom)"""
        parts = [
            "/* ===== MedFlow Industrial Theme ===== */",
            self.generate_css_variables(branding),
            self.generate_base_styles(branding),
        ]

        if branding.custom_css:
            parts.append(f"\n/* Custom CSS */\n{branding.custom_css}")

        return "\n".join(parts)

    async def get_theme_css(self, agency_id: Optional[str] = None) -> str:
        """
        Retorna CSS completo para a agency.

        Se agency_id for None, retorna o tema Industrial padrão.
        """
        if agency_id:
            branding = await self.get_agency_branding(agency_id)
        else:
            branding = DEFAULT_BRANDING

        return self.generate_full_theme(branding)

    def generate_font_imports(self, branding: BrandingConfig) -> str:
        """Gera imports de fontes do Google Fonts"""
        fonts = []

        if "Inter Tight" in branding.fonts.display:
            fonts.append("Inter+Tight:wght@400;500;600;700")

        if "Inter" in branding.fonts.body:
            fonts.append("Inter:wght@400;500;600")

        if "JetBrains Mono" in branding.fonts.mono:
            fonts.append("JetBrains+Mono:wght@400;500")

        if not fonts:
            return ""

        font_string = "&family=".join(fonts)
        return f'<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family={font_string}&display=swap" rel="stylesheet">'


# Singleton instance
branding_service = BrandingService()


async def get_branding_css(agency_id: Optional[str] = None) -> str:
    """Helper function para obter CSS de branding"""
    return await branding_service.get_theme_css(agency_id)


def get_default_branding() -> BrandingConfig:
    """Retorna configuração de branding padrão"""
    return DEFAULT_BRANDING
