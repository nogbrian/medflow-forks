# Plano de Integração: MedFlow + Clawdbot

> **Objetivo**: Testar 3 cenários de integração e definir a arquitetura final do "Claude Code para Marketing Médico"

---

## TL;DR - Fases do Projeto

| Fase | Duração | Objetivo |
|------|---------|----------|
| **0. Setup** | 1 dia | Instalar Clawdbot, conectar WhatsApp de teste |
| **1. Cenário B** | 3 dias | MedFlow como Skills do Clawdbot |
| **2. Cenário C** | 4 dias | Arquitetura Híbrida (Clawdbot + AgentOS) |
| **3. Cenário D** | 5 dias | Clawdbot faz tudo |
| **4. Decisão** | 1 dia | Avaliar e escolher arquitetura final |

**Total estimado**: 2 semanas de experimentação

---

## Fase 0: Setup do Ambiente

### 0.1 Instalação do Clawdbot

```bash
# Opção 1: NPM global
npm i -g clawdbot

# Opção 2: Curl (recomendado)
curl -fsSL https://clawd.bot/install.sh | bash

# Verificar instalação
clawdbot --version
```

### 0.2 Configuração Inicial

```bash
# Criar diretório de config
mkdir -p ~/.clawdbot

# Criar config básica
cat > ~/.clawdbot/clawdbot.json << 'EOF'
{
  "model": "claude-sonnet-4-20250514",
  "workspace": "medflow-test",
  "channels": {
    "whatsapp": {
      "enabled": true
    },
    "telegram": {
      "enabled": false
    }
  },
  "gateway": {
    "port": 18789,
    "host": "127.0.0.1"
  }
}
EOF
```

### 0.3 Conectar WhatsApp de Teste

```bash
# Iniciar Clawdbot
clawdbot start

# Vai gerar QR code para parear WhatsApp
# Use um número de TESTE, não o da clínica
```

### 0.4 Teste de Sanidade

1. Envie "Olá" para o WhatsApp pareado
2. Verifique se Claude responde
3. Teste um comando simples: "Que horas são?"

**Checkpoint**: Clawdbot respondendo via WhatsApp ✓

---

## Fase 1: Cenário B — MedFlow como Skills

> **Hipótese**: Transformar agentes MedFlow em skills do Clawdbot é rápido e funciona para casos simples.

### 1.1 Anatomia de um Skill Clawdbot

```typescript
// ~/.clawdbot/skills/medflow-agendamento.ts
import { Skill, Context } from 'clawdbot';

export default class AgendamentoSkill extends Skill {
  name = 'medflow-agendamento';
  description = 'Agenda consultas no Cal.com via MedFlow';

  triggers = [
    'agendar consulta',
    'marcar horário',
    'quero agendar'
  ];

  async execute(ctx: Context) {
    // Chamar API do MedFlow
    const response = await fetch('http://localhost:8000/api/v1/booking/slots', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: ctx.message,
        contact: ctx.sender,
      })
    });

    const data = await response.json();
    return ctx.reply(data.response);
  }
}
```

### 1.2 Skills a Criar (MVP)

| Skill | Agente MedFlow Original | Função |
|-------|------------------------|--------|
| `medflow-agendamento` | `agents/scheduler.py` | Agendar/remarcar consultas |
| `medflow-atendimento` | `agents/attendant.py` | Responder dúvidas gerais |
| `medflow-sdr` | `agents/sdr.py` | Qualificar leads |
| `medflow-followup` | `agents/follow_up.py` | Enviar lembretes |

### 1.3 Arquitetura Cenário B

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAWDBOT                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  WhatsApp   │  │  Telegram   │  │   WebChat   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                 ┌─────────────────┐                         │
│                 │  Clawdbot Loop  │  ← Claude como LLM      │
│                 │  (Orquestração) │                         │
│                 └────────┬────────┘                         │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         ▼                ▼                ▼                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Skill:    │  │  Skill:    │  │  Skill:    │            │
│  │ Agendamento│  │ Atendimento│  │    SDR     │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼───────────────┼───────────────┼────────────────────┘
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ Cal.com  │    │ Chatwoot │    │Twenty CRM│
   │   API    │    │   API    │    │   API    │
   └──────────┘    └──────────┘    └──────────┘
```

### 1.4 Implementação

```bash
# Estrutura de skills
mkdir -p ~/.clawdbot/skills/medflow

