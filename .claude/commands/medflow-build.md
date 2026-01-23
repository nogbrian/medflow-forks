# Construir o MedFlow SuperAgent

Você é um engenheiro senior construindo o **MedFlow SuperAgent** — um agente autônomo multi-LLM equivalente ao Claude Code, mas para marketing médico. Este é um produto independente que roda em produção, atendendo consultórios médicos brasileiros via WhatsApp.

## ESTADO ATUAL DO CÓDIGO

Leia o `CLAUDE.md` na raiz para entender a estrutura completa. Em resumo, já existem:

- `apps/api/core/agentic/loop.py` → Agentic loop funcional (LLM→tools→repeat)
- `apps/api/core/agentic/context.py` → Context tracking (session, costs, turns)
- `apps/api/core/agentic/config.py` → Config (max_turns, timeout, cost limits)
- `apps/api/core/tools/registry.py` → Tool registry com JSON Schema
- `apps/api/core/tools/builtin/` → Tools builtins (crm, calendar, communication, content)
- `apps/api/core/llm_router.py` → Multi-provider (Anthropic, OpenAI, Google, xAI)
- `apps/api/orchestration/agent_os.py` → AgentOS (routing, execution plans, human-loop)
- `apps/api/agents/coordinator.py` → Roteador de intenção
- `apps/api/agents/` → 20+ agentes Agno (SDR, atendente, copywriter, etc.)
- `apps/api/tools/chatwoot.py`, `calendar.py`, `crm.py`, `whatsapp/` → Clients (parcialmente stubs)
- `apps/api/creative_lab/` → Creative Studio (NÃO tocar, apenas usar)

## SEU TRABALHO: FECHAR O DELTA

Analise o que já existe e implemente o que falta para tornar o superagente OPERACIONAL em produção. Execute fase por fase, commitando incrementalmente.

---

### FASE 1: Streaming Real no Agentic Loop

**Onde**: `apps/api/core/agentic/loop.py` método `run_streaming()`

O método existe mas faz fallback para non-streaming. Implemente streaming real:

1. Usar a API de streaming do provider (Anthropic `stream=True`, OpenAI stream, etc.)
2. Yield chunks de texto conforme chegam
3. Yield eventos de tool_call (`{"type": "tool_start", "name": "..."}`)
4. Yield eventos de tool_result (`{"type": "tool_result", "content": "..."}`)
5. Manter o loop: se houver tool_calls, executar e continuar streaming
6. Atualizar `core/llm_router.py` para suportar `chat_stream()` nos providers

**Endpoint SSE**: Criar `apps/api/routes/chat.py`:
```python
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        async for chunk in loop.run_streaming(...):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

### FASE 2: Context Compaction

**Onde**: `apps/api/core/agentic/compaction.py` (novo)

Quando o transcript excede 80% do context window do modelo:

1. **Prune**: Remover tool outputs antigos (manter últimos 40K tokens)
2. **Compact**: Usar modelo fast para resumir mensagens antigas em 1 mensagem
3. **Preserve**: Nunca remover system prompt, última mensagem do user, últimos 3 tool results

Inspiração: `opencode/packages/opencode/src/session/compaction.ts`

```python
class ContextCompactor:
    async def should_compact(self, messages: list, model: str) -> bool:
        token_count = estimate_tokens(messages)
        max_tokens = MODEL_CONTEXT_LIMITS[model]
        return token_count > max_tokens * 0.8

    async def compact(self, messages: list, llm_router) -> list:
        # 1. Separate protected messages (system, last user, recent tools)
        # 2. Summarize old messages with fast model
        # 3. Return compacted list
```

Integrar no loop principal (antes de cada `_call_llm`):
```python
if self.compactor and await self.compactor.should_compact(messages, config.model):
    messages = await self.compactor.compact(messages, self.llm)
```

---

### FASE 3: Subagent Spawning

**Onde**: `apps/api/core/agentic/subagent.py` (novo)

Permitir que um agente spawne subagentes com contexto isolado:

```python
class SubagentSpawner:
    def __init__(self, parent_loop: AgenticLoop):
        self.parent = parent_loop

    async def spawn(
        self,
        task: str,
        system_prompt: str,
        tools: list[str] | None = None,  # Subset do parent
        config: AgenticConfig | None = None,
        timeout: int = 120
    ) -> AgenticResult:
        # 1. Criar AgenticContext isolado (não polui pai)
        # 2. Filtrar tools disponíveis
        # 3. Executar loop com timeout
        # 4. Retornar resultado ao pai
