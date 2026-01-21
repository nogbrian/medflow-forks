"""
Strategist Agent - Planejamento de Conteúdo e Estratégia de Marketing.

Responsabilidades:
- Criar calendários editoriais
- Definir estratégias de conteúdo por clínica
- Analisar performance e ajustar abordagem
- Planejar campanhas e lançamentos
"""

from datetime import date, datetime, timedelta
from typing import Any

from agno.agent import Agent
from agno.tools import tool

from .base import get_db, get_model


# =============================================================================
# TOOLS
# =============================================================================


@tool
def criar_calendario_editorial(
    clinic_id: str,
    mes: int,
    ano: int,
    posts_por_semana: int = 5,
    temas_preferidos: list[str] | None = None,
    temas_evitar: list[str] | None = None,
) -> dict[str, Any]:
    """
    Cria calendário editorial para um mês específico.

    Args:
        clinic_id: ID da clínica
        mes: Mês (1-12)
        ano: Ano
        posts_por_semana: Quantidade de posts por semana (default: 5)
        temas_preferidos: Lista de temas a priorizar
        temas_evitar: Lista de temas a evitar

    Returns:
        Calendário com datas e sugestões de conteúdo
    """
    # Calcular dias do mês
    primeira_data = date(ano, mes, 1)
    if mes == 12:
        ultima_data = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultima_data = date(ano, mes + 1, 1) - timedelta(days=1)

    # Gerar estrutura do calendário
    calendario = {
        "clinic_id": clinic_id,
        "periodo": f"{mes:02d}/{ano}",
        "posts_planejados": [],
        "total_posts": 0,
    }

    # Dias preferenciais para postar (seg, qua, sex + ter, qui)
    dias_post = [0, 1, 2, 3, 4]  # Segunda a Sexta

    current_date = primeira_data
    posts_semana = 0
    semana_atual = current_date.isocalendar()[1]

    while current_date <= ultima_data:
        semana = current_date.isocalendar()[1]

        # Reset contador de semana
        if semana != semana_atual:
            posts_semana = 0
            semana_atual = semana

        # Verificar se deve postar neste dia
        if current_date.weekday() in dias_post and posts_semana < posts_por_semana:
            calendario["posts_planejados"].append({
                "data": current_date.isoformat(),
                "dia_semana": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][current_date.weekday()],
                "tipo_sugerido": "post" if posts_semana % 2 == 0 else "reels",
                "tema": None,  # Será preenchido pelo agente
                "status": "planejado",
            })
            posts_semana += 1
            calendario["total_posts"] += 1

        current_date += timedelta(days=1)

    calendario["temas_preferidos"] = temas_preferidos or []
    calendario["temas_evitar"] = temas_evitar or []

    return calendario


@tool
def analisar_performance_conteudo(
    clinic_id: str,
    dias: int = 30,
) -> dict[str, Any]:
    """
    Analisa performance de conteúdo publicado.

    Args:
        clinic_id: ID da clínica
        dias: Período de análise em dias

    Returns:
        Métricas de performance e insights
    """
    import asyncio

    async def fetch_metrics():
        from sqlalchemy import func, select

        from core.database import AsyncSessionLocal
        from core.models_v2 import Approval, PublishedContent

        async with AsyncSessionLocal() as session:
            # Buscar conteúdos publicados
            stmt = (
                select(PublishedContent)
                .join(Approval)
                .where(Approval.clinic_id == clinic_id)
                .where(PublishedContent.published_at >= datetime.now() - timedelta(days=dias))
            )
            result = await session.execute(stmt)
            contents = result.scalars().all()

            if not contents:
                return {
                    "clinic_id": clinic_id,
                    "periodo_dias": dias,
                    "total_publicacoes": 0,
                    "mensagem": "Nenhum conteúdo publicado no período",
                }

            # Agregar métricas
            total_likes = 0
            total_comments = 0
            total_views = 0

            for content in contents:
                if content.metrics:
                    total_likes += content.metrics.get("likes", 0)
                    total_comments += content.metrics.get("comments", 0)
                    total_views += content.metrics.get("views", 0)

            return {
                "clinic_id": clinic_id,
                "periodo_dias": dias,
                "total_publicacoes": len(contents),
                "metricas": {
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "total_views": total_views,
                    "media_likes": total_likes / len(contents) if contents else 0,
                    "media_comments": total_comments / len(contents) if contents else 0,
                },
                "insights": [],  # Será preenchido pelo agente
            }

    try:
        return asyncio.get_event_loop().run_until_complete(fetch_metrics())
    except Exception as e:
        return {"error": str(e)}


