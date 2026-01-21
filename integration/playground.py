"""
Agno Agent UI Playground - Separate endpoint for agent validation and testing.

This module provides a standalone playground interface for testing MedFlow agents
without affecting the production API. Connect with Agno Agent UI at:
- https://app.agno.com/playground (hosted)
- Or run locally: npx create-agent-ui@latest

Usage:
    # Run the playground server
    python -m playground

    # Or with uvicorn directly
    uvicorn playground:app --reload --port 7777

The playground runs on port 7777 by default (Agno Agent UI default).
"""

import os
import sys

# Add the integration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agno.agent import Agent
from agno.playground import Playground, serve_playground_app
from agno.tools.duckduckgo import DuckDuckGoTools

from agents.base import get_agent_storage, get_db, get_model, AGENT_STORAGE_DIR
from core.config import get_settings

settings = get_settings()


# =============================================================================
# AGENT DEFINITIONS FOR TESTING
# =============================================================================


def create_creative_director():
    """Create the Creative Director agent for content ideation."""
    return Agent(
        name="Creative Director",
        agent_id="creative_director",
        model=get_model("smart"),
        storage=get_agent_storage("creative_director"),
        db=get_db(),
        description="Especialista em marketing médico ético. Cria conteúdo para redes sociais seguindo normas do CFM.",
        instructions=[
            "Você é o Creative Director da MedFlow, especialista em marketing médico.",
            "Crie conteúdo que seja ético, seguindo as regras do CFM/CRM para publicidade médica.",
            "NUNCA prometa resultados específicos de tratamentos.",
            "NUNCA use termos como 'melhor', 'único', 'garantido' para procedimentos.",
            "Foque em educação, prevenção e bem-estar.",
            "Use linguagem acessível mas profissional.",
            "Inclua CTAs sutis e não agressivos.",
            "Sugira hashtags relevantes quando apropriado.",
        ],
        add_history_to_context=True,
        markdown=True,
    )


def create_copywriter():
    """Create the Copywriter agent for text generation."""
    return Agent(
        name="Copywriter",
        agent_id="copywriter",
        model=get_model("smart"),
        storage=get_agent_storage("copywriter"),
        db=get_db(),
        description="Copywriter especializado em marketing médico. Gera textos para posts, anúncios e campanhas.",
        instructions=[
            "Você é um copywriter especializado em marketing médico ético.",
            "Sempre siga as normas do CFM/CRM para publicidade médica.",
            "Crie textos persuasivos mas responsáveis.",
            "Adapte o tom conforme solicitado: profissional, amigável, educativo, etc.",
            "Inclua CTAs apropriados para cada formato.",
            "Sugira hashtags quando relevante.",
        ],
        add_history_to_context=True,
        markdown=True,
    )


def create_seo_analyst():
    """Create the SEO Analyst agent for search optimization."""
    return Agent(
        name="SEO Analyst",
        agent_id="seo_analyst",
        model=get_model("smart"),
        storage=get_agent_storage("seo_analyst"),
        db=get_db(),
        description="Analista de SEO para clínicas médicas. Pesquisa keywords e otimiza conteúdo.",
        instructions=[
            "Você é um analista de SEO especializado em saúde e medicina.",
            "Pesquise keywords relevantes para a especialidade médica.",
            "Sugira otimizações de conteúdo para melhor ranking.",
            "Analise a concorrência e identifique oportunidades.",
            "Foque em SEO local para clínicas.",
        ],
        tools=[DuckDuckGoTools()],
        add_history_to_context=True,
        markdown=True,
    )


def create_lead_qualifier():
    """Create the Lead Qualifier agent for lead scoring."""
    return Agent(
        name="Lead Qualifier",
        agent_id="lead_qualifier",
        model=get_model("fast"),
        storage=get_agent_storage("lead_qualifier"),
        db=get_db(),
        description="Qualifica leads e identifica oportunidades de conversão.",
        instructions=[
            "Você é um especialista em qualificação de leads para clínicas médicas.",
            "Analise o perfil do lead e determine seu potencial.",
            "Identifique sinais de intenção de compra.",
            "Sugira próximos passos para conversão.",
            "Classifique leads como: hot, warm, cold.",
        ],
        add_history_to_context=True,
        markdown=True,
    )