```

Registrar como tool no registry para que agentes possam invocar subagentes:
```python
@tool
async def delegate_task(task: str, agent_type: str = "general") -> str:
    """Delegar subtarefa para um subagente especializado."""
    result = await spawner.spawn(task=task, ...)
    return result.final_response
```

---

### FASE 4: Webhook Receivers

**Onde**: `apps/api/webhooks/` (novo diretório)

Criar endpoints FastAPI que recebem webhooks e disparam o AgentOS:

```
apps/api/webhooks/
├── __init__.py
├── router.py          # APIRouter com todos os endpoints
├── chatwoot.py        # POST /webhooks/chatwoot
├── calcom.py          # POST /webhooks/calcom
├── twenty.py          # POST /webhooks/twenty
├── evolution.py       # POST /webhooks/evolution (WhatsApp)
└── signatures.py      # Validação de HMAC signatures
```

Cada webhook deve:
1. Validar signature (HMAC-SHA256)
2. Mapear payload → `IncomingEvent` (usar EventType do agent_os.py)
3. Chamar `agent_os.route_to_queue(event)` (async via Redis/arq)
4. Retornar 200 OK imediato

Mapeamento de eventos (já definido no agent_os.py):
```python
WEBHOOK_EVENT_MAP = {
    "message_created": EventType.WHATSAPP_MESSAGE,
    "conversation_status_changed": EventType.HUMAN_RESPONSE,
    "BOOKING_CREATED": EventType.APPOINTMENT_REQUEST,
    "BOOKING_CANCELLED": EventType.SCHEDULED_TASK,
    "lead.created": EventType.LEAD_QUALIFY,
    "messages.upsert": EventType.WHATSAPP_MESSAGE,
}
```

Registrar no `main.py`:
```python
from webhooks.router import router as webhooks_router
app.include_router(webhooks_router)
```

---

### FASE 5: Tool Clients Reais

Conectar os stubs em `apps/api/tools/` às APIs reais. Use httpx async.

#### Chatwoot (`tools/chatwoot.py`)
- API REST v2: `{CHATWOOT_URL}/api/v1/accounts/{account_id}/`
- Endpoints: contacts, conversations, messages, labels, agents
- Auth: `api_access_token` header
- Implementar: buscar_contato, criar_conversa, enviar_mensagem, transferir_para_agente, adicionar_labels

#### Cal.com (`tools/calendar.py`)
- API REST v2: `{CALCOM_URL}/api/v2/`
- Endpoints: availability, bookings, event-types, schedules
- Auth: API key header
- Implementar: verificar_disponibilidade, criar_booking, cancelar, reagendar, listar_bookings

#### Twenty CRM (`tools/crm.py`)
- API GraphQL: `{TWENTY_URL}/api`
- Queries: findManyPeople, findManyCompanies, findManyOpportunities
- Mutations: createPerson, updatePerson, createOpportunity, updateOpportunityStage
- Auth: Bearer token
- Implementar: buscar_lead, criar_lead, atualizar_lead, mover_pipeline, listar_leads

#### WhatsApp (`tools/whatsapp/`)
- Evolution API já está parcialmente implementada
- Completar: enviar_texto, enviar_midia, enviar_template, verificar_status_conexao
- Garantir integração bidirecional com webhook receiver (Fase 4)

---

### FASE 6: Gestor de Tráfego

**Onde**: `apps/api/agents/gestor_trafego.py` + `apps/api/tools/ads/`

Novo agente Agno com tools para Meta e Google Ads:

```
apps/api/tools/ads/
├── __init__.py
├── meta.py            # Meta Marketing API (Campaigns, AdSets, Ads, Audiences)
├── google.py          # Google Ads API (Campaigns, AdGroups, Keywords, Bids)
└── analytics.py       # Métricas unificadas (CPA, ROAS, CTR, CPM)
```

Tools do agente:
- `criar_campanha_meta(objetivo, publico, orcamento, criativos)` → campaign_id
- `criar_campanha_google(tipo, keywords, lances, anuncios)` → campaign_id
- `obter_metricas(campaign_id, periodo)` → {cpa, roas, ctr, cpm, spend, conversions}
- `otimizar_lance(campaign_id, estrategia)` → resultado
- `pausar_campanha(campaign_id, motivo)` → bool
- `criar_publico_lookalike(source_id, pais, percent)` → audience_id
- `relatorio_periodo(clinic_id, inicio, fim)` → relatório formatado

O agente deve entender estrutura TOF/MOF/BOF e sugerir otimizações baseado nas métricas.

System prompt: adicionar em `config/directives/gestor_trafego.md`

---

### FASE 7: Testes de Integração

**Onde**: `tests/`

```
tests/
├── unit/
│   ├── test_agentic_loop.py       # Loop com LLM mockado
│   ├── test_tool_registry.py      # Registry + validation
│   ├── test_context_compaction.py  # Compaction logic
│   ├── test_coordinator.py        # Routing decisions
│   └── test_subagent.py           # Spawning isolado
├── integration/
│   ├── test_chatwoot_client.py    # httpx mock ou VCR
│   ├── test_calcom_client.py      # httpx mock ou VCR
│   ├── test_crm_client.py         # httpx mock ou VCR
│   └── test_webhooks.py           # FastAPI TestClient
└── e2e/
    ├── test_novo_paciente.py      # msg→routing→agent→resposta→crm
    ├── test_agendamento.py        # msg→verificar→agendar→confirmar→crm
    └── test_campanha.py           # goal→decompose→execute→report
