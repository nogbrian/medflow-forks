"""
BI Agent - Business Intelligence e Analytics.

Responsabilidades:
- Gerar relatórios de performance
- Analisar métricas de marketing
- Calcular ROI e KPIs
- Identificar tendências e anomalias
- Alertar sobre problemas
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from agno.agent import Agent
from agno.tools import tool

from .base import get_db, get_model


# =============================================================================
# TOOLS
# =============================================================================


@tool
def gerar_relatorio_mensal(
    clinic_id: str,
    mes: int,
    ano: int,
) -> dict[str, Any]:
    """
    Gera relatório mensal completo de uma clínica.

    Args:
        clinic_id: ID da clínica
        mes: Mês do relatório
        ano: Ano do relatório

    Returns:
        Relatório com todas as métricas do período
    """
    import asyncio

    async def fetch_report():
        from sqlalchemy import extract, func, select

        from core.database import AsyncSessionLocal
        from core.models_v2 import (
            AgentExecution,
            Approval,
            Contact,
            Conversation,
            Message,
            Opportunity,
            PublishedContent,
        )

        async with AsyncSessionLocal() as session:
            # Período
            data_inicio = datetime(ano, mes, 1)
            if mes == 12:
                data_fim = datetime(ano + 1, 1, 1)
            else:
                data_fim = datetime(ano, mes + 1, 1)

            # Métricas de Leads
            leads_query = select(func.count(Contact.id)).where(
                Contact.clinic_id == clinic_id,
                Contact.created_at >= data_inicio,
                Contact.created_at < data_fim,
            )
            leads_result = await session.execute(leads_query)
            total_leads = leads_result.scalar() or 0

            # Leads por temperatura
            leads_temp_query = select(
                Contact.temperature, func.count(Contact.id)
            ).where(
                Contact.clinic_id == clinic_id,
                Contact.created_at >= data_inicio,
                Contact.created_at < data_fim,
            ).group_by(Contact.temperature)
            leads_temp_result = await session.execute(leads_temp_query)
            leads_por_temp = {row[0].value: row[1] for row in leads_temp_result.all()}

            # Conversas
            conversas_query = select(func.count(Conversation.id)).where(
                Conversation.clinic_id == clinic_id,
                Conversation.created_at >= data_inicio,
                Conversation.created_at < data_fim,
            )
            conversas_result = await session.execute(conversas_query)
            total_conversas = conversas_result.scalar() or 0

            # Mensagens
            msgs_query = select(func.count(Message.id)).join(Conversation).where(
                Conversation.clinic_id == clinic_id,
                Message.created_at >= data_inicio,
                Message.created_at < data_fim,
            )
            msgs_result = await session.execute(msgs_query)
            total_mensagens = msgs_result.scalar() or 0

            # Conteúdos publicados
            conteudos_query = select(func.count(PublishedContent.id)).join(Approval).where(
                Approval.clinic_id == clinic_id,
                PublishedContent.published_at >= data_inicio,
                PublishedContent.published_at < data_fim,
            )
            conteudos_result = await session.execute(conteudos_query)
            total_conteudos = conteudos_result.scalar() or 0

            # Custos de agentes
            custos_query = select(func.sum(AgentExecution.cost_usd)).where(
                AgentExecution.clinic_id == clinic_id,
                AgentExecution.started_at >= data_inicio,
                AgentExecution.started_at < data_fim,
            )
            custos_result = await session.execute(custos_query)
            custo_total_usd = float(custos_result.scalar() or 0)

            # Execuções de agentes
            execucoes_query = select(func.count(AgentExecution.id)).where(
                AgentExecution.clinic_id == clinic_id,
                AgentExecution.started_at >= data_inicio,
                AgentExecution.started_at < data_fim,
            )
            execucoes_result = await session.execute(execucoes_query)
            total_execucoes = execucoes_result.scalar() or 0

            return {
                "clinic_id": clinic_id,
                "periodo": f"{mes:02d}/{ano}",
                "gerado_em": datetime.now().isoformat(),
                "metricas": {
                    "leads": {
                        "total": total_leads,
                        "por_temperatura": leads_por_temp,
                    },
                    "conversas": {
                        "total": total_conversas,
                        "mensagens": total_mensagens,
                    },
                    "conteudo": {
                        "publicados": total_conteudos,
                    },
                    "agentes": {
                        "execucoes": total_execucoes,
                        "custo_usd": custo_total_usd,
                    },
                },
            }

    try:
        return asyncio.get_event_loop().run_until_complete(fetch_report())
    except Exception as e:
        return {"error": str(e)}


@tool
def calcular_roi_marketing(
    clinic_id: str,
    investimento_ads: float,
    receita_gerada: float,
    periodo_dias: int = 30,
) -> dict[str, Any]:
    """
    Calcula ROI de marketing.

    Args:
        clinic_id: ID da clínica
        investimento_ads: Valor investido em ads (R$)
        receita_gerada: Receita gerada no período (R$)
        periodo_dias: Período de análise

    Returns:
        Análise de ROI com métricas
    """
    import asyncio

    async def fetch_costs():
        from sqlalchemy import func, select

        from core.database import AsyncSessionLocal
        from core.models_v2 import AgentExecution

        async with AsyncSessionLocal() as session:
            # Custo de agentes no período
            custos_query = select(func.sum(AgentExecution.cost_usd)).where(
                AgentExecution.clinic_id == clinic_id,
                AgentExecution.started_at >= datetime.now() - timedelta(days=periodo_dias),
            )
            result = await session.execute(custos_query)
            custo_agentes_usd = float(result.scalar() or 0)

            # Converter para BRL (taxa aproximada)
            custo_agentes_brl = custo_agentes_usd * 5.5

            return custo_agentes_brl

    try:
        custo_agentes = asyncio.get_event_loop().run_until_complete(fetch_costs())
    except Exception:
        custo_agentes = 0

    # Calcular métricas
    investimento_total = investimento_ads + custo_agentes
    lucro = receita_gerada - investimento_total
    roi = ((receita_gerada - investimento_total) / investimento_total * 100) if investimento_total > 0 else 0
    roas = (receita_gerada / investimento_ads) if investimento_ads > 0 else 0

    return {
        "clinic_id": clinic_id,
        "periodo_dias": periodo_dias,
        "investimentos": {
            "ads": investimento_ads,
            "agentes_ia": round(custo_agentes, 2),
            "total": round(investimento_total, 2),
        },
        "receita": receita_gerada,
        "lucro": round(lucro, 2),
        "metricas": {
            "roi_percentual": round(roi, 2),
            "roas": round(roas, 2),
        },
        "analise": "positivo" if roi > 0 else "negativo",
        "recomendacao": (
            "Manter estratégia atual" if roi > 50
            else "Otimizar campanhas" if roi > 0
            else "Revisar estratégia urgente"
        ),
    }


@tool
def analisar_funil_vendas(
    clinic_id: str,
    periodo_dias: int = 30,
) -> dict[str, Any]:
    """
    Analisa o funil de vendas de uma clínica.

    Args:
        clinic_id: ID da clínica
        periodo_dias: Período de análise

    Returns:
        Análise do funil com taxas de conversão
    """
    import asyncio

    async def fetch_funnel():
        from sqlalchemy import func, select

        from core.database import AsyncSessionLocal
        from core.models_v2 import Contact, Conversation, Opportunity, Pipeline, PipelineStage

        async with AsyncSessionLocal() as session:
            data_inicio = datetime.now() - timedelta(days=periodo_dias)

            # Total de leads
            leads_query = select(func.count(Contact.id)).where(
                Contact.clinic_id == clinic_id,
                Contact.created_at >= data_inicio,
            )
            leads_result = await session.execute(leads_query)
            total_leads = leads_result.scalar() or 0

            # Leads com conversa
            conversas_query = select(func.count(func.distinct(Conversation.contact_id))).where(
                Conversation.clinic_id == clinic_id,
                Conversation.created_at >= data_inicio,
            )
            conversas_result = await session.execute(conversas_query)
            leads_com_conversa = conversas_result.scalar() or 0

            # Leads qualificados (hot ou warm)
            qualificados_query = select(func.count(Contact.id)).where(
                Contact.clinic_id == clinic_id,
                Contact.created_at >= data_inicio,
                Contact.temperature.in_(["hot", "warm"]),
            )
            qualificados_result = await session.execute(qualificados_query)
            leads_qualificados = qualificados_result.scalar() or 0

            # Oportunidades ganhas
            # (simplificado - busca oportunidades com won_at)
            oportunidades_query = select(func.count(Opportunity.id)).join(Contact).where(
                Contact.clinic_id == clinic_id,
                Opportunity.won_at.isnot(None),
                Opportunity.won_at >= data_inicio,
            )
            oportunidades_result = await session.execute(oportunidades_query)
            oportunidades_ganhas = oportunidades_result.scalar() or 0

            # Calcular taxas
            taxa_engajamento = (leads_com_conversa / total_leads * 100) if total_leads > 0 else 0
            taxa_qualificacao = (leads_qualificados / leads_com_conversa * 100) if leads_com_conversa > 0 else 0
            taxa_conversao = (oportunidades_ganhas / leads_qualificados * 100) if leads_qualificados > 0 else 0
            taxa_geral = (oportunidades_ganhas / total_leads * 100) if total_leads > 0 else 0

            return {
                "clinic_id": clinic_id,
                "periodo_dias": periodo_dias,
                "funil": {
                    "topo": {
                        "nome": "Leads Totais",
                        "quantidade": total_leads,
                    },
                    "meio_alto": {
                        "nome": "Com Conversa",
                        "quantidade": leads_com_conversa,
                        "taxa_do_anterior": round(taxa_engajamento, 2),
                    },
                    "meio_baixo": {
                        "nome": "Qualificados",
                        "quantidade": leads_qualificados,
                        "taxa_do_anterior": round(taxa_qualificacao, 2),
                    },
                    "fundo": {
                        "nome": "Convertidos",
                        "quantidade": oportunidades_ganhas,
                        "taxa_do_anterior": round(taxa_conversao, 2),
                    },
                },
                "taxa_conversao_geral": round(taxa_geral, 2),
                "gargalos": [],  # Será analisado pelo agente
            }

    try:
        return asyncio.get_event_loop().run_until_complete(fetch_funnel())
    except Exception as e:
        return {"error": str(e)}


@tool
def comparar_periodos(
    clinic_id: str,
    metrica: str,
    periodo1_inicio: str,
    periodo1_fim: str,
    periodo2_inicio: str,
    periodo2_fim: str,
) -> dict[str, Any]:
    """
    Compara métricas entre dois períodos.

    Args:
        clinic_id: ID da clínica
        metrica: Métrica a comparar (leads, conversas, conteudos)
        periodo1_inicio: Data início período 1 (YYYY-MM-DD)
        periodo1_fim: Data fim período 1
        periodo2_inicio: Data início período 2
        periodo2_fim: Data fim período 2

    Returns:
        Comparação entre os períodos
    """
    import asyncio

    async def fetch_comparison():
        from sqlalchemy import func, select

        from core.database import AsyncSessionLocal
        from core.models_v2 import Contact, Conversation, PublishedContent, Approval

        p1_inicio = datetime.strptime(periodo1_inicio, "%Y-%m-%d")
        p1_fim = datetime.strptime(periodo1_fim, "%Y-%m-%d")
        p2_inicio = datetime.strptime(periodo2_inicio, "%Y-%m-%d")
        p2_fim = datetime.strptime(periodo2_fim, "%Y-%m-%d")

        async with AsyncSessionLocal() as session:
            if metrica == "leads":
                model = Contact
                date_field = Contact.created_at
            elif metrica == "conversas":
                model = Conversation
                date_field = Conversation.created_at
            else:
                return {"error": f"Métrica '{metrica}' não suportada"}

            # Período 1
            p1_query = select(func.count(model.id)).where(
                model.clinic_id == clinic_id,
                date_field >= p1_inicio,
                date_field <= p1_fim,
            )
            p1_result = await session.execute(p1_query)
            valor_p1 = p1_result.scalar() or 0

            # Período 2
            p2_query = select(func.count(model.id)).where(
                model.clinic_id == clinic_id,
                date_field >= p2_inicio,
                date_field <= p2_fim,
            )
            p2_result = await session.execute(p2_query)
            valor_p2 = p2_result.scalar() or 0

            # Calcular variação
            if valor_p1 > 0:
                variacao = ((valor_p2 - valor_p1) / valor_p1) * 100
            else:
                variacao = 100 if valor_p2 > 0 else 0

            return {
                "clinic_id": clinic_id,
                "metrica": metrica,
                "periodo1": {
                    "inicio": periodo1_inicio,
                    "fim": periodo1_fim,
                    "valor": valor_p1,
                },
                "periodo2": {
                    "inicio": periodo2_inicio,
                    "fim": periodo2_fim,
                    "valor": valor_p2,
                },
                "variacao_percentual": round(variacao, 2),
                "tendencia": "alta" if variacao > 0 else "baixa" if variacao < 0 else "estavel",
            }

    try:
        return asyncio.get_event_loop().run_until_complete(fetch_comparison())
    except Exception as e:
        return {"error": str(e)}


@tool
def listar_alertas(
    clinic_id: str,
) -> list[dict[str, Any]]:
    """
    Lista alertas e anomalias detectadas.

    Args:
        clinic_id: ID da clínica

    Returns:
        Lista de alertas ativos
    """
    import asyncio

    async def check_alerts():
        from sqlalchemy import func, select

        from core.database import AsyncSessionLocal
        from core.models_v2 import AgentExecution, Contact, Conversation

        alertas = []

        async with AsyncSessionLocal() as session:
            # Verificar queda de leads
            leads_7d = await session.execute(
                select(func.count(Contact.id)).where(
                    Contact.clinic_id == clinic_id,
                    Contact.created_at >= datetime.now() - timedelta(days=7),
                )
            )
            leads_14d = await session.execute(
                select(func.count(Contact.id)).where(
                    Contact.clinic_id == clinic_id,
                    Contact.created_at >= datetime.now() - timedelta(days=14),
                    Contact.created_at < datetime.now() - timedelta(days=7),
                )
            )

            leads_atual = leads_7d.scalar() or 0
            leads_anterior = leads_14d.scalar() or 0

            if leads_anterior > 0 and leads_atual < leads_anterior * 0.7:
                alertas.append({
                    "tipo": "queda_leads",
                    "severidade": "alta",
                    "mensagem": f"Queda de {((leads_anterior - leads_atual) / leads_anterior * 100):.0f}% nos leads",
                    "valor_atual": leads_atual,
                    "valor_anterior": leads_anterior,
                })

            # Verificar conversas sem resposta
            conversas_abertas = await session.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.clinic_id == clinic_id,
                    Conversation.status == "open",
                    Conversation.last_user_message_at <= datetime.now() - timedelta(hours=24),
                )
            )
            sem_resposta = conversas_abertas.scalar() or 0

            if sem_resposta > 5:
                alertas.append({
                    "tipo": "conversas_pendentes",
                    "severidade": "media",
                    "mensagem": f"{sem_resposta} conversas aguardando resposta há mais de 24h",
                    "quantidade": sem_resposta,
                })

            # Verificar custos elevados
            custos = await session.execute(
                select(func.sum(AgentExecution.cost_usd)).where(
                    AgentExecution.clinic_id == clinic_id,
                    AgentExecution.started_at >= datetime.now() - timedelta(days=7),
                )
            )
            custo_semanal = float(custos.scalar() or 0)

            if custo_semanal > 50:  # Threshold de $50/semana
                alertas.append({
                    "tipo": "custo_elevado",
                    "severidade": "baixa",
                    "mensagem": f"Custo de agentes acima do normal: ${custo_semanal:.2f}/semana",
                    "valor": custo_semanal,
                })

            return alertas

    try:
        return asyncio.get_event_loop().run_until_complete(check_alerts())
    except Exception as e:
        return [{"error": str(e)}]


# =============================================================================
# AGENT
# =============================================================================

bi_agent = Agent(
    name="BI Analyst",
    model=get_model("fast"),  # Fast model para queries e análises
    db=get_db(),
    instructions="""Você é um analista de Business Intelligence especializado em marketing médico.