# Skills a criar:
# - ~/.clawdbot/skills/medflow/agendamento.ts
# - ~/.clawdbot/skills/medflow/atendimento.ts
# - ~/.clawdbot/skills/medflow/sdr.ts
# - ~/.clawdbot/skills/medflow/followup.ts
# - ~/.clawdbot/skills/medflow/crm.ts
```

### 1.5 Critérios de Sucesso Cenário B

- [ ] Skill de agendamento funciona end-to-end
- [ ] Skill consegue acessar Twenty CRM
- [ ] Conversa mantém contexto entre mensagens
- [ ] Compliance CFM é respeitado (sem promessas de resultado)
- [ ] Latência < 5s para resposta

### 1.6 Limitações Esperadas

- Menos controle sobre o agentic loop
- Dependência total do Clawdbot para orquestração
- Difícil implementar human-in-the-loop complexo
- Multi-agente (coordinator → specialist) pode ser limitado

---

## Fase 2: Cenário C — Arquitetura Híbrida

> **Hipótese**: Clawdbot cuida de canais + browser, MedFlow cuida de business logic.

### 2.1 Divisão de Responsabilidades

| Componente | Responsabilidade |
|------------|------------------|
| **Clawdbot** | Canais (WhatsApp, Telegram), Browser automation, Voice |
| **MedFlow AgentOS** | Orquestração, Routing de intenção, Human-loop, Compliance |
| **MedFlow Tools** | Twenty CRM, Cal.com, Chatwoot (data), Meta Ads |

### 2.2 Arquitetura Cenário C

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAWDBOT                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  WhatsApp   │  │  Browser    │  │   Voice     │         │
│  │  (Baileys)  │  │  (CDP)      │  │  (Eleven)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                 ┌─────────────────┐                         │
│                 │ Gateway WebSocket│                        │
│                 │  :18789         │                        │
│                 └────────┬────────┘                         │
└──────────────────────────┼──────────────────────────────────┘
                           │ WebSocket
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    MEDFLOW AGENTOS                           │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ Clawdbot Bridge │───▶│   Coordinator   │                 │
│  │  (WS Client)    │    │  (Intent Route) │                 │
│  └─────────────────┘    └────────┬────────┘                 │
│                                  │                           │
│         ┌────────────────────────┼────────────────────────┐  │
│         ▼                        ▼                        ▼  │
│  ┌────────────┐          ┌────────────┐          ┌──────────┐│
│  │ Attendant  │          │  Scheduler │          │   SDR    ││
│  │   Agent    │          │   Agent    │          │  Agent   ││
│  └─────┬──────┘          └─────┬──────┘          └────┬─────┘│
│        │                       │                      │      │
│        └───────────────────────┼──────────────────────┘      │
│                                ▼                             │
│                    ┌─────────────────────┐                   │
│                    │    Tool Registry    │                   │
│                    │ (CRM, Calendar, Ads)│                   │
│                    └─────────────────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Componente: Clawdbot Bridge

```python
# apps/api/bridges/clawdbot_bridge.py
import asyncio
import websockets
import json
from typing import Callable, Awaitable

class ClawdbotBridge:
    """
    Conecta MedFlow AgentOS ao Clawdbot Gateway.
    Recebe mensagens de canais e envia respostas.
    """

    def __init__(
        self,
        gateway_url: str = "ws://127.0.0.1:18789",
        on_message: Callable[[dict], Awaitable[str]] = None
    ):
        self.gateway_url = gateway_url
        self.on_message = on_message
        self.ws = None

    async def connect(self):
        """Estabelece conexão com Clawdbot Gateway."""
        self.ws = await websockets.connect(self.gateway_url)
        asyncio.create_task(self._listen())

    async def _listen(self):
        """Loop de escuta de mensagens."""
        async for raw in self.ws:
            msg = json.loads(raw)

            if msg.get("type") == "message":
                # Processar via AgentOS
                response = await self.on_message(msg)

                # Enviar resposta de volta
                await self.send_response(
                    channel=msg["channel"],
                    chat_id=msg["chat_id"],
                    text=response
                )

    async def send_response(self, channel: str, chat_id: str, text: str):
        """Envia resposta via Clawdbot."""
        await self.ws.send(json.dumps({
            "type": "send",
            "channel": channel,
            "chat_id": chat_id,
            "text": text
        }))

    async def request_browser_action(self, action: dict) -> dict:
        """Solicita ação de browser ao Clawdbot."""
        await self.ws.send(json.dumps({
            "type": "browser_action",
            **action
        }))
        # Aguardar resposta...
        response = await self.ws.recv()
        return json.loads(response)
