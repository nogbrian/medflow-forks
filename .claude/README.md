# MedFlow — Setup para Claude Code (Ralph Loop)

## O Que É

Configuração de Claude Code + ralph-loop para que ele construa autonomamente o **MedFlow SuperAgent** — um produto independente (multi-LLM, Agno Framework) que é o equivalente do Claude Code para marketing médico.

O Claude Code é o **construtor**. O SuperAgent é o **produto**.

## Arquitetura

```
.claude/
├── commands/
│   ├── medflow-build.md     # Prompt: construir tudo (8 fases)
│   ├── medflow-sprint.md    # Prompt: uma fase por vez
│   └── medflow-atender.md   # Prompt: simular atendimento
├── hooks/
│   └── stop-hook.sh         # Ralph loop: re-injeta prompt até promise
├── scripts/
│   └── start-medflow-loop.sh # Setup do loop autônomo
├── settings.json             # Permissões do Claude Code
└── README.md                 # ← Você está aqui

CLAUDE.md (raiz)              # Contexto do projeto para o Claude Code
```

## Como Usar

### Build Completo (loop autônomo)
```bash
cd medflow
./.claude/scripts/start-medflow-loop.sh medflow-build --max-iterations 100 --promise "MEDFLOW_SUPERAGENT_OPERATIONAL"
claude
```

O Claude Code vai iterar fase por fase até emitir a promise de completion.

### Sprint Focada
```bash
./.claude/scripts/start-medflow-loop.sh medflow-sprint --max-iterations 20 --promise "SPRINT_COMPLETE"
claude
# Dentro do Claude Code: "Trabalhe na fase-4"
```

### Uso Livre (sem loop)
```bash
claude
# O CLAUDE.md já dá todo o contexto. Peça o que quiser:
# "Implemente o webhook receiver para Chatwoot"
# "Adicione streaming ao agentic loop"
```

## O Que o Claude Code Vai Construir

O produto final é um superagente que:

1. Recebe mensagens via webhook (WhatsApp, Instagram, CRM events)
2. Roteia para o agente certo (Coordinator → SDR/Scheduler/Support/etc.)
3. Executa com tools reais (Chatwoot, Cal.com, Twenty CRM, Meta Ads, Google Ads)
4. Responde via WhatsApp/Chatwoot
5. Mostra tudo em real-time no frontend (SSE streaming)
6. Gerencia custos, human-in-the-loop, e context overflow

## Fases do Build

| Fase | O Que | Onde |
|------|-------|------|
| 1 | Streaming real no agentic loop | `core/agentic/loop.py` + `routes/chat.py` |
| 2 | Context compaction | `core/agentic/compaction.py` |
| 3 | Subagent spawning | `core/agentic/subagent.py` |
| 4 | Webhook receivers | `webhooks/` |
| 5 | Tool clients reais | `tools/chatwoot.py`, `calendar.py`, `crm.py` |
| 6 | Gestor de Tráfego | `agents/gestor_trafego.py` + `tools/ads/` |
| 7 | Testes | `tests/` |
| 8 | Frontend conectado | `apps/web/` |

## Cancelar Loop
```bash
rm .claude/ralph-loop.local.md
```
