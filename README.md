# MedFlow Forks

> **Plataforma Unificada de Growth para Clínicas Médicas**
>
> Integração white-label de Twenty CRM, Cal.com e Chatwoot com orquestração de agentes de IA.

---

## O Que É

MedFlow Forks é uma plataforma que unifica três poderosas ferramentas open-source como white-labels sob uma única interface e identidade visual:

| Serviço | Função | Fork |
|---------|--------|------|
| **Twenty CRM** | Gestão de contatos e pipeline de vendas | White-label completo |
| **Cal.com** | Agendamento de consultas e disponibilidade | White-label completo |
| **Chatwoot** | Atendimento omnichannel (WhatsApp, Instagram, Chat) | White-label completo |

### Diferencial: Funções Agênticas

O grande diferencial do MedFlow são os **agentes de IA** que orquestram tarefas complexas entre os três serviços:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENTE COORDENADOR                                │
│   Recebe objetivos complexos e delega para agentes especializados        │
└─────────────────────────────────────────────────────────────────────────┘
         │              │              │              │              │
         ▼              ▼              ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
    │RESEARCHER│   │COPYWRITER│   │ DESIGNER│   │   SDR   │   │ SUPPORT │
    │         │   │         │   │         │   │         │   │         │
    │Pesquisa │   │ Cria    │   │ Gera    │   │Qualifica│   │Atende   │
    │tendências│   │ copies  │   │ artes   │   │ leads   │   │pacientes│
    └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

**Exemplos de automações:**

1. **Lead entra pelo WhatsApp** → Agente SDR qualifica → Cria contato no Twenty → Agenda consulta no Cal.com
2. **Paciente marca consulta** → Agente Support envia confirmação → Cria oportunidade no CRM
3. **Marketing solicita conteúdo** → Researcher analisa tendências → Copywriter cria posts → Designer gera artes

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FRONTEND UNIFICADO (Next.js)                         │
│           Design System Industrial | Multi-tenant | SSO                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                            │
│    /crm/* → Twenty  │  /agenda/* → Cal.com  │  /inbox/* → Chatwoot      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER (FastAPI)                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐ │
│  │   Auth    │  │  Clinics  │  │  Agents   │  │    Creative Lab       │ │
│  │  (SSO)    │  │  (Multi-  │  │   (AI     │  │   (AI Content)        │ │
│  │           │  │  Tenant)  │  │ Orchestr) │  │                       │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────────────────┘ │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐ │
│  │  Webhooks │  │   Sync    │  │  Branding │  │     Analytics         │ │
│  │ (Unified) │  │ (Bidirec) │  │ (Dynamic) │  │    (Unified)          │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   TWENTY CRM     │     │    CAL.COM       │     │    CHATWOOT      │
│   (White-label)  │     │   (White-label)  │     │   (White-label)  │
│                  │     │                  │     │                  │
│  • Contacts      │     │  • Scheduling    │     │  • WhatsApp      │
│  • Companies     │     │  • Availability  │     │  • Instagram     │
│  • Opportunities │     │  • Teams         │     │  • Live Chat     │
│  • Pipelines     │     │  • Integrations  │     │  • AI Chatbot    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
                    ┌──────────────────────────────┐
                    │    PostgreSQL + Redis         │
                    │  (Shared Infrastructure)      │
                    └──────────────────────────────┘
```

---

## Multi-Tenancy

```
AGENCY (Superuser - Agência de Marketing)
│
├── CLINIC A (Clínica Dermatológica)
│   ├── Twenty Workspace (contatos, leads, pipeline)
│   ├── Cal.com Team (médicos, horários, consultas)
│   ├── Chatwoot Inbox (WhatsApp da clínica)
│   └── Users (recepcionistas, médicos, admin)
│
├── CLINIC B (Clínica de Estética)
│   ├── Twenty Workspace
│   ├── Cal.com Team
│   ├── Chatwoot Inbox
│   └── Users
│
└── Agency Users (acesso a todas as clínicas)
```

---

## Agentes de IA

### Coordinator (Orquestrador)

Recebe objetivos de alto nível e coordena múltiplos agentes:

```python
# Exemplo de goal
{
    "goal": "Criar campanha de lançamento do novo procedimento de harmonização facial",
    "context": {
        "clinic_id": "clinic_a",
        "budget": "R$ 5.000",
        "deadline": "2026-02-01"
    }
}

# Coordinator delega para:
# 1. Researcher → pesquisa tendências de harmonização
# 2. Copywriter → cria posts e legendas
# 3. Designer → gera imagens e carrosséis
# 4. SDR → prepara script de qualificação
```

### Agentes Especializados

| Agente | Modelo | Função | Integração |
|--------|--------|--------|------------|
| **Researcher** | Claude 4.5 Opus | Pesquisa tendências, análise de concorrência, insights de mercado | Web Search, Twenty (notas) |
| **Copywriter** | Claude 4.5 Sonnet | Copies para redes sociais, emails, scripts de vendas | Twenty (templates) |
| **Designer** | GPT-5.2 + DALL-E 4 | Geração de imagens, adaptação de artes, carrosséis | Storage, Creative Lab |
| **SDR** | Claude 4.5 Sonnet | Qualificação de leads, agendamento automático | Twenty, Cal.com, Chatwoot |
| **Support** | Claude 4.5 Haiku | Atendimento ao paciente, FAQ, triagem | Chatwoot, Cal.com |

---

## Design System Industrial

Todos os white-labels seguem o **Design System Industrial** - uma linguagem visual inspirada em design Suíço/Industrial:

### Tokens

```css
/* Cores */
--paper: #F2F0E9;      /* Background principal */
--ink: #111111;        /* Texto principal */
--graphite: #000000;   /* Bordas e elementos pesados */
--accent-orange: #F24E1E;  /* Ação primária, alertas */
--accent-blue: #0047AB;    /* Links, informação */
--steel: #666666;      /* Texto secundário */