```

### 2.4 Integração com AgentOS

```python
# apps/api/main.py (adicionar)
from bridges.clawdbot_bridge import ClawdbotBridge
from orchestration.agent_os import AgentOS

agent_os = AgentOS()
bridge = ClawdbotBridge(on_message=handle_clawdbot_message)

async def handle_clawdbot_message(msg: dict) -> str:
    """Processa mensagem vinda do Clawdbot via AgentOS."""

    # Converter formato Clawdbot → MedFlow
    event = {
        "type": "message",
        "source": f"clawdbot:{msg['channel']}",
        "contact": {
            "id": msg["sender_id"],
            "name": msg.get("sender_name"),
            "phone": msg.get("phone"),
        },
        "content": msg["text"],
        "metadata": {
            "clawdbot_chat_id": msg["chat_id"],
            "channel": msg["channel"],
        }
    }

    # Processar via AgentOS (coordinator → agent especializado)
    result = await agent_os.process_event(event)

    return result.response

@app.on_event("startup")
async def startup():
    await bridge.connect()
```

### 2.5 Critérios de Sucesso Cenário C

- [ ] Bridge conecta e recebe mensagens
- [ ] Coordinator roteia corretamente para agentes
- [ ] Respostas chegam de volta ao WhatsApp
- [ ] Browser automation funciona (ex: scraping de perfil)
- [ ] Human-in-the-loop funciona (transferir para humano)
- [ ] Latência < 3s end-to-end

### 2.6 Vantagens Esperadas

- Mantém controle total sobre business logic
- Compliance CFM implementado no AgentOS
- Multi-agente complexo (coordinator → specialists)
- Clawdbot cuida da infraestrutura "difícil" (WhatsApp, browser)

---

## Fase 3: Cenário D — Clawdbot Faz Tudo

> **Hipótese**: Migrar toda lógica para skills Clawdbot, usar apenas APIs externas.

### 3.1 Arquitetura Cenário D

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLAWDBOT                                │
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │WhatsApp │ │Telegram │ │ Discord │ │ Browser │ │  Voice  │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       └───────────┴───────────┼───────────┴───────────┘        │
│                               ▼                                 │
│                    ┌─────────────────────┐                      │
│                    │   Clawdbot Agent    │                      │
│                    │   (Claude Opus)     │                      │
│                    └──────────┬──────────┘                      │
│                               │                                 │
│    ┌──────────────────────────┼──────────────────────────┐     │
│    ▼              ▼           ▼           ▼              ▼     │
│ ┌──────┐    ┌──────────┐ ┌─────────┐ ┌─────────┐   ┌────────┐  │
│ │Memory│    │Coordinator│ │Marketing│ │Atendimento│ │Tráfego│  │
│ │Skill │    │  Skill   │ │  Skill  │ │  Skill  │   │ Skill │  │
│ └──────┘    └────┬─────┘ └────┬────┘ └────┬────┘   └───┬────┘  │
│                  │            │           │            │        │
│    ┌─────────────┴────────────┴───────────┴────────────┘       │
│    ▼                                                            │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │                    Tool Layer                            │    │
│ │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐    │    │
│ │  │Twenty   │ │ Cal.com │ │ Meta    │ │  Browser    │    │    │
│ │  │CRM API  │ │   API   │ │Ads API  │ │  Control    │    │    │
│ │  └─────────┘ └─────────┘ └─────────┘ └─────────────┘    │    │
│ └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

                    APIs Externas (Data Stores)
         ┌─────────────┬─────────────┬─────────────┐
         ▼             ▼             ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Twenty  │  │ Cal.com │  │Chatwoot │  │ Meta    │
    │   CRM   │  │         │  │ (logs)  │  │ Ads     │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

### 3.2 Skills Completos para Cenário D

#### 3.2.1 Coordinator Skill (Roteador de Intenção)

```typescript
// ~/.clawdbot/skills/medflow/coordinator.ts
import { Skill, Context, SkillRouter } from 'clawdbot';

