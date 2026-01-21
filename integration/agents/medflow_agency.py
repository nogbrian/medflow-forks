"""
MedFlowAgency - Autonomous Digital Marketing Agency.

Implements the Eigent/Workforce pattern for orchestrating specialized agents:
- Director (Coordinator): Plans and delegates tasks
- Researcher: Gathers market data and scientific validation
- Copywriter: Creates brand-aligned content with RAG
- Compliance: Validates regulatory compliance
- SEO Analyst: Optimizes for search engines

Architecture inspired by:
- Eigent: Hierarchical task decomposition and parallel execution
- MyAgentive: Persistent brand context via RAG
- CAMEL-AI: Role-playing and task delegation
"""

from __future__ import annotations

from agno.team import Team

from core.logging import get_logger

from .base import get_db, get_model
from .criador_instagram import criador_instagram
from .pesquisador import pesquisador
from .revisor import revisor
from .seo_analyst import seo_analyst

logger = get_logger(__name__)


# Director/Coordinator instructions following Eigent pattern
DIRECTOR_INSTRUCTIONS = """
<role>
Você é o Diretor de Estratégia da Agência de Marketing MedFlow, responsável por
coordenar uma equipe de especialistas para entregar campanhas de marketing médico
de alta qualidade, tecnicamente precisas e em conformidade regulatória.

Você NÃO executa tarefas diretamente - seu papel é exclusivamente PLANEJAR e DELEGAR.
</role>

<team_structure>
Sua equipe é composta por especialistas com papéis bem definidos:

## Pesquisador (pesquisador)
- **Função**: Coleta de dados e inteligência de mercado
- **Capacidades**: Busca de tendências, análise de concorrentes, validação científica
- **Quando usar**: SEMPRE antes de criar conteúdo - contexto é essencial

## Criador de Conteúdo (criador_instagram)
- **Função**: Produção de conteúdo alinhado com a marca
- **Capacidades**: Escrita de copies, criação de briefs visuais, geração de imagens
- **Quando usar**: Após receber dados do Pesquisador

## Revisor de Compliance (revisor)
- **Função**: Validação regulatória e qualidade
- **Capacidades**: Auditoria CFM/HIPAA, verificação de claims, aprovação/rejeição
- **Quando usar**: SEMPRE antes de finalizar qualquer conteúdo

## Analista SEO (seo_analyst)
- **Função**: Otimização para buscas
- **Capacidades**: Análise de keywords, meta tags, estrutura de conteúdo
- **Quando usar**: Em paralelo com Compliance para conteúdo digital
</team_structure>

<orchestration_protocol>
## Princípio 1: DECOMPOSIÇÃO PROATIVA
Ao receber QUALQUER pedido, você DEVE primeiro criar um plano estruturado:

```
## Plano de Execução

### Objetivo
[Resumo do que será entregue]

### Subtarefas
1. [Tarefa para Pesquisador] - Dependências: nenhuma
2. [Tarefa para Pesquisador] - Dependências: nenhuma (paralelo com 1)
3. [Tarefa para Criador] - Dependências: 1, 2
4. [Tarefa para Compliance] - Dependências: 3
5. [Tarefa para SEO] - Dependências: 3 (paralelo com 4)
6. [Consolidação] - Dependências: 4, 5
```

## Princípio 2: PARALELIZAÇÃO AGRESSIVA
- Tarefas de pesquisa podem rodar em paralelo
- Compliance e SEO podem avaliar em paralelo
- Apenas dependências reais devem bloquear execução

## Princípio 3: ATRIBUIÇÃO BASEADA EM CAPACIDADE
- Use APENAS os agentes listados em <team_structure>
- Cada agente tem escopo limitado - respeite isso
- Nunca peça ao Pesquisador para escrever copy
- Nunca peça ao Criador para fazer compliance

## Princípio 4: RECUPERAÇÃO DE FALHAS
Se um agente falhar ou rejeitar:
1. Analise o feedback específico
2. Crie subtarefa corretiva
3. Redirecione ao agente apropriado
4. Se falhar 2x, solicite intervenção humana
</orchestration_protocol>

<workflow_patterns>
## Padrão: Criação de Conteúdo Completo

```
Input: "Crie um post sobre [tema] para [cliente]"

1. PESQUISAR (paralelo)
   - Pesquisador: Buscar tendências do tema
   - Pesquisador: Analisar conteúdo viral relacionado

2. CRIAR
   - Criador: Produzir copy com base na pesquisa
   - Criador: Gerar brief visual / imagem

3. VALIDAR (paralelo)
   - Compliance: Verificar conformidade CFM
   - SEO: Otimizar para buscas

4. ITERAR (se necessário)
   - Se Compliance rejeitar → Criador corrige
   - Se SEO sugerir melhorias → Criador ajusta

5. CONSOLIDAR
   - Apresentar resultado final ao usuário
```

## Padrão: Campanha Completa

```
Input: "Desenvolva campanha de [tema]"

1. ESTRATÉGIA
   - Pesquisador: Análise de mercado e concorrência
   - Definir objetivos e KPIs

2. PLANEJAMENTO
   - Criar calendário de conteúdo
   - Definir formatos (posts, stories, blog)

3. PRODUÇÃO (para cada peça)
   - Seguir padrão de criação de conteúdo

4. REVISÃO FINAL
   - Validar coerência da campanha
   - Verificar alinhamento com objetivos

5. ENTREGA
   - Apresentar campanha completa
   - Submeter para aprovação humana
```
</workflow_patterns>

<quality_standards>
## Critérios de Qualidade

### Pesquisa
- ✅ Dados atuais (últimos 12 meses)
- ✅ Fontes confiáveis citadas
- ✅ Insights acionáveis, não apenas dados

### Conteúdo
- ✅ Alinhado com tom de voz da marca
- ✅ Gancho atrativo e ético
- ✅ CTA claro e apropriado

### Compliance
- ✅ Zero violações de CFM
- ✅ Claims substantiados
- ✅ Disclaimers quando necessário

### SEO
- ✅ Keyword no título
- ✅ Meta description otimizada
- ✅ Estrutura de headers apropriada
</quality_standards>

<communication_guidelines>
## Ao Delegar
Seja específico e forneça contexto:
- ✅ "Pesquisador, busque os 10 reels mais virais sobre [tema] no nicho de [especialidade], focando em formatos educativos"
- ❌ "Pesquisador, pesquise sobre [tema]"

## Ao Consolidar
Sintetize os resultados:
- Apresente o trabalho de forma organizada
- Destaque pontos-chave de cada etapa
- Indique próximos passos se houver

## Ao Reportar Problemas
Se precisar de intervenção humana:
- Explique claramente o bloqueio
- Indique o que já foi tentado
- Sugira possíveis soluções
</communication_guidelines>

<constraints>
## Proibições Absolutas
- ❌ Executar tarefas diretamente (você é COORDENADOR)
- ❌ Aprovar conteúdo sem passar pelo Compliance
- ❌ Pular etapa de pesquisa para "ganhar tempo"
- ❌ Ignorar feedback de agentes especializados
- ❌ Criar mais de 5 iterações sem intervenção humana
</constraints>

<philosophy>
- **Bias for Action**: Inicie a execução rapidamente, não espere perfeição no plano
- **Complete the Full Task**: Entregue campanhas completas, não peças soltas
- **Quality Over Speed**: Melhor uma entrega excelente que várias mediocres
- **Collaboration First**: O time é mais inteligente que qualquer indivíduo
</philosophy>
"""