/* Tipografia */
--font-display: "Inter Tight", sans-serif;  /* Headlines */
--font-mono: "JetBrains Mono", monospace;   /* Dados, métricas */

/* Sombras */
--shadow-hard: 4px 4px 0px 0px #000000;
--shadow-hard-orange: 4px 4px 0px 0px #F24E1E;

/* Bordas */
--border-width: 2px;
--border-radius: 0;  /* SEM border-radius */
```

### Princípios

1. **Brutalismo Funcional** - Estrutura exposta, sem decoração desnecessária
2. **Hard Shadows** - Sombras sólidas de 4px, sem blur
3. **Sem Border-Radius** - Todos os elementos são retangulares
4. **Tipografia Mono** - Dados e métricas sempre em monospace
5. **Grid Visível** - Estrutura dividida com bordas aparentes

---

## Quick Start

### 1. Clone e Configure

```bash
git clone https://github.com/seu-usuario/medflow-forks.git
cd medflow-forks
cp .env.example .env
# Edite .env com suas credenciais
```

### 2. Inicie os Serviços

```bash
docker-compose up -d
```

### 3. Acesse

| Serviço | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Twenty CRM | http://localhost:3000/crm |
| Cal.com | http://localhost:3000/agenda |
| Chatwoot | http://localhost:3000/inbox |
| API Docs | http://localhost:8000/docs |

---

## API Endpoints

### Autenticação

```bash
POST /api/auth/login        # Login SSO
GET  /api/auth/me           # Usuário atual
POST /api/auth/refresh      # Refresh token
```

### Clínicas (Multi-tenant)

```bash
GET  /api/clinics           # Listar clínicas
POST /api/clinics           # Criar clínica (superuser)
GET  /api/clinics/{id}      # Detalhes da clínica
PUT  /api/clinics/{id}      # Atualizar clínica
```

### Agentes (IA)

```bash
POST /api/agents/goal       # Enviar objetivo complexo
POST /api/agents/workflow   # Executar workflow específico
POST /api/agents/message    # Processar mensagem individual
GET  /api/agents/available  # Listar agentes disponíveis
GET  /api/agents/status/{id}# Status de execução
```

### Creative Lab

```bash
POST /api/creative-lab/chat    # Chat com Creative Director
POST /api/creative-lab/image   # Gerar imagem
POST /api/creative-lab/copy    # Gerar copy
POST /api/creative-lab/brief   # Criar brief de campanha
```

### Sync (Webhooks)

```bash
POST /api/webhooks/twenty      # Webhook do Twenty
POST /api/webhooks/calcom      # Webhook do Cal.com
POST /api/webhooks/chatwoot    # Webhook do Chatwoot
GET  /api/sync/status          # Status de sincronização
```

---

## Configuração de White-Label

### Branding por Agency

```json
{
  "agency_id": "agency_001",
  "branding": {
    "name": "MedGrowth",
    "logo_url": "https://cdn.../logo.svg",
    "favicon_url": "https://cdn.../favicon.ico",
    "colors": {
      "primary": "#F24E1E",
      "secondary": "#0047AB",
      "background": "#F2F0E9"
    },
    "fonts": {
      "display": "Inter Tight",
      "mono": "JetBrains Mono"
    },
    "domain": "app.medgrowth.com.br"
  }
}
```

### Injeção de Temas nos Forks

Os temas são injetados via CSS custom properties:

```bash
customizations/
├── twenty/
│   └── theme/
│       ├── industrial.css      # Overrides de CSS
│       └── tailwind.config.ts  # Extensão do Tailwind
├── calcom/
│   └── theme/
│       ├── industrial.css
│       └── tailwind.config.ts
└── chatwoot/
    └── theme/
        ├── industrial.css
        └── tailwind.config.ts
```

---

## Deploy (Produção)

### Requisitos

- VPS com 8GB+ RAM (Hostinger KVM8 recomendado)
- Docker & Docker Compose
- Domínio com DNS configurado
- SSL (Let's Encrypt via Traefik)

### Setup

```bash
# 1. SSH no servidor
ssh root@seu-servidor

# 2. Clone
git clone https://github.com/seu-usuario/medflow-forks.git
cd medflow-forks

# 3. Configure
cp .env.example .env
nano .env  # Configure todas as variáveis

# 4. Inicie
docker-compose -f docker-compose.prod.yml up -d

# 5. Verifique
docker-compose logs -f
```

---

## Roadmap

- [x] Integração Twenty CRM
- [x] Integração Cal.com
- [x] Integração Chatwoot
- [x] Multi-tenancy (Agency → Clinic → User)
- [x] Design System Industrial
- [x] Agentes de IA (Coordinator, Researcher, Copywriter, SDR, Support)
- [x] Creative Lab
- [ ] SSO unificado entre os três serviços
- [ ] Dashboard de métricas unificado
- [ ] Mobile app (React Native)
- [ ] Marketplace de templates de automação

---

## Licença

Proprietário - Todos os direitos reservados.

---

<p align="center">
  <strong>MedFlow Forks</strong><br>
  Unificando CRM, Agendamento e Atendimento com Inteligência Artificial
</p>
