# MedFlow Sprint — Fase Específica

Execute uma sprint focada em uma fase específica do delta. Leia `CLAUDE.md` e `.claude/commands/medflow-build.md` para contexto completo.

## FASES

Diga qual fase executar. Exemplo: "Trabalhe na fase-1"

- **fase-1**: Streaming real no agentic loop + endpoint SSE
- **fase-2**: Context compaction (prune + compact quando overflow)
- **fase-3**: Subagent spawning com contexto isolado
- **fase-4**: Webhook receivers (Chatwoot, Cal.com, Twenty, Evolution)
- **fase-5**: Tool clients reais (httpx async → APIs externas)
- **fase-6**: Gestor de Tráfego (Meta + Google Ads agent + tools)
- **fase-7**: Testes (unit + integration + e2e)
- **fase-8**: Frontend conectado a dados reais

## REGRAS

1. Foque APENAS na fase indicada
2. Leia o código existente antes de criar
3. Commits atômicos a cada feature funcional
4. Testes para cada módulo novo
5. Se stub existe, implemente o body sem mudar assinatura
6. Use httpx.AsyncClient, pydantic-settings, structlog

## COMPLETION

Quando a fase estiver completa com testes passando:

<promise>SPRINT_COMPLETE</promise>
