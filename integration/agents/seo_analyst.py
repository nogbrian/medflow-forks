"""
SEO Analyst Agent - Search Optimization and Content Analytics.

Specialized agent for:
- Keyword research and optimization
- Meta descriptions and title optimization
- Content structure and HTML semantics
- Search performance analysis
"""

from agno.agent import Agent
from agno.tools import tool
from agno.tools.duckduckgo import DuckDuckGoTools

from .base import get_db, get_model
from .tools.note_taking import append_note, list_notes, read_note, write_note


@tool(cache_results=True, cache_ttl=600)
def analyze_serp(query: str, num_results: int = 10) -> list[dict]:
    """
    Analyze Search Engine Results Page for a given query.

    Args:
        query: Search query to analyze
        num_results: Number of results to analyze

    Returns:
        List of top results with titles, descriptions, and URLs
    """
    from duckduckgo_search import DDGS

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            return [
                {
                    "position": i + 1,
                    "title": r.get("title", ""),
                    "description": r.get("body", ""),
                    "url": r.get("href", ""),
                }
                for i, r in enumerate(results)
            ]
    except Exception:
        return []


@tool(cache_results=True, cache_ttl=300)
def suggest_keywords(seed_keyword: str, language: str = "pt-BR") -> list[str]:
    """
    Suggest related keywords based on a seed keyword.

    Uses search autocomplete and related searches to find variations.

    Args:
        seed_keyword: Primary keyword to expand
        language: Target language for suggestions

    Returns:
        List of related keyword suggestions
    """
    from duckduckgo_search import DDGS

    suggestions = []
    try:
        with DDGS() as ddgs:
            # Get autocomplete suggestions
            autocomplete = list(ddgs.suggestions(seed_keyword))
            suggestions.extend([s.get("phrase", "") for s in autocomplete])

            # Get related searches from actual search
            results = list(ddgs.text(seed_keyword, max_results=5))
            for result in results:
                # Extract potential keywords from titles
                title = result.get("title", "")
                if title and seed_keyword.lower() in title.lower():
                    suggestions.append(title)
    except Exception:
        pass

    # Deduplicate and limit
    return list(set(suggestions))[:20]


@tool
def analyze_content_seo(
    title: str,
    content: str,
    target_keyword: str,
) -> dict:
    """
    Analyze content for SEO optimization opportunities.

    Checks keyword density, title optimization, content length,
    and provides actionable recommendations.

    Args:
        title: Content title
        content: Full content text
        target_keyword: Primary keyword to optimize for

    Returns:
        SEO analysis with scores and recommendations
    """
    content_lower = content.lower()
    target_lower = target_keyword.lower()

    # Calculate metrics
    word_count = len(content.split())
    keyword_count = content_lower.count(target_lower)
    keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0

    # Title analysis
    title_has_keyword = target_lower in title.lower()
    title_length = len(title)

    # Content structure (basic checks)
    has_subheadings = any(
        marker in content for marker in ["##", "<h2>", "<h3>", "**"]
    )

    # Score calculation (0-100)
    score = 0

    # Keyword presence (30 points)
    if title_has_keyword:
        score += 15
    if keyword_count >= 3:
        score += 15
    elif keyword_count >= 1:
        score += 10

    # Keyword density (20 points) - ideal is 1-3%
    if 1.0 <= keyword_density <= 3.0:
        score += 20
    elif 0.5 <= keyword_density <= 4.0:
        score += 10

    # Content length (25 points)
    if word_count >= 1500:
        score += 25
    elif word_count >= 1000:
        score += 20
    elif word_count >= 500:
        score += 15
    elif word_count >= 300:
        score += 10

    # Title length (15 points) - ideal is 50-60 chars
    if 50 <= title_length <= 60:
        score += 15
    elif 40 <= title_length <= 70:
        score += 10

    # Structure (10 points)
    if has_subheadings:
        score += 10

    # Build recommendations
    recommendations = []

    if not title_has_keyword:
        recommendations.append(
            f"Inclua '{target_keyword}' no título para melhor relevância"
        )

    if title_length > 60:
        recommendations.append(
            f"Título muito longo ({title_length} chars). Ideal: 50-60 caracteres"
        )
    elif title_length < 40:
        recommendations.append(
            f"Título muito curto ({title_length} chars). Ideal: 50-60 caracteres"
        )

    if keyword_density < 1.0:
        recommendations.append(
            f"Densidade de keyword baixa ({keyword_density:.1f}%). "
            f"Considere mencionar '{target_keyword}' mais vezes naturalmente"
        )
    elif keyword_density > 3.0:
        recommendations.append(
            f"Densidade de keyword alta ({keyword_density:.1f}%). "
            "Reduza para evitar penalização"
        )

    if word_count < 500:
        recommendations.append(
            f"Conteúdo curto ({word_count} palavras). "
            "Conteúdos mais longos (1000+) tendem a ranquear melhor"
        )

    if not has_subheadings:
        recommendations.append(
            "Adicione subtítulos (H2, H3) para melhorar legibilidade e SEO"
        )

    return {
        "score": score,
        "metrics": {
            "word_count": word_count,
            "keyword_count": keyword_count,
            "keyword_density": round(keyword_density, 2),
            "title_length": title_length,
            "title_has_keyword": title_has_keyword,
            "has_subheadings": has_subheadings,
        },
        "recommendations": recommendations,
        "verdict": "OTIMIZADO" if score >= 70 else "PRECISA MELHORIAS" if score >= 50 else "NECESSITA REVISÃO",
    }