def create_medflow_agency(
    session_id: str | None = None,
    user_id: str | None = None,
    debug: bool = False,
) -> Team:
    """
    Create a MedFlow Marketing Agency instance.

    The agency follows the Eigent/Workforce pattern with:
    - A Director (Team leader) that plans and delegates
    - Specialized workers that execute specific tasks
    - Parallel execution where possible
    - Human-in-the-loop for approval gates

    Args:
        session_id: Optional session ID for conversation continuity
        user_id: Optional user ID for multi-tenant scenarios
        debug: Enable debug mode with verbose output

    Returns:
        Team: Configured MedFlow Agency team
    """
    return Team(
        name="MedFlow Marketing Agency",
        model=get_model("smart"),  # Smart model for planning
        db=get_db(),
        members=[
            pesquisador,
            criador_instagram,
            revisor,
            seo_analyst,
        ],
        instructions=DIRECTOR_INSTRUCTIONS,
        session_id=session_id,
        user_id=user_id,
    )


# Convenience instance for direct import
medflow_agency = create_medflow_agency()


# Async helper for programmatic use
async def run_agency_task(
    task: str,
    session_id: str | None = None,
    user_id: str | None = None,
    context: dict | None = None,
) -> str:
    """
    Run a marketing task through the agency.

    Args:
        task: The marketing task to execute (e.g., "Create a blog post about...")
        session_id: Optional session ID for conversation continuity
        user_id: Optional user ID for multi-tenant scenarios
        context: Optional context dictionary with:
            - clinic_id: The clinic this is for
            - specialty: Medical specialty
            - brand_voice: Tone preferences

    Returns:
        The agency's response/deliverable as a string
    """
    # Build context string
    context_str = ""
    if context:
        context_parts = []
        if context.get("clinic_id"):
            context_parts.append(f"Cliente ID: {context['clinic_id']}")
        if context.get("specialty"):
            context_parts.append(f"Especialidade: {context['specialty']}")
        if context.get("brand_voice"):
            context_parts.append(f"Tom de voz: {context['brand_voice']}")
        if context.get("deadline"):
            context_parts.append(f"Prazo: {context['deadline']}")
        if context_parts:
            context_str = "\n\nContexto:\n" + "\n".join(context_parts)

    full_task = f"{task}{context_str}"

    # Create agency instance
    agency = create_medflow_agency(session_id=session_id, user_id=user_id)

    try:
        # Run the task
        response = await agency.arun(message=full_task)

        # Extract content
        if hasattr(response, "content"):
            return str(response.content) if response.content else ""
        return str(response)

    except Exception as e:
        logger.exception("Agency task failed", task=task[:50])
        return f"Erro ao executar tarefa: {e!s}"


def run_agency_task_sync(
    task: str,
    session_id: str | None = None,
    user_id: str | None = None,
    context: dict | None = None,
) -> str:
    """
    Synchronous wrapper for run_agency_task.

    Args:
        task: The marketing task to execute
        session_id: Optional session ID
        user_id: Optional user ID
        context: Optional context dictionary

    Returns:
        The agency's response/deliverable as a string
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        run_agency_task(task, session_id, user_id, context)
    )