export default class CoordinatorSkill extends Skill {
  name = 'medflow-coordinator';
  description = 'Roteia mensagens para o skill especializado correto';

  // Sempre executa primeiro
  priority = 100;

  private router = new SkillRouter([
    { patterns: ['agendar', 'marcar', 'consulta', 'horário'], skill: 'medflow-agendamento' },
    { patterns: ['preço', 'valor', 'quanto custa'], skill: 'medflow-atendimento' },
    { patterns: ['campanha', 'anúncio', 'tráfego', 'ads'], skill: 'medflow-trafego' },
    { patterns: ['post', 'conteúdo', 'instagram', 'reel'], skill: 'medflow-marketing' },
    { patterns: ['lead', 'interesse', 'quero saber'], skill: 'medflow-sdr' },
  ]);

  async execute(ctx: Context) {
    const intent = await this.classifyIntent(ctx.message);
    const targetSkill = this.router.route(intent);

    // Delegar para skill especializado
    return ctx.delegateTo(targetSkill);
  }

  private async classifyIntent(message: string): Promise<string> {
    // Pode usar Claude para classificação se patterns não bastarem
    const response = await ctx.llm.complete({
      prompt: `Classifique a intenção: "${message}"
      Opções: agendamento, atendimento, trafego, marketing, sdr, outro`,
      maxTokens: 10
    });
    return response.trim();
  }
}
```

#### 3.2.2 Atendimento Skill (Secretária Virtual)

```typescript
// ~/.clawdbot/skills/medflow/atendimento.ts
import { Skill, Context } from 'clawdbot';

export default class AtendimentoSkill extends Skill {
  name = 'medflow-atendimento';
  description = 'Secretária virtual para clínicas médicas';

  // System prompt com compliance CFM
  systemPrompt = `
Você é a secretária virtual de uma clínica médica.

REGRAS OBRIGATÓRIAS (CFM):
- NUNCA prometa resultados de procedimentos
- NUNCA mostre fotos antes/depois sem autorização
- NUNCA divulgue preços publicamente (apenas em conversa privada)
- SEMPRE sugira agendamento para discussão de valores

PERSONALIDADE:
- Profissional mas acolhedora
- Respostas concisas (máx 3 parágrafos)
- Use emojis com moderação

CAPACIDADES:
- Responder dúvidas sobre procedimentos
- Agendar consultas (use tool: calendar)
- Consultar histórico do paciente (use tool: crm)
- Enviar lembretes (use tool: notification)
`;

  tools = ['calendar', 'crm', 'notification'];

  async execute(ctx: Context) {
    // Buscar contexto do paciente no CRM
    const patient = await ctx.tools.crm.getContact(ctx.sender.phone);

    // Adicionar contexto ao prompt
    const contextualPrompt = patient
      ? `Paciente: ${patient.name}, Última consulta: ${patient.lastVisit}`
      : 'Novo contato, ainda não cadastrado.';

    // Responder via Claude com contexto
    return ctx.llm.chat({
      system: this.systemPrompt,
      context: contextualPrompt,
      message: ctx.message,
      tools: this.tools
    });
  }
}
```

#### 3.2.3 Marketing Skill (Copywriter + Social Media)

```typescript
// ~/.clawdbot/skills/medflow/marketing.ts
import { Skill, Context } from 'clawdbot';

export default class MarketingSkill extends Skill {
  name = 'medflow-marketing';
  description = 'Cria conteúdo para redes sociais de clínicas';

  systemPrompt = `
Você é um copywriter especializado em marketing médico.

EXPERTISE:
- Posts para Instagram (carrossel, reels, stories)
- Legendas persuasivas com CTAs
- Hooks que capturam atenção
- Compliance CFM/LGPD

FORMATO DE ENTREGA:
Sempre entregue em formato estruturado:
1. HOOK (primeira linha que aparece)
2. CORPO (conteúdo educativo)
3. CTA (chamada para ação)
4. HASHTAGS (5-10 relevantes)
`;

  tools = ['browser', 'canvas', 'file'];

  async execute(ctx: Context) {
    const task = await this.parseMarketingTask(ctx.message);

    switch (task.type) {
      case 'post':
        return this.createPost(ctx, task);
      case 'carrossel':
        return this.createCarousel(ctx, task);
      case 'reel_script':
        return this.createReelScript(ctx, task);
      case 'research':
        return this.researchTrends(ctx, task);
    }
  }

