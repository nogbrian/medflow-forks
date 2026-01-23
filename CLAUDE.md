# MedFlow — Projeto de Superagente Multi-LLM para Marketing Médico

## O Que É Este Projeto

O MedFlow é uma plataforma de atendimento e marketing para consultórios médicos brasileiros. O core é a integração de Three forks: Twenty CRM + Chatwoot + Cal.com. Sobre essa base, estamos construindo um **superagente autônomo multi-LLM** — o equivalente funcional do Claude Code, mas para marketing médico.

O superagente NÃO é o Claude Code. É um produto independente que roda com múltiplos providers (Anthropic, OpenAI, Google, xAI) via Agno Framework, tem seu próprio agentic loop, tool registry, context management, e orquestração multi-agente.

## Stack

- **Backend**: FastAPI + Python 3.12 + SQLAlchemy async + PostgreSQL + Redis + arq
- **Agents**: Agno Framework (multi-LLM) + loop agêntico próprio em `core/agentic/`
- **LLM Router**: Multi-provider com fallback em `core/llm_router.py`
- **Frontend**: Next.js 14 + React 18 + TanStack Query + Tailwind
- **WhatsApp**: Evolution API
- **Integrações**: Twenty CRM (GraphQL), Chatwoot (REST), Cal.com (REST)

## Estrutura

```
apps/api/
├── core/
│   ├── agentic/           # Loop agêntico (loop.py, context.py, config.py)
│   ├── tools/             # Tool registry + builtins (crm, calendar, communication, content)
│   ├── llm_router.py      # Multi-provider routing com fallback
│   ├── database.py        # Async PostgreSQL
│   └── models_v2.py       # SQLAlchemy models
├── agents/                # 20+ agentes especializados (Agno)
│   ├── coordinator.py     # Roteador de intenção
│   ├── campaign_manager.py # Decomposição de goals
│   └── ...
├── orchestration/         # AgentOS (orquestração, human-loop, costs)
│   ├── agent_os.py        # Runtime principal
│   ├── human_loop.py      # Estado machine bot↔humano
│   └── cost_monitor.py    # Tracking de custos
├── tools/                 # Clients para APIs externas
│   ├── chatwoot.py, calendar.py, crm.py, whatsapp/
├── creative_lab/          # Creative Studio (copywriter + creative director)
├── config/directives/     # System prompts dos agentes em markdown
└── main.py

apps/web/                  # Frontend Next.js
```

## O Que Já Existe e Funciona

1. **Agentic Loop** (`core/agentic/loop.py`): Loop while com LLM→tools→repeat. Suporta timeout, cost limits, max turns, hooks, retry, streaming stub.
2. **Tool Registry** (`core/tools/registry.py`): Registry declarativo com JSON Schema, validação, idempotência, categorias.
3. **LLM Router** (`core/llm_router.py`): 4 providers, 3 tiers (fast/smart/creative), fallback automático, cost tracking.
4. **AgentOS** (`orchestration/agent_os.py`): Processa eventos, roteia para agentes, executa plans com subtasks paralelas, human-in-the-loop.
5. **Coordinator** (`agents/coordinator.py`): Keywords + LLM para roteamento de intenção.
6. **20+ Agentes Agno**: SDR, atendente, copywriter, creative director, instagram, follow-up, lead_qualifier, campaign_manager, etc.
7. **Tool Clients**: Chatwoot, Cal.com, Twenty CRM, Evolution API (parcialmente stubs).
8. **Creative Studio** (`creative_lab/`): Copywriter Elite + Creative Director.
9. **Webhook mapping** definido mas não implementado como endpoints.

## O Que Falta (Delta)

O delta está no prompt `/medflow-build`. Em resumo:
- Conectar tool clients às APIs reais (hoje parcialmente stubs)
- Implementar webhook receivers (FastAPI endpoints)
- Streaming real no agentic loop (SSE)
- Context compaction (prune mensagens antigas quando overflow)
- Subagent spawning isolado (contexto separado do pai)
- Gestor de Tráfego (Meta + Google Ads APIs)
- Frontend conectado a dados reais (hoje mockups)
- Testes de integração

## Padrões Obrigatórios

- Type hints em tudo
- Async/await para I/O
- Pydantic para validação
- Structlog para logging
- Commits atômicos
- Tests para cada módulo novo
- Docstrings descritivas
- Nunca hardcode secrets (use settings/env)

## Compliance

- **CFM**: Sem garantia de resultados, sem antes/depois sem autorização, sem preços públicos
- **LGPD**: Consentimento, minimização, transparência, eliminação quando solicitado

## Dois Perfis de Uso do SuperAgent (produto final)

1. **Superusers (agência)**: Time completo de marketing — copy, tráfego, social media, projetos, SDR, BI
2. **Clientes (clínicas)**: Secretária virtual + automações CRM↔Chatwoot↔Cal.com
