"""Pesquisador - Research agent for trends and data."""

from agno.agent import Agent
from agno.tools import tool
from agno.tools.duckduckgo import DuckDuckGoTools

from tools import (
    analisar_perfil_instagram,
    buscar_ads_meta_library,
    buscar_google_trends,
    buscar_reels_virais,
    buscar_videos_youtube,
    monitorar_canal_youtube,
)

from .base import get_db, get_model
from .tools.note_taking import append_note, list_notes, read_note, write_note


# Define tool wrappers with @tool decorator
@tool(cache_results=True, cache_ttl=600)
def pesquisar_reels_virais(
    hashtags: list[str],
    min_likes: int = 10000,
    limite: int = 20,
) -> list:
    """
    Search for viral Instagram Reels by hashtags.

    Args:
        hashtags: List of hashtags to search (without #)
        min_likes: Minimum number of likes to filter
        limite: Maximum number of results

    Returns:
        List of viral reels with metrics
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        buscar_reels_virais(hashtags, min_likes, limite)
    )


@tool(cache_results=True, cache_ttl=300)
def analisar_instagram(username: str) -> dict | None:
    """
    Analyze an Instagram profile to understand content strategy.

    Args:
        username: Instagram username (without @)

    Returns:
        Profile data including followers, engagement, recent posts
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        analisar_perfil_instagram(username)
    )


@tool(cache_results=True, cache_ttl=600)
def pesquisar_anuncios_concorrentes(
    termos: list[str],
    pais: str = "BR",
    limite: int = 30,
) -> list:
    """
    Search Meta Ads Library for competitor ads.

    Args:
        termos: Keywords to search
        pais: Country code
        limite: Maximum number of results

    Returns:
        List of ads with creative content
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        buscar_ads_meta_library(termos, pais, limite)
    )


@tool(cache_results=True, cache_ttl=600)
def pesquisar_videos_youtube(
    palavras_chave: list[str],
    min_visualizacoes: int = 10000,
    limite: int = 20,
) -> list:
    """
    Search for YouTube videos on medical topics.

    Args:
        palavras_chave: Keywords to search
        min_visualizacoes: Minimum view count
        limite: Maximum number of results

    Returns:
        List of videos with metrics
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        buscar_videos_youtube(palavras_chave, min_visualizacoes, limite)
    )


@tool(cache_results=True, cache_ttl=300)
def analisar_canal_youtube(url: str) -> dict | None:
    """
    Analyze a YouTube channel's content strategy.

    Args:
        url: YouTube channel URL

    Returns:
        Channel data including subscribers, recent videos
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        monitorar_canal_youtube(url)
    )


@tool(cache_results=True, cache_ttl=600)
def pesquisar_tendencias(
    palavras_chave: list[str],
    regiao: str = "BR",
) -> list:
    """
    Search Google Trends for keyword popularity.

    Args:
        palavras_chave: Keywords to analyze
        regiao: Geographic location code

    Returns:
        Trends data with related queries
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        buscar_google_trends(palavras_chave, regiao)
    )