  private async createPost(ctx: Context, task: any) {
    // Gerar copy
    const copy = await ctx.llm.chat({
      system: this.systemPrompt,
      message: `Crie um post sobre: ${task.topic}
      Tom: ${task.tone || 'educativo'}
      Objetivo: ${task.goal || 'engajamento'}`
    });

    return copy;
  }

  private async researchTrends(ctx: Context, task: any) {
    // Usar browser para pesquisar trends
    const trends = await ctx.tools.browser.search(`${task.niche} trends instagram 2025`);
    return ctx.llm.summarize(trends, 'Liste as 5 principais tendências');
  }
}
```

#### 3.2.4 Tráfego Skill (Gestor de Ads)

```typescript
// ~/.clawdbot/skills/medflow/trafego.ts
import { Skill, Context } from 'clawdbot';

export default class TrafegoSkill extends Skill {
  name = 'medflow-trafego';
  description = 'Gerencia campanhas de Meta Ads e Google Ads';

  tools = ['meta_ads', 'google_ads', 'browser', 'analytics'];

  systemPrompt = `
Você é um gestor de tráfego pago especializado em clínicas médicas.

CAPACIDADES:
- Criar campanhas no Meta Ads
- Analisar métricas (CTR, CPC, ROAS)
- Sugerir otimizações
- Criar públicos lookalike

COMPLIANCE:
- Nunca prometer resultados específicos
- Ads de saúde precisam de disclaimers
- Seguir políticas do Meta para healthcare
`;

  async execute(ctx: Context) {
    const task = await this.parseTrafegoTask(ctx.message);

    switch (task.type) {
      case 'report':
        return this.generateReport(ctx, task);
      case 'create_campaign':
        return this.createCampaign(ctx, task);
      case 'optimize':
        return this.suggestOptimizations(ctx, task);
      case 'audience':
        return this.createAudience(ctx, task);
    }
  }

  private async generateReport(ctx: Context, task: any) {
    // Buscar dados das APIs
    const metaData = await ctx.tools.meta_ads.getInsights({
      dateRange: task.period || 'last_7_days',
      metrics: ['spend', 'impressions', 'clicks', 'conversions']
    });

    // Gerar relatório via Claude
    return ctx.llm.chat({
      system: this.systemPrompt,
      message: `Analise estas métricas e gere um relatório executivo:
      ${JSON.stringify(metaData, null, 2)}`
    });
  }
}
```

#### 3.2.5 CRM Tool (Twenty API)

```typescript
// ~/.clawdbot/tools/twenty-crm.ts
import { Tool } from 'clawdbot';

export default class TwentyCRMTool extends Tool {
  name = 'crm';
  description = 'Acessa e manipula dados no Twenty CRM';

  private baseUrl = process.env.TWENTY_API_URL || 'http://localhost:3000';
  private apiKey = process.env.TWENTY_API_KEY;

  schema = {
    getContact: {
      description: 'Busca contato por telefone ou email',
      params: {
        phone: { type: 'string', optional: true },
        email: { type: 'string', optional: true }
      }
    },
    createContact: {
      description: 'Cria novo contato no CRM',
      params: {
        name: { type: 'string', required: true },
        phone: { type: 'string' },
        email: { type: 'string' },
        source: { type: 'string' }
      }
    },
    addNote: {
      description: 'Adiciona nota a um contato',
      params: {
        contactId: { type: 'string', required: true },
        note: { type: 'string', required: true }
      }
    },
    updateStage: {
      description: 'Atualiza estágio do lead no funil',
      params: {
        contactId: { type: 'string', required: true },
        stage: { type: 'string', enum: ['lead', 'qualified', 'scheduled', 'attended', 'converted'] }
      }
    }
  };

  async getContact(params: { phone?: string; email?: string }) {
    const query = `
      query GetPerson($filter: PersonFilterInput) {
        people(filter: $filter, first: 1) {
          edges {
            node {
              id
              name { firstName lastName }
              emails { primaryEmail }
              phones { primaryPhoneNumber }
              createdAt
            }
          }
        }
      }
    `;

    const filter = params.phone
      ? { phones: { primaryPhoneNumber: { eq: params.phone } } }
      : { emails: { primaryEmail: { eq: params.email } } };

    const response = await this.graphql(query, { filter });
    return response.data.people.edges[0]?.node || null;
  }

