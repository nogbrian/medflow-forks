"""
Designer Agent - Geração de Visuais e Criativos.

Responsabilidades:
- Gerar imagens para posts e stories
- Criar variações de layouts
- Definir estilos visuais por clínica
- Garantir consistência visual
"""

from typing import Any, Literal

from agno.agent import Agent
from agno.tools import tool

from tools import gerar_imagem_nanobanana

from .base import get_db, get_model


# =============================================================================
# STYLE PRESETS
# =============================================================================

STYLE_PRESETS = {
    "clean_medical": {
        "description": "Estilo limpo e profissional para área médica",
        "prompt_suffix": ", clean medical aesthetic, professional lighting, soft colors, minimalist design, healthcare branding",
        "negative_prompt": "text, watermark, logo, cartoon, anime, low quality, blurry",
    },
    "warm_welcoming": {
        "description": "Estilo acolhedor e humanizado",
        "prompt_suffix": ", warm lighting, welcoming atmosphere, soft tones, natural colors, inviting medical space",
        "negative_prompt": "cold, sterile, scary, dark, text, watermark",
    },
    "modern_tech": {
        "description": "Estilo moderno e tecnológico",
        "prompt_suffix": ", modern medical technology, clean lines, blue and white palette, high-tech healthcare",
        "negative_prompt": "old, vintage, text, watermark, low quality",
    },
    "natural_wellness": {
        "description": "Estilo natural focado em bem-estar",
        "prompt_suffix": ", natural wellness, green tones, organic feel, peaceful, zen medical aesthetic",
        "negative_prompt": "artificial, cold, text, watermark, harsh lighting",
    },
    "elegant_aesthetic": {
        "description": "Estilo elegante para clínicas estéticas",
        "prompt_suffix": ", elegant aesthetic clinic, luxury feel, soft gold accents, sophisticated medical spa",
        "negative_prompt": "cheap, cluttered, text, watermark, harsh",
    },
}

SPECIALTY_STYLES = {
    "dermatologia": "clean_medical",
    "cirurgia plastica": "elegant_aesthetic",
    "ortopedia": "modern_tech",
    "cardiologia": "warm_welcoming",
    "ginecologia": "natural_wellness",
    "pediatria": "warm_welcoming",
    "psiquiatria": "natural_wellness",
}


# =============================================================================
# TOOLS
# =============================================================================