@tool
def generate_meta_tags(
    title: str,
    content: str,
    target_keyword: str,
) -> dict:
    """
    Generate optimized meta tags for content.

    Creates SEO-optimized title tag, meta description,
    and Open Graph tags.

    Args:
        title: Content title
        content: Full content text
        target_keyword: Primary keyword to optimize for

    Returns:
        Dictionary with optimized meta tags
    """
    # Extract first meaningful sentences for description
    sentences = content.replace("\n", " ").split(".")
    description_base = ". ".join(sentences[:2]).strip()
    if len(description_base) > 155:
        description_base = description_base[:152] + "..."

    # Ensure keyword is in description
    if target_keyword.lower() not in description_base.lower():
        description_base = f"{target_keyword}: {description_base}"
        if len(description_base) > 160:
            description_base = description_base[:157] + "..."

    # Optimize title tag
    title_tag = title
    if len(title_tag) > 60:
        title_tag = title_tag[:57] + "..."
    if target_keyword.lower() not in title_tag.lower():
        title_tag = f"{target_keyword} - {title_tag}"[:60]

    return {
        "title_tag": title_tag,
        "meta_description": description_base,
        "og_title": title[:60],
        "og_description": description_base[:200],
        "keywords": [target_keyword] + target_keyword.split()[:4],
        "character_counts": {
            "title": len(title_tag),
            "description": len(description_base),
        },
    }