  async createContact(params: any) {
    const mutation = `
      mutation CreatePerson($input: PersonCreateInput!) {
        createPerson(data: $input) {
          id
          name { firstName lastName }
        }
      }
    `;

    const [firstName, ...rest] = params.name.split(' ');
    const lastName = rest.join(' ');

    const input = {
      name: { firstName, lastName },
      phones: { primaryPhoneNumber: params.phone },
      emails: { primaryEmail: params.email }
    };

    const response = await this.graphql(mutation, { input });
    return response.data.createPerson;
  }

  private async graphql(query: string, variables: any) {
    const response = await fetch(`${this.baseUrl}/graphql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({ query, variables })
    });
    return response.json();
  }
}
```

#### 3.2.6 Calendar Tool (Cal.com API)

```typescript
// ~/.clawdbot/tools/calcom.ts
import { Tool } from 'clawdbot';

export default class CalcomTool extends Tool {
  name = 'calendar';
  description = 'Gerencia agendamentos no Cal.com';

  private baseUrl = process.env.CALCOM_API_URL || 'https://api.cal.com/v1';
  private apiKey = process.env.CALCOM_API_KEY;

  schema = {
    getAvailability: {
      description: 'Lista horários disponíveis',
      params: {
        eventTypeId: { type: 'number', required: true },
        startDate: { type: 'string', format: 'date' },
        endDate: { type: 'string', format: 'date' }
      }
    },
    createBooking: {
      description: 'Agenda uma consulta',
      params: {
        eventTypeId: { type: 'number', required: true },
        start: { type: 'string', format: 'datetime', required: true },
        name: { type: 'string', required: true },
        email: { type: 'string', required: true },
        phone: { type: 'string' },
        notes: { type: 'string' }
      }
    },
    cancelBooking: {
      description: 'Cancela um agendamento',
      params: {
        bookingId: { type: 'number', required: true },
        reason: { type: 'string' }
      }
    }
  };

  async getAvailability(params: any) {
    const { eventTypeId, startDate, endDate } = params;

    const response = await fetch(
      `${this.baseUrl}/availability?eventTypeId=${eventTypeId}&startTime=${startDate}&endTime=${endDate}`,
      { headers: { 'Authorization': `Bearer ${this.apiKey}` } }
    );

    const data = await response.json();

    // Formatar para resposta amigável
    return data.slots.map((slot: any) => ({
      date: new Date(slot.time).toLocaleDateString('pt-BR'),
      time: new Date(slot.time).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      available: slot.available
    }));
  }

  async createBooking(params: any) {
    const response = await fetch(`${this.baseUrl}/bookings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        eventTypeId: params.eventTypeId,
        start: params.start,
        responses: {
          name: params.name,
          email: params.email,
          phone: params.phone,
          notes: params.notes
        }
      })
    });

    return response.json();
  }
}
```

### 3.3 Memory e Contexto Persistente

```typescript
// ~/.clawdbot/skills/medflow/memory.ts
import { Skill, Context, Memory } from 'clawdbot';

export default class MemorySkill extends Skill {
  name = 'medflow-memory';
  description = 'Gerencia memória persistente de pacientes e contexto';

  // Executa em background para todas conversas
  background = true;

  async onMessage(ctx: Context) {
    const memory = ctx.memory;

    // Atualizar contexto do paciente
    await memory.set(`patient:${ctx.sender.phone}`, {
      lastMessage: ctx.message,
      lastInteraction: new Date().toISOString(),
      conversationCount: (await memory.get(`patient:${ctx.sender.phone}`))?.conversationCount + 1 || 1
    });

    // Extrair e salvar preferências mencionadas
    const preferences = await this.extractPreferences(ctx.message);
    if (preferences.length > 0) {
      await memory.append(`patient:${ctx.sender.phone}:preferences`, preferences);
    }
  }