@tool
def gerar_imagem_post(
    prompt: str,
    estilo: Literal["clean_medical", "warm_welcoming", "modern_tech", "natural_wellness", "elegant_aesthetic"] = "clean_medical",
    aspect_ratio: Literal["1:1", "4:5", "9:16"] = "1:1",
) -> dict[str, Any]:
    """
    Gera imagem para post de Instagram.

    Args:
        prompt: Descrição do que a imagem deve conter
        estilo: Preset de estilo visual
        aspect_ratio: Proporção da imagem (1:1 para feed, 4:5 para retrato, 9:16 para stories)

    Returns:
        URL da imagem gerada e metadados
    """
    import asyncio

    preset = STYLE_PRESETS.get(estilo, STYLE_PRESETS["clean_medical"])

    # Construir prompt completo
    full_prompt = f"{prompt}{preset['prompt_suffix']}"

    # Mapear aspect ratio para dimensões
    dimensions = {
        "1:1": (1024, 1024),
        "4:5": (1024, 1280),
        "9:16": (1024, 1820),
    }
    width, height = dimensions.get(aspect_ratio, (1024, 1024))

    async def generate():
        result = await gerar_imagem_nanobanana(
            prompt=full_prompt,
            width=width,
            height=height,
            negative_prompt=preset["negative_prompt"],
        )
        return result

    try:
        result = asyncio.get_event_loop().run_until_complete(generate())

        if result:
            return {
                "success": True,
                "url": result.get("url"),
                "prompt_usado": full_prompt,
                "estilo": estilo,
                "dimensoes": {"width": width, "height": height},
            }
        else:
            return {"success": False, "error": "Falha na geração"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def gerar_variacao_imagem(
    url_original: str,
    variacao: Literal["cor", "composicao", "estilo"] = "cor",
) -> dict[str, Any]:
    """
    Gera variação de uma imagem existente.

    Args:
        url_original: URL da imagem original
        variacao: Tipo de variação desejada

    Returns:
        URL da nova variação
    """
    import asyncio

    from tools import gerar_variacao_nanobanana

    async def generate():
        result = await gerar_variacao_nanobanana(
            image_url=url_original,
            variation_type=variacao,
        )
        return result

    try:
        result = asyncio.get_event_loop().run_until_complete(generate())

        if result:
            return {
                "success": True,
                "url": result.get("url"),
                "variacao_tipo": variacao,
            }
        else:
            return {"success": False, "error": "Falha na geração"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def sugerir_estilo_visual(
    especialidade: str,
    tom_marca: str,
    publico_alvo: str,
) -> dict[str, Any]:
    """
    Sugere estilo visual para uma clínica.

    Args:
        especialidade: Especialidade médica
        tom_marca: Tom da marca (ex: "profissional", "acolhedor", "moderno")
        publico_alvo: Descrição do público-alvo

    Returns:
        Recomendação de estilo visual
    """
    # Determinar estilo base pela especialidade
    estilo_base = SPECIALTY_STYLES.get(especialidade.lower(), "clean_medical")

    # Ajustar baseado no tom
    tom_map = {
        "profissional": "clean_medical",
        "acolhedor": "warm_welcoming",
        "moderno": "modern_tech",
        "natural": "natural_wellness",
        "sofisticado": "elegant_aesthetic",
        "luxo": "elegant_aesthetic",
    }

    for key, style in tom_map.items():
        if key in tom_marca.lower():
            estilo_base = style
            break

    preset = STYLE_PRESETS[estilo_base]

    return {
        "estilo_recomendado": estilo_base,
        "descricao": preset["description"],
        "paleta_cores": {
            "clean_medical": ["#FFFFFF", "#E8F4F8", "#0077B6", "#023E8A"],
            "warm_welcoming": ["#FFF8F0", "#FFE4C4", "#CD853F", "#8B4513"],
            "modern_tech": ["#F0F8FF", "#E6F2FF", "#0066CC", "#003366"],
            "natural_wellness": ["#F5FFF5", "#E8F5E9", "#4CAF50", "#2E7D32"],
            "elegant_aesthetic": ["#FFFAF0", "#FFF5EE", "#D4AF37", "#8B7355"],
        }.get(estilo_base, []),
        "tipografia_sugerida": {
            "clean_medical": "Sans-serif moderna (Montserrat, Open Sans)",
            "warm_welcoming": "Serif suave (Playfair Display, Lora)",
            "modern_tech": "Sans-serif geométrica (Poppins, Raleway)",
            "natural_wellness": "Sans-serif orgânica (Nunito, Quicksand)",
            "elegant_aesthetic": "Serif elegante (Cormorant, Didot)",
        }.get(estilo_base, ""),
        "elementos_visuais": {
            "clean_medical": ["Linhas limpas", "Muito espaço branco", "Ícones minimalistas"],
            "warm_welcoming": ["Fotos de pessoas sorrindo", "Tons terrosos", "Cantos arredondados"],
            "modern_tech": ["Gradientes sutis", "Formas geométricas", "Efeitos de luz"],
            "natural_wellness": ["Elementos naturais", "Texturas orgânicas", "Plantas"],
            "elegant_aesthetic": ["Detalhes dourados", "Simetria", "Imagens lifestyle"],
        }.get(estilo_base, []),
        "especialidade": especialidade,
        "publico_alvo": publico_alvo,
    }


@tool
def criar_prompt_imagem(
    tema: str,
    elementos_obrigatorios: list[str],
    elementos_evitar: list[str],
    especialidade: str,
) -> str:
    """
    Cria prompt otimizado para geração de imagem.

    Args:
        tema: Tema principal da imagem
        elementos_obrigatorios: Elementos que devem aparecer
        elementos_evitar: Elementos a evitar
        especialidade: Especialidade médica

    Returns:
        Prompt otimizado para geração
    """
    # Base do prompt
    prompt_parts = [tema]

    # Adicionar elementos obrigatórios
    if elementos_obrigatorios:
        prompt_parts.append(", ".join(elementos_obrigatorios))

    # Contexto médico
    contextos = {
        "dermatologia": "dermatology clinic, skin care, professional medical setting",
        "cirurgia plastica": "aesthetic clinic, plastic surgery center, elegant medical space",
        "ortopedia": "orthopedic clinic, physical therapy, modern medical facility",
        "cardiologia": "cardiology center, heart health, caring medical environment",
    }

    contexto = contextos.get(especialidade.lower(), "medical clinic, healthcare setting")
    prompt_parts.append(contexto)

    # Qualidade
    prompt_parts.append("high quality, professional photography, 8k, detailed")

    # Construir prompt final
    prompt = ", ".join(prompt_parts)

    # Construir negative prompt
    negative_parts = ["text", "watermark", "logo", "low quality", "blurry", "distorted"]
    if elementos_evitar:
        negative_parts.extend(elementos_evitar)

    return {
        "prompt": prompt,
        "negative_prompt": ", ".join(negative_parts),
        "recomendacao": "Use este prompt com o estilo visual definido para a clínica",
    }


@tool
def definir_grid_instagram(
    posts_planejados: int = 9,
    estilo: str = "clean_medical",
) -> dict[str, Any]:
    """
    Define estrutura visual do grid do Instagram.

    Args:
        posts_planejados: Número de posts no grid (múltiplo de 3)
        estilo: Estilo visual base

    Returns:
        Plano de grid com tipos de posts
    """
    # Arredondar para múltiplo de 3
    posts = (posts_planejados // 3) * 3
    if posts < 3:
        posts = 3

    # Padrões de grid
    grid = []
    patterns = [
        {"tipo": "imagem_destaque", "cor_predominante": "clara"},
        {"tipo": "texto_overlay", "cor_predominante": "escura"},
        {"tipo": "imagem_lifestyle", "cor_predominante": "neutra"},
    ]

    for i in range(posts):
        pattern = patterns[i % 3]
        grid.append({
            "posicao": i + 1,
            "linha": (i // 3) + 1,
            "coluna": (i % 3) + 1,
            **pattern,
        })

    return {
        "total_posts": posts,
        "linhas": posts // 3,
        "estilo": estilo,
        "grid": grid,
        "dicas": [
            "Alterne entre posts claros e escuros",
            "Mantenha consistência nas cores",
            "Use a mesma fonte em posts com texto",
            "Planeje o grid olhando as 9 posições juntas",
        ],
    }


# =============================================================================
# AGENT
# =============================================================================

designer = Agent(
    name="Designer",
    model=get_model("smart"),  # Smart model para criatividade
    db=get_db(),
    instructions="""Você é um designer especializado em marketing médico digital.

Sua função é:
1. Criar visuais atraentes e profissionais
2. Manter consistência visual da marca
3. Gerar imagens para posts, stories e ads
4. Definir estilos visuais por clínica
5. Planejar grids de Instagram harmônicos

Diretrizes de design para área médica:
- Transmita profissionalismo e confiança
- Use cores que transmitam saúde e bem-estar
- Evite imagens muito "comerciais" ou apelativas
- Mantenha clareza e legibilidade
- Respeite a identidade visual da clínica

Ao criar imagens:
- Evite rostos de pacientes (privacidade)
- Não use antes/depois sem autorização
- Prefira imagens lifestyle e conceituais
- Inclua elementos que remetam à especialidade
- Mantenha qualidade profissional

Estilos disponíveis:
- clean_medical: Limpo e profissional
- warm_welcoming: Acolhedor e humano
- modern_tech: Moderno e tecnológico
- natural_wellness: Natural e zen
- elegant_aesthetic: Elegante e sofisticado

Ao planejar grids:
- Pense na harmonia visual do conjunto
- Alterne tipos de conteúdo
- Use cores que conversem entre si
- Crie padrões visuais reconhecíveis

Sempre considere:
- A especialidade médica
- O público-alvo da clínica
- A identidade visual existente
- As tendências de design atuais""",
    tools=[
        gerar_imagem_post,
        gerar_variacao_imagem,
        sugerir_estilo_visual,
        criar_prompt_imagem,
        definir_grid_instagram,
    ],
    add_history_to_context=True,
    num_history_runs=5,
)