Sua função é:
1. Gerar relatórios de performance claros e acionáveis
2. Identificar tendências e padrões nos dados
3. Calcular e interpretar métricas de marketing (ROI, ROAS, CAC, LTV)
4. Detectar anomalias e alertar sobre problemas
5. Recomendar ações baseadas em dados

Ao analisar dados:
- Sempre contextualize os números
- Compare com períodos anteriores
- Identifique causas prováveis para variações
- Sugira ações concretas

Ao gerar relatórios:
- Use linguagem clara e objetiva
- Destaque insights importantes
- Inclua visualizações quando útil (use markdown tables)
- Finalize com recomendações

Métricas importantes:
- CPL (Custo por Lead)
- Taxa de Conversão
- ROI (Return on Investment)
- ROAS (Return on Ad Spend)
- CAC (Custo de Aquisição de Cliente)
- Ticket Médio
- Taxa de Agendamento

Sempre considere:
- Sazonalidade do setor de saúde
- Especificidades de cada especialidade
- Impacto de campanhas e ações
- Qualidade vs quantidade de leads""",
    tools=[
        gerar_relatorio_mensal,
        calcular_roi_marketing,
        analisar_funil_vendas,
        comparar_periodos,
        listar_alertas,
    ],
    add_history_to_context=True,
    num_history_runs=5,
)