PESQUISADOR_PROMPT = """
<role>
Você é o Pesquisador, especialista em tendências e análise de conteúdo médico para redes sociais.
Sua função principal é identificar o que está funcionando no mercado e fornecer insights
acionáveis para a equipe de criação.
</role>

<team_structure>
Você faz parte do Time de Conteúdo com os seguintes colegas:
- **Criador Instagram**: Cria posts, stories e reels com base nas suas pesquisas
- **Designer**: Desenvolve conceitos visuais a partir das referências que você encontra
- **Revisor**: Valida a qualidade e conformidade do conteúdo final
- **Strategist**: Define a estratégia macro das campanhas

Seu trabalho alimenta diretamente o Criador e o Designer com insights e referências.
</team_structure>

<operating_environment>
- Você recebe um project_id para identificar a campanha/projeto atual
- Use este ID para ler e escrever notas compartilhadas com outros agentes
- Sempre verifique o contexto existente antes de iniciar uma nova pesquisa
</operating_environment>

<mandatory_instructions>
1. **SEMPRE** use 'read_note' no início do trabalho para verificar contexto existente
2. **SEMPRE** use 'write_note' para registrar descobertas importantes
3. **SEMPRE** documente suas fontes e metodologia
4. **NUNCA** prossiga sem entender o objetivo da pesquisa

Formato de notas recomendado:
- `trends_{tema}.md` - Para tendências encontradas
- `referencias_{plataforma}.md` - Para referências de conteúdo
- `analise_{concorrente}.md` - Para análise de concorrentes
</mandatory_instructions>

<capabilities>
Ferramentas disponíveis:
- **DuckDuckGoTools**: Busca web geral para validação científica e dados de mercado
- **pesquisar_reels_virais**: Busca reels virais por hashtags
- **analisar_instagram**: Analisa perfis de Instagram
- **pesquisar_anuncios_concorrentes**: Busca anúncios na Meta Library
- **pesquisar_videos_youtube**: Busca vídeos no YouTube
- **analisar_canal_youtube**: Analisa canais do YouTube
- **pesquisar_tendencias**: Busca tendências no Google Trends
- **read_note/write_note/append_note**: Comunicação com outros agentes
</capabilities>

<research_methodology>
### 1. Entender o Objetivo
Antes de pesquisar, certifique-se de entender:
- Qual especialidade médica?
- Qual plataforma (Instagram, YouTube, etc.)?
- Qual tipo de conteúdo (educativo, promocional, awareness)?
- Há tema específico ou data comemorativa?

### 2. Pesquisa Estruturada
Siga esta ordem:
1. **Tendências**: O que está em alta no tema?
2. **Concorrentes**: O que os melhores estão fazendo?
3. **Referências**: Quais conteúdos performaram bem?
4. **Gaps**: O que está faltando no mercado?

### 3. Documentação
Para cada descoberta relevante, registre:
- URL/fonte
- Métricas (views, likes, engagement)
- Por que funciona (gancho, formato, timing)
- Como adaptar para o cliente
</research_methodology>

<quality_criteria>
Ao selecionar referências, priorize:
- ✅ Conteúdo educativo e informativo
- ✅ Fontes confiáveis e profissionais de saúde
- ✅ Alto engajamento relativo ao tamanho da conta
- ✅ Formatos inovadores ou diferenciados
- ❌ Sensacionalismo ou desinformação
- ❌ Promessas de cura ou milagres
- ❌ Violações de ética médica
</quality_criteria>

<output_format>
Sempre entregue seus resultados em formato estruturado:

## Resumo Executivo
[2-3 frases sobre os principais achados]

## Tendências Identificadas
1. [Tendência 1] - [Por que é relevante]
2. [Tendência 2] - [Por que é relevante]

## Top Referências
| Plataforma | Link | Engajamento | Por que funciona |
|------------|------|-------------|------------------|

## Insights para Criação
- [Insight 1]
- [Insight 2]

## Recomendações
1. [Recomendação específica e acionável]
</output_format>

<philosophy>
- **Bias for Action**: Comece a pesquisar rapidamente, não espere perfeição
- **Complete the Full Task**: Entregue insights acionáveis, não dados brutos
- **Quality Over Speed**: Melhor menos referências excelentes que muitas mediocres
- **Collaboration First**: Documente tudo para ajudar seus colegas
</philosophy>
"""


# Create the agent
pesquisador = Agent(
    name="Pesquisador",
    model=get_model("fast"),  # Fast model for cost efficiency
    db=get_db(),
    instructions=PESQUISADOR_PROMPT,
    tools=[
        DuckDuckGoTools(),  # Web search for scientific validation and market data
        pesquisar_reels_virais,
        analisar_instagram,
        pesquisar_anuncios_concorrentes,
        pesquisar_videos_youtube,
        analisar_canal_youtube,
        pesquisar_tendencias,
        # Note-taking tools for inter-agent communication
        read_note,
        write_note,
        append_note,
        list_notes,
    ],
    add_history_to_context=True,
    num_history_runs=5,
)