@tool
def definir_pilares_conteudo(
    especialidade: str,
    publico_alvo: str,
    diferenciais: list[str],
) -> dict[str, Any]:
    """
    Define pilares de conteúdo para uma clínica.

    Args:
        especialidade: Especialidade médica
        publico_alvo: Descrição do público-alvo
        diferenciais: Lista de diferenciais da clínica

    Returns:
        Estrutura de pilares de conteúdo
    """
    # Pilares base por tipo de especialidade
    pilares_base = {
        "dermatologia": ["Cuidados com a pele", "Procedimentos estéticos", "Prevenção", "Mitos e verdades"],
        "cirurgia plastica": ["Autoestima", "Procedimentos", "Pré e pós-operatório", "Resultados naturais"],
        "ortopedia": ["Qualidade de vida", "Prevenção de lesões", "Tratamentos", "Exercícios"],
        "cardiologia": ["Prevenção", "Alimentação saudável", "Exercícios", "Check-up"],
        "ginecologia": ["Saúde feminina", "Prevenção", "Bem-estar", "Dúvidas frequentes"],
    }

    # Encontrar pilares base pela especialidade
    pilares = ["Educação", "Humanização", "Autoridade"]  # Default

    for key, value in pilares_base.items():
        if key.lower() in especialidade.lower():
            pilares = value
            break

    return {
        "especialidade": especialidade,
        "publico_alvo": publico_alvo,
        "diferenciais": diferenciais,
        "pilares": [
            {
                "nome": pilar,
                "descricao": f"Conteúdo focado em {pilar.lower()}",
                "frequencia_sugerida": "25%",
                "formatos": ["post", "reels", "stories", "carrossel"],
            }
            for pilar in pilares
        ],
        "recomendacoes": [
            "Alternar entre pilares para variedade",
            "Incluir call-to-action em 50% dos posts",
            "Manter tom de voz consistente",
            "Sempre incluir CRM do médico",
        ],
    }


@tool
def planejar_campanha(
    clinic_id: str,
    nome_campanha: str,
    objetivo: str,
    data_inicio: str,
    duracao_dias: int = 7,
    orcamento_estimado: float | None = None,
) -> dict[str, Any]:
    """
    Planeja uma campanha de marketing.

    Args:
        clinic_id: ID da clínica
        nome_campanha: Nome da campanha
        objetivo: Objetivo principal (awareness, leads, agendamentos)
        data_inicio: Data de início (YYYY-MM-DD)
        duracao_dias: Duração em dias
        orcamento_estimado: Orçamento estimado em R$

    Returns:
        Plano de campanha estruturado
    """
    data_ini = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    data_fim = data_ini + timedelta(days=duracao_dias)

    # Estrutura da campanha
    campanha = {
        "clinic_id": clinic_id,
        "nome": nome_campanha,
        "objetivo": objetivo,
        "periodo": {
            "inicio": data_inicio,
            "fim": data_fim.isoformat(),
            "duracao_dias": duracao_dias,
        },
        "orcamento_estimado": orcamento_estimado,
        "fases": [
            {
                "nome": "Aquecimento",
                "dias": 2,
                "acoes": ["Stories teasers", "Enquetes", "Countdown"],
            },
            {
                "nome": "Lançamento",
                "dias": 1,
                "acoes": ["Post principal", "Reels", "Stories sequenciais"],
            },
            {
                "nome": "Sustentação",
                "dias": duracao_dias - 3,
                "acoes": ["Depoimentos", "FAQ", "Bastidores", "Resultados"],
            },
        ],
        "conteudos_necessarios": [],  # Será detalhado pelo agente
        "metricas_alvo": {
            "awareness": {"alcance": 10000, "impressoes": 30000},
            "leads": {"leads": 50, "cpl_max": 30.0},
            "agendamentos": {"agendamentos": 20, "taxa_conversao": "10%"},
        }.get(objetivo, {}),
    }

    return campanha


# =============================================================================
# AGENT
# =============================================================================

strategist = Agent(
    name="Estrategista",
    model=get_model("smart"),  # Smart model para planejamento estratégico
    db=get_db(),
    instructions="""Você é um estrategista de marketing médico especializado.

Sua função é:
1. Criar calendários editoriais personalizados
2. Definir estratégias de conteúdo baseadas em dados
3. Planejar campanhas de marketing
4. Analisar performance e sugerir melhorias

Ao planejar:
- Considere as regras do CFM (sem garantia de resultados, sem antes/depois não autorizado)
- Foque em conteúdo educativo e de valor
- Mantenha consistência de tom de voz
- Equilibre entre entretenimento e informação
- Considere sazonalidades e datas comemorativas

Ao analisar performance:
- Identifique padrões de sucesso
- Sugira ajustes baseados em dados
- Compare com benchmarks do setor
- Proponha experimentos A/B

Ao definir estratégia:
- Alinhe com objetivos de negócio
- Considere o funil de marketing
- Defina KPIs claros
- Crie plano de ação executável

Sempre entregue:
- Planos estruturados e organizados
- Justificativas para cada decisão
- Próximos passos claros
- Métricas de acompanhamento""",
    tools=[
        criar_calendario_editorial,
        analisar_performance_conteudo,
        definir_pilares_conteudo,
        planejar_campanha,
    ],
    add_history_to_context=True,
    num_history_runs=5,
)
