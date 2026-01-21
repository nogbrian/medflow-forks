# MedFlow Forks

> Plataforma unificada de growth para médicos integrando Twenty CRM, Cal.com e Chatwoot.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                    │
│    /crm/* → Twenty  │  /agenda/* → Cal.com  │  /inbox/* → Chatwoot│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Layer (FastAPI)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐ │
│  │  Auth   │  │ Clinics │  │ Agents  │  │   Creative Lab      │ │
│  │ Multi-  │  │ (Multi- │  │  (AI    │  │   (AI Content       │ │
│  │ Tenant  │  │ Tenant) │  │Orchestr)│  │   Creation)         │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│   Twenty     │          │   Cal.com    │          │   Chatwoot   │
│    CRM       │          │  Scheduling  │          │   Messaging  │
└──────────────┘          └──────────────┘          └──────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
                    ┌──────────────────────────────┐
                    │    PostgreSQL + Redis         │
                    │  (Shared Infrastructure)      │
                    └──────────────────────────────┘
```

## Multi-Tenancy

```
Agency (Superuser)
├── Clinic A
│   ├── CRM Workspace (Twenty)
│   ├── Calendar Team (Cal.com)
│   ├── Inbox (Chatwoot)
│   └── Users (Clinic Staff)
├── Clinic B
│   └── ...
└── Agency Users (Can access all clinics)
```

## Quick Start

### 1. Clone e Configure

```bash
git clone https://github.com/seu-usuario/medflow-forks.git
cd medflow-forks
cp .env.example .env
# Edit .env with your secrets
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Access

- **Integration API**: http://localhost/api/docs
- **Twenty CRM**: http://localhost/crm/
- **Cal.com**: http://localhost/agenda/
- **Chatwoot**: http://localhost/inbox/

## Services

### Twenty CRM
- Contact management
- Pipeline/opportunities
- Company management
- Email sync

### Cal.com
- Appointment scheduling
- Availability management
- Team calendars
- Video conferencing

### Chatwoot
- WhatsApp integration
- Instagram DM
- Live chat widget
- AI chatbot support

### Integration Layer
- Multi-tenant authentication
- AI agents (content creation, lead qualification)
- Creative Studio
- Cross-service synchronization

## AI Agents

| Agent | Description |
|-------|-------------|
| `researcher` | Pesquisa tendências e virais |
| `copywriter` | Cria copies para redes sociais |
| `designer` | Gera imagens e artes |
| `sdr` | Qualifica leads e agenda reuniões |
| `support` | Atendimento ao paciente |

## API Endpoints

### Auth
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Current user
- `POST /api/auth/change-password` - Change password

### Clinics
- `GET /api/clinics` - List clinics
- `POST /api/clinics` - Create clinic (superuser)
- `GET /api/clinics/{id}` - Get clinic
- `PUT /api/clinics/{id}` - Update clinic

### Agents
- `POST /api/agents/goal` - Handle complex goal
- `POST /api/agents/workflow` - Run workflow
- `POST /api/agents/message` - Process message
- `GET /api/agents/available` - List available agents

### Creative Lab
- `POST /api/creative-lab/chat` - Chat with Creative Director
- `POST /api/creative-lab/image` - Generate image
- `POST /api/creative-lab/copy` - Generate copy

## Deploy (Hostinger KVM8)

### Requirements
- KVM8 VPS (8GB RAM minimum)
- Docker & Docker Compose
- Domain with DNS configured

### Setup

1. SSH into server
2. Clone repository
3. Configure `.env`
4. Run `docker-compose up -d`
5. Configure Nginx/Traefik for SSL

## White-Label

Cada agency pode ter:
- Logo customizado
- Cores customizadas
- Domínio próprio
- Configurações específicas

Configure em `Agency.branding`:
```json
{
  "logo_url": "https://...",
  "primary_color": "#4F46E5",
  "secondary_color": "#10B981",
  "company_name": "Minha Agência"
}
```

## License

Private - All rights reserved.
