"""Gestor de Tráfego - Traffic Manager agent for Meta and Google Ads.

Specializes in paid traffic management for medical clinics:
- Campaign creation and optimization (TOF/MOF/BOF)
- Budget allocation and bid strategies
- Audience management and lookalikes
- Performance reporting and recommendations
"""

from __future__ import annotations

from typing import Any

from agents.base import create_agent, get_model
from core.logging import get_logger
from core.tools.registry import ToolRegistry

logger = get_logger(__name__)

# Tool registry for traffic management
traffic_registry = ToolRegistry()

GESTOR_TRAFEGO_PROMPT = """Você é o Gestor de Tráfego do MedFlow, especialista em tráfego pago para clínicas médicas brasileiras.

## Sua Expertise
- Meta Ads (Facebook/Instagram): Campanhas de alcance, tráfego, leads e conversões
- Google Ads (Search/Display): Campanhas de busca, display e remarketing
- Estratégia de funil: TOF (Topo), MOF (Meio), BOF (Fundo)
- Otimização baseada em dados: CPA, ROAS, CTR, CPM

## Regras de Compliance (CFM)
- NUNCA promover garantia de resultados médicos
- NUNCA usar antes/depois sem autorização documentada
- NUNCA divulgar preços de procedimentos em anúncios públicos
- Usar linguagem educativa e informativa
- Respeitar a ética médica em toda comunicação paga

## Estrutura de Funil
- **TOF (Awareness)**: Alcance, vídeos educativos, brand awareness
- **MOF (Consideration)**: Tráfego para conteúdo, engajamento, vídeo views
- **BOF (Conversion)**: Lead generation, agendamentos, remarketing

## Alocação Recomendada
- Clínicas novas: TOF 50% / MOF 30% / BOF 20%
- Clínicas estabelecidas: TOF 20% / MOF 30% / BOF 50%
- Lançamento de procedimento: TOF 40% / MOF 40% / BOF 20%

## Ao Criar Campanhas
1. Pergunte o objetivo e orçamento
2. Sugira estrutura de funil adequada
3. Defina públicos (geolocalização, idade, interesses médicos)
4. Crie segmentação por procedimento/especialidade
5. Configure pixels e eventos de conversão
6. Defina métricas de sucesso (CPA alvo, ROAS mínimo)

## Ao Otimizar
1. Analise métricas dos últimos 7 dias
2. Identifique campanhas abaixo do CPA alvo
3. Sugira ajustes de lance, público ou criativo
4. Recomende realocação de orçamento para melhor performance
5. Alerte sobre campanhas com gasto sem conversões

Responda sempre em português brasileiro. Seja analítico e orientado a dados.
"""


@traffic_registry.register(
    category="ads",
    description="Criar campanha de anúncios no Meta (Facebook/Instagram)",
    parameters={
        "type": "object",
        "properties": {
            "nome": {"type": "string", "description": "Nome da campanha"},
            "objetivo": {
                "type": "string",
                "enum": ["REACH", "TRAFFIC", "LEAD_GENERATION", "CONVERSIONS"],
                "description": "Objetivo da campanha",
            },
            "orcamento_diario_brl": {"type": "number", "description": "Orçamento diário em BRL"},
            "plataforma": {
                "type": "string",
                "enum": ["meta", "google"],
                "description": "Plataforma de anúncios",
            },
        },
        "required": ["nome", "objetivo", "orcamento_diario_brl", "plataforma"],
    },
)
async def criar_campanha(
    nome: str,
    objetivo: str,
    orcamento_diario_brl: float,
    plataforma: str = "meta",
) -> dict[str, Any]:
    """Criar uma nova campanha de anúncios."""
    if plataforma == "meta":
        from tools.ads.meta import MetaAdsClient
        client = MetaAdsClient()
        try:
            result = await client.criar_campanha(
                nome=nome,
                objetivo=objetivo,
                orcamento_diario_centavos=int(orcamento_diario_brl * 100),
            )
            return {"success": True, "platform": "meta", "campaign": result}
        finally:
            await client.close()
    else:
        from tools.ads.google import GoogleAdsClient
        client = GoogleAdsClient()
        try:
            result = await client.criar_campanha(
                nome=nome,
                tipo="SEARCH" if objetivo == "TRAFFIC" else "DISPLAY",
                orcamento_diario_micros=int(orcamento_diario_brl * 1_000_000),
            )
            return {"success": True, "platform": "google", "campaign": result}
        finally:
            await client.close()