def create_appointment_scheduler():
    """Create the Appointment Scheduler agent."""
    return Agent(
        name="Appointment Scheduler",
        agent_id="appointment_scheduler",
        model=get_model("fast"),
        storage=get_agent_storage("appointment_scheduler"),
        db=get_db(),
        description="Gerencia agendamentos e disponibilidade de horários.",
        instructions=[
            "Você é o assistente de agendamento da clínica.",
            "Ajude pacientes a encontrar horários disponíveis.",
            "Confirme dados necessários para o agendamento.",
            "Envie lembretes e confirmações quando apropriado.",
            "Seja cordial e eficiente.",
        ],
        add_history_to_context=True,
        markdown=True,
    )


def create_coordinator():
    """Create the Coordinator agent for routing."""
    return Agent(
        name="Coordinator",
        agent_id="coordinator",
        model=get_model("fast"),
        storage=get_agent_storage("coordinator"),
        db=get_db(),
        description="Roteador de mensagens. Identifica intenções e direciona para o agente apropriado.",
        instructions=[
            "Você é o coordenador de atendimento da MedFlow.",
            "Analise a mensagem do usuário e identifique a intenção.",
            "Determine qual agente deve atender: scheduling, sales, support, creative.",
            "Extraia informações relevantes da mensagem.",
            "Responda em JSON com: agent, confidence, reasoning.",
        ],
        add_history_to_context=False,
        markdown=False,
    )


def create_researcher():
    """Create the Researcher agent for market research."""
    return Agent(
        name="Researcher",
        agent_id="researcher",
        model=get_model("smart"),
        storage=get_agent_storage("researcher"),
        db=get_db(),
        description="Pesquisador de mercado e tendências em saúde.",
        instructions=[
            "Você é um pesquisador especializado em marketing médico.",
            "Pesquise tendências de mercado na área de saúde.",
            "Analise concorrentes e identifique diferenciais.",
            "Sugira oportunidades de conteúdo baseadas em dados.",
            "Mantenha-se atualizado sobre mudanças regulatórias.",
        ],
        tools=[DuckDuckGoTools()],
        add_history_to_context=True,
        markdown=True,
    )


# =============================================================================
# PLAYGROUND SETUP
# =============================================================================


def get_playground_agents() -> list[Agent]:
    """Get all agents configured for the playground."""
    try:
        return [
            create_creative_director(),
            create_copywriter(),
            create_seo_analyst(),
            create_lead_qualifier(),
            create_appointment_scheduler(),
            create_coordinator(),
            create_researcher(),
        ]
    except ValueError as e:
        print(f"⚠️  Warning: Could not create all agents: {e}")
        print("   Some agents may require API keys to be configured.")
        return []


# Create the playground
playground = Playground(agents=get_playground_agents())

# Get the FastAPI app
app = playground.get_app()


# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "agno-playground",
        "agents": len(playground.agents) if hasattr(playground, "agents") else 0,
        "storage_dir": str(AGENT_STORAGE_DIR),
    }


@app.get("/")
async def root():
    """Root endpoint with instructions."""
    return {
        "service": "MedFlow Agent Playground",
        "description": "Test MedFlow agents with Agno Agent UI",
        "connect": {
            "hosted": "https://app.agno.com/playground",
            "local": "npx create-agent-ui@latest",
            "endpoint": "http://localhost:7777/v1",
        },
        "agents": [
            "Creative Director",
            "Copywriter",
            "SEO Analyst",
            "Lead Qualifier",
            "Appointment Scheduler",
            "Coordinator",
            "Researcher",
        ],
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🎮 MedFlow Agent Playground")
    print("=" * 60)
    print()
    print("Connect with Agno Agent UI:")
    print("  • Hosted: https://app.agno.com/playground")
    print("  • Local:  npx create-agent-ui@latest")
    print()
    print("Endpoint: http://localhost:7777/v1")
    print()
    print("Available agents:")
    for agent in get_playground_agents():
        print(f"  • {agent.name}: {agent.description[:50]}...")
    print()
    print("=" * 60)

    # Serve the playground
    serve_playground_app("playground:app", reload=True, port=7777)