SEO_ANALYST_PROMPT = """
<role>
Você é o Analista de SEO, especialista em otimização de conteúdo para mecanismos de busca
no nicho de saúde e medicina. Sua função é garantir que todo conteúdo seja encontrável
e bem posicionado nas buscas.
</role>

<team_structure>
Você faz parte do Time de Conteúdo com os seguintes colegas:
- **Pesquisador**: Fornece dados de mercado e tendências
- **Criador Instagram**: Cria o conteúdo que você otimiza
- **Revisor**: Valida a conformidade com CFM (trabalha em paralelo com você)
- **Strategist**: Define a estratégia macro das campanhas

Você trabalha em paralelo com o Revisor, cada um avaliando aspectos diferentes.
</team_structure>

<operating_environment>
- Você recebe um project_id para identificar a campanha/projeto atual
- Use este ID para ler e escrever notas compartilhadas
- Documente suas análises e recomendações para o time
</operating_environment>

<mandatory_instructions>
1. **SEMPRE** use 'read_note' no início para verificar contexto existente
2. **SEMPRE** use 'write_note' para documentar suas análises SEO
3. **SEMPRE** forneça recomendações acionáveis e específicas
4. **NUNCA** otimize keywords que violem normas de marketing médico
5. **NUNCA** recomende práticas de black-hat SEO

Formato de notas recomendado:
- `seo_analysis_{conteudo_id}.md` - Análise SEO completa
- `keywords_{tema}.md` - Pesquisa de keywords
</mandatory_instructions>

<capabilities>
Ferramentas disponíveis:
- **analyze_serp**: Analisa resultados de busca para uma query
- **suggest_keywords**: Sugere keywords relacionadas
- **analyze_content_seo**: Análise completa de SEO do conteúdo
- **generate_meta_tags**: Gera meta tags otimizadas
- **read_note/write_note/append_note**: Comunicação com outros agentes
- **DuckDuckGoTools**: Busca web para pesquisa de concorrentes
</capabilities>

<seo_guidelines>
## Princípios para SEO Médico

### Keywords Permitidas
- Termos informativos: "o que é [condição]", "sintomas de [condição]"
- Procedimentos: "como funciona [procedimento]"
- Perguntas frequentes: "quando procurar [especialidade]"
- Localização: "[especialidade] em [cidade]"

### Keywords a Evitar
- ❌ "melhor médico", "tratamento garantido", "cura definitiva"
- ❌ Promessas de resultado: "emagreça X kg"
- ❌ Comparativos sem evidência: "mais eficaz que"

### Estrutura de Conteúdo
1. **Título**: 50-60 caracteres, keyword no início
2. **Meta Description**: 150-160 caracteres, keyword natural
3. **Headers**: H2/H3 com variações da keyword
4. **Densidade**: 1-3% de keyword density
5. **Comprimento**: 1000+ palavras para blog posts

### Schema Markup Recomendado
- MedicalWebPage para artigos médicos
- FAQPage para seções de perguntas
- LocalBusiness para páginas de clínica
</seo_guidelines>

<output_format>
Sempre entregue análises estruturadas:

## Análise SEO: [Título do Conteúdo]

### Score Geral: [X/100]
**Veredicto**: [OTIMIZADO / PRECISA MELHORIAS / NECESSITA REVISÃO]

### Métricas
| Métrica | Valor | Status |
|---------|-------|--------|
| Palavra-chave no título | ✅/❌ | |
| Densidade de keyword | X% | |
| Tamanho do conteúdo | X palavras | |
| Meta description | X chars | |

### Recomendações Prioritárias
1. [Ação específica e urgente]
2. [Ação importante]
3. [Melhoria opcional]

### Meta Tags Otimizadas
```html
<title>[título otimizado]</title>
<meta name="description" content="[descrição otimizada]">
```

### Keywords Secundárias Sugeridas
- [keyword 1]
- [keyword 2]
</output_format>

<workflow>
### 1. Contextualizar
- Leia as notas do projeto (briefing, objetivo)
- Identifique a keyword principal
- Entenda o público-alvo

### 2. Pesquisar
- Analise SERP da keyword principal
- Identifique concorrentes bem posicionados
- Sugira keywords secundárias

### 3. Analisar
- Avalie o conteúdo com analyze_content_seo
- Gere meta tags otimizadas
- Identifique gaps de otimização

### 4. Recomendar
- Liste ações prioritárias
- Forneça exemplos específicos
- Documente em notas para o time
</workflow>

<philosophy>
- **Bias for Action**: Análises rápidas com recomendações claras
- **Complete the Full Task**: Entregue análise + recomendações + meta tags
- **Quality Over Speed**: Melhor uma análise profunda que várias superficiais
- **Collaboration First**: Documente para ajudar o Criador a melhorar
</philosophy>
"""


# Create the agent with DuckDuckGo tools for web search
seo_analyst = Agent(
    name="SEO Analyst",
    model=get_model("fast"),  # Fast model for cost efficiency
    db=get_db(),
    instructions=SEO_ANALYST_PROMPT,
    tools=[
        DuckDuckGoTools(),  # Web search for competitor research
        analyze_serp,
        suggest_keywords,
        analyze_content_seo,
        generate_meta_tags,
        # Note-taking tools for inter-agent communication
        read_note,
        write_note,
        append_note,
        list_notes,
    ],
    add_history_to_context=True,
    num_history_runs=5,
)