  private async extractPreferences(message: string): Promise<string[]> {
    // Usar Claude para extrair preferências
    const response = await ctx.llm.complete({
      prompt: `Extraia preferências mencionadas nesta mensagem (horários, médicos, procedimentos):
      "${message}"
      Retorne como JSON array ou [] se nenhuma.`,
      maxTokens: 100
    });

    try {
      return JSON.parse(response);
    } catch {
      return [];
    }
  }
}
```

### 3.4 Critérios de Sucesso Cenário D

- [ ] Todos os skills funcionam standalone
- [ ] Coordinator roteia corretamente 90%+ das mensagens
- [ ] CRM tool cria/atualiza contatos
- [ ] Calendar tool agenda consultas
- [ ] Marketing skill gera posts utilizáveis
- [ ] Memory persiste entre sessões
- [ ] Compliance CFM respeitado em todas respostas
- [ ] Latência < 5s para respostas simples

### 3.5 O Que Acontece com MedFlow Backend?

No Cenário D, o backend MedFlow (FastAPI) se torna opcional ou mínimo:

| Componente | Destino |
|------------|---------|
| `core/agentic/` | Substituído pelo Clawdbot loop |
| `agents/` | Migrados para Clawdbot skills |
| `tools/` | Migrados para Clawdbot tools |
| `orchestration/` | Substituído pelo Clawdbot |
| `config/directives/` | Movidos para systemPrompt dos skills |

**Manter apenas**:
- Endpoints de webhook para serviços externos (se necessário)
- Dashboard frontend (Next.js) para visualização
- Banco de dados para histórico (ou usar Clawdbot memory)

---

## Fase 4: Avaliação e Decisão

### 4.1 Matriz de Comparação

| Critério | Cenário B | Cenário C | Cenário D |
|----------|-----------|-----------|-----------|
| **Velocidade de implementação** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Controle sobre lógica** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Manutenção futura** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Escalabilidade** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Dependência externa** | Alta | Média | Alta |
| **Compliance CFM** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Multi-clínica** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 4.2 Perguntas para Decisão Final

1. **Controle é crítico?** → Cenário C
2. **Velocidade é prioridade?** → Cenário B
3. **Simplicidade de stack?** → Cenário D
4. **Multi-tenant complexo?** → Cenário C
5. **Uma clínica apenas?** → Cenário D

### 4.3 Recomendação Inicial

**Começar com Cenário B** para validar rapidamente, depois **migrar para C ou D** baseado nos aprendizados:

```
Semana 1: Cenário B (validar Clawdbot + skills simples)
    ↓
Semana 2: Se ok → Cenário D (migrar tudo)
    ↓
    ou
    ↓
Semana 2: Se precisar mais controle → Cenário C (híbrido)
```

---

## Checklist de Execução

### Fase 0: Setup
- [ ] Instalar Clawdbot
- [ ] Criar config básica
- [ ] Parear WhatsApp de teste
- [ ] Testar resposta básica

### Fase 1: Cenário B
- [ ] Criar skill `medflow-atendimento`
- [ ] Criar skill `medflow-agendamento`
- [ ] Testar com mensagens reais
- [ ] Avaliar limitações

### Fase 2: Cenário C
- [ ] Criar ClawdbotBridge
- [ ] Integrar com AgentOS
- [ ] Testar routing de intenção
- [ ] Testar human-in-the-loop

### Fase 3: Cenário D
- [ ] Migrar todos skills
- [ ] Criar tools (CRM, Calendar)
- [ ] Implementar memory
- [ ] Testar end-to-end completo

### Fase 4: Decisão
- [ ] Documentar aprendizados
- [ ] Comparar métricas
- [ ] Escolher arquitetura final
- [ ] Planejar migração de produção

---

## Comandos Rápidos

```bash
# Instalar Clawdbot
npm i -g clawdbot

# Iniciar
clawdbot start

# Ver logs
clawdbot logs -f

# Listar skills
clawdbot skills list

# Instalar skill
clawdbot skills add ./skills/medflow-atendimento.ts

# Testar skill
clawdbot skills test medflow-atendimento "Quero agendar uma consulta"

# Conectar WhatsApp
clawdbot channel connect whatsapp

# Ver status
clawdbot status
```

---

## Recursos

- [Clawdbot GitHub](https://github.com/clawdbot/clawdbot)
- [Clawdbot Docs](https://clawd.bot/docs)
- [Clawdbot Skills API](https://clawd.bot/docs/skills)
- [Twenty CRM GraphQL](https://docs.twenty.com/api)
- [Cal.com API](https://cal.com/docs/api)

---

*Documento criado em: 2025-01-25*
*Última atualização: 2025-01-25*