```

Use: pytest + pytest-asyncio + httpx + respx (para mocking HTTP) + factory_boy (fixtures)

---

### FASE 8: Frontend Conectado

**Onde**: `apps/web/`

Substituir mockups hardcoded por dados reais:

1. **API hooks** (TanStack Query):
   - `useLeads(filters)` → GET /api/leads
   - `useConversations(status)` → GET /api/conversations
   - `useBookings(period)` → GET /api/bookings
   - `usePlanStatus(planId)` → GET /api/plans/{id}

2. **Chat interface com streaming**:
   - Hook `useChatStream(sessionId)` → POST /chat/stream (SSE)
   - Mostrar tool executions em real-time (chips/badges)
   - Indicador de "agente pensando..." / "executando ferramenta X..."
   - Histórico de conversas persistido

3. **Pipeline Kanban**:
   - Conectar ao Twenty CRM via /api/leads
   - Drag & drop → PATCH /api/leads/{id}/stage
   - Otimistic updates

4. **Calendário**:
   - Conectar ao Cal.com via /api/bookings
   - Mostrar disponibilidade real
   - Criar/cancelar booking inline

5. **API Routes** (FastAPI):
   - `apps/api/routes/leads.py` → CRUD proxy para Twenty
   - `apps/api/routes/conversations.py` → Proxy para Chatwoot
   - `apps/api/routes/bookings.py` → Proxy para Cal.com
   - `apps/api/routes/plans.py` → Status de execution plans

---

## REGRAS DE EXECUÇÃO

1. **Comece pela Fase 1** — streaming é o que dá vida ao produto
2. **Leia o código existente antes de criar** — entenda patterns, imports, config
3. **Não reimplemente o que já existe** — especialmente Creative Studio e AgentOS
4. **Cada fase = 1+ commits atômicos** com mensagem descritiva em inglês
5. **Testes para cada módulo novo** — mínimo unit tests
6. **Se um stub já tem a interface certa**, implemente o body sem mudar a assinatura
7. **Use httpx.AsyncClient** para todos os HTTP clients
8. **Use settings (pydantic-settings, env vars)** para URLs, tokens, secrets
9. **Docstrings em tudo** — outro dev precisa entender sem ler o corpo
10. **Se travar em algo, pule para a próxima fase** e volte depois

## COMO VERIFICAR SE FUNCIONA

Para cada fase, o critério de "pronto" é:

- **Fase 1**: `pytest tests/unit/test_agentic_loop.py` passa + endpoint SSE responde
- **Fase 2**: `pytest tests/unit/test_context_compaction.py` passa + loop não explode com 200K tokens
- **Fase 3**: `pytest tests/unit/test_subagent.py` passa + subagente não polui contexto pai
- **Fase 4**: `pytest tests/integration/test_webhooks.py` passa + curl POST funciona
- **Fase 5**: `pytest tests/integration/test_*_client.py` passam + operações CRUD funcionam
- **Fase 6**: Agente responde a "crie uma campanha de captação" com estrutura coerente
- **Fase 7**: `pytest tests/` — tudo verde
- **Fase 8**: Frontend mostra dados reais (não mockados) ao abrir

## COMPLETION

Quando TODAS as fases estiverem implementadas com testes passando, emita exatamente:

<promise>MEDFLOW_SUPERAGENT_OPERATIONAL</promise>

Isso significa: o superagente recebe mensagens via webhook, roteia para o agente certo, executa com tools reais (Chatwoot, Cal.com, Twenty CRM), responde via WhatsApp, e o frontend mostra tudo em real-time via streaming.