@traffic_registry.register(
    category="ads",
    description="Obter métricas de performance de campanhas",
    parameters={
        "type": "object",
        "properties": {
            "campaign_id": {"type": "string", "description": "ID da campanha (opcional, vazio = todas)"},
            "periodo_dias": {"type": "integer", "description": "Período em dias (padrão: 7)"},
            "plataforma": {"type": "string", "enum": ["meta", "google", "todas"], "description": "Plataforma"},
        },
        "required": [],
    },
)
async def obter_metricas(
    campaign_id: str = "",
    periodo_dias: int = 7,
    plataforma: str = "todas",
) -> dict[str, Any]:
    """Obter métricas de performance de campanhas de ads."""
    from tools.ads.analytics import AdsAnalytics
    from tools.ads.meta import MetaAdsClient
    from tools.ads.google import GoogleAdsClient

    meta_client = MetaAdsClient() if plataforma in ("meta", "todas") else None
    google_client = GoogleAdsClient() if plataforma in ("google", "todas") else None

    analytics = AdsAnalytics(meta_client=meta_client, google_client=google_client)

    try:
        report = await analytics.relatorio_periodo(periodo_dias=periodo_dias)
        return {"success": True, "report": report}
    finally:
        if meta_client:
            await meta_client.close()
        if google_client:
            await google_client.close()


@traffic_registry.register(
    category="ads",
    description="Pausar uma campanha de anúncios",
    parameters={
        "type": "object",
        "properties": {
            "campaign_id": {"type": "string", "description": "ID da campanha"},
            "plataforma": {"type": "string", "enum": ["meta", "google"], "description": "Plataforma"},
            "motivo": {"type": "string", "description": "Motivo da pausa"},
        },
        "required": ["campaign_id", "plataforma"],
    },
)
async def pausar_campanha(
    campaign_id: str,
    plataforma: str,
    motivo: str = "",
) -> dict[str, Any]:
    """Pausar uma campanha de anúncios."""
    if plataforma == "meta":
        from tools.ads.meta import MetaAdsClient
        client = MetaAdsClient()
        try:
            result = await client.pausar_campanha(campaign_id)
            return {"success": True, "platform": "meta", "result": result, "motivo": motivo}
        finally:
            await client.close()
    else:
        from tools.ads.google import GoogleAdsClient
        client = GoogleAdsClient()
        try:
            result = await client.pausar_campanha(campaign_id)
            return {"success": True, "platform": "google", "result": result, "motivo": motivo}
        finally:
            await client.close()


@traffic_registry.register(
    category="ads",
    description="Criar público lookalike no Meta Ads",
    parameters={
        "type": "object",
        "properties": {
            "source_audience_id": {"type": "string", "description": "ID do público fonte"},
            "porcentagem": {"type": "number", "description": "Porcentagem do lookalike (1-10)"},
            "nome": {"type": "string", "description": "Nome do público"},
        },
        "required": ["source_audience_id"],
    },
)
async def criar_publico_lookalike(
    source_audience_id: str,
    porcentagem: float = 1.0,
    nome: str = "",
) -> dict[str, Any]:
    """Criar público lookalike baseado em público existente."""
    from tools.ads.meta import MetaAdsClient
    client = MetaAdsClient()
    try:
        result = await client.criar_publico_lookalike(
            source_audience_id=source_audience_id,
            ratio=porcentagem / 100,
            nome=nome,
        )
        return {"success": True, "audience": result}
    finally:
        await client.close()


def create_gestor_trafego(
    user_id: str | None = None,
    session_id: str | None = None,
):
    """Create a configured Gestor de Tráfego agent.

    Returns an Agno Agent configured with traffic management tools
    and the specialized system prompt.
    """
    tools_list = []
    for tool_def in traffic_registry.list_tools():
        tools_list.append(tool_def.handler)

    return create_agent(
        name="gestor-trafego",
        instructions=GESTOR_TRAFEGO_PROMPT,
        tools=tools_list,
        model_type="smart",
        user_id=user_id,
        session_id=session_id,
    )
