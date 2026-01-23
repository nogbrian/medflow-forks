# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Coolify (PaaS)                                   │
│                     72.61.37.176 + Traefik                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  MedFlow Frontend Shell (Next.js)                                  │  │
│  │  medflow.trafegoparaconsultorios.com.br                            │  │
│  │                                                                    │  │
│  │  ┌──────────┐  ┌───────────────────────────────────────────────┐  │  │
│  │  │ Sidebar  │  │  Iframe Modules:                              │  │  │
│  │  │          │  │                                               │  │  │
│  │  │ Dashboard│  │  /crm     → crm.trafego...   (Twenty)        │  │  │
│  │  │ CRM      │  │  /inbox   → inbox.trafego... (Chatwoot)      │  │  │
│  │  │ Inbox    │  │  /agenda  → agenda.trafego...(Cal.com)       │  │  │
│  │  │ Agenda   │  │  /creative→ studio.trafego...(Creative)      │  │  │
│  │  │ Creative │  │                                               │  │  │
│  │  └──────────┘  └───────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │  Twenty CRM  │   │   Chatwoot   │   │   Cal.com    │                │
│  │  (Contacts   │   │  (Messaging  │   │ (Scheduling) │                │
│  │   Pipeline)  │   │   WhatsApp)  │   │              │                │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                │
│         │                   │                   │                        │
│         │    Webhooks       │    Webhooks       │   Webhooks             │
│         ▼                   ▼                   ▼                        │
│  ┌──────────────────────────────────────────────────────┐               │
│  │              MedFlow Integration API                  │               │
│  │           (FastAPI + PostgreSQL + Redis)               │               │
│  │                                                       │               │
│  │  /auth/login               → JWT token                │               │
│  │  /sync/webhooks/twenty     → sync contact to Chatwoot │               │
│  │  /sync/webhooks/chatwoot   → sync contact to Twenty   │               │
│  │  /sync/webhooks/calcom     → update Twenty + notify   │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────┐               │
│  │              Intel - Viral Finder                    │               │
│  │         (FastAPI + Next.js + Apify + AI)             │               │
│  │                                                      │               │
│  │  intel-api (:8001)  intel-web (:3002)                │               │
│  │  /api/instagram-orchestrator  Dashboard              │               │
│  │  /api/ads/meta-ads/search     Workspaces             │               │
│  │  /api/ai/chat                 Profiles               │               │
│  │  /api/ai/brand-profiles       Creative Lab           │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐                                   │
│  │Creative Studio│   │ Evolution API│── WhatsApp ──▶ Chatwoot           │
│  │ (Gemini AI)  │   │  (WhatsApp)  │                                   │
│  └──────────────┘   └──────────────┘                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### MedFlow Frontend Shell (NEW)
- **Role:** Unified navigation interface wrapping all modules
- **URL:** `https://medflow.trafegoparaconsultorios.com.br`
- **Stack:** Next.js 15 + React 19 + Tailwind CSS
- **Auth:** JWT via Integration API, stored in localStorage
- **Pattern:** Shell Container with iframe embedding
- **Port:** 3000

### Creative Studio (NEW)
- **Role:** AI-powered creative/image generation for marketing
- **URL:** `https://studio.trafegoparaconsultorios.com.br`
- **Stack:** React 19 + Vite + Google Gemini API
- **Auth:** Gemini API key injected at container runtime
- **Port:** 3001
- **Serving:** nginx (static SPA)

### Twenty CRM
- **Role:** Source of truth for contacts and sales pipeline
- **URL:** `https://crm.trafegoparaconsultorios.com.br`
- **Stack:** Node.js + PostgreSQL + Redis
- **Key Objects:** Person (contacts), Opportunity (pipeline stages)

### Chatwoot
- **Role:** Customer messaging hub (WhatsApp, web chat)
- **URL:** `https://inbox.trafegoparaconsultorios.com.br`
- **Stack:** Rails + PostgreSQL (pgvector) + Redis + Sidekiq
- **Key Objects:** Contact, Conversation, Message

### Cal.com
- **Role:** Appointment scheduling
- **URL:** `https://agenda.trafegoparaconsultorios.com.br`
- **Stack:** Next.js + PostgreSQL
- **Key Objects:** Booking, EventType

### Evolution API
- **Role:** WhatsApp Business API bridge
- **URL:** `https://evo.trafegoparaconsultorios.com.br`
- **Connection:** Directly integrated with Chatwoot inbox

### MedFlow Integration API
- **Role:** Orchestration layer + auth + AI agents
- **URL:** `https://api.trafegoparaconsultorios.com.br`
- **Stack:** FastAPI (Python 3.12) + PostgreSQL + Redis
- **Key Modules:**
  - `core/auth.py` - JWT authentication + RBAC
  - `api/routes/auth.py` - Login/logout endpoints
  - `services/sync_service.py` - Cross-service sync
  - `api/routes/sync.py` - Webhook endpoints

### Intel - Viral Finder (NEW)
- **Role:** Instagram intelligence, ads transparency, AI-powered content analysis
- **URLs:**
  - API: `https://intel.trafegoparaconsultorios.com.br/api/` (via intel-api)
  - Web: `https://intel.trafegoparaconsultorios.com.br` (via intel-web)
- **Stack:**
  - Backend: FastAPI (Python 3.11+) + SQLAlchemy async + pgvector
  - Frontend: Next.js 16 + React 19 + Prisma + shadcn/ui
- **Auth:** Traefik forwardAuth → Integration API `/api/auth/verify`
- **Features:**
  - Instagram scraping via Apify (profiles, posts, reels)
  - Meta Ad Library search
  - Google Ads Transparency search
  - Multi-LLM AI chat (OpenAI, Anthropic, Google, xAI)
  - Brand profiles with context injection
  - Semantic memory search with pgvector embeddings
  - Image generation
- **Ports:** API 8001, Web 3002

## Docker Compose Services (medflow-forks)

```yaml
services:
  integration     # FastAPI API    → api.trafegoparaconsultorios.com.br     :8000
  web             # Next.js Shell  → medflow.trafegoparaconsultorios.com.br  :3000
  creative-studio # Vite + nginx   → studio.trafegoparaconsultorios.com.br   :3001
  intel-api       # FastAPI API    → intel.trafegoparaconsultorios.com.br/api :8001
  intel-web       # Next.js        → intel.trafegoparaconsultorios.com.br    :3002
```

## Data Flow

### User Authentication
```
Browser → /login (Shell) → POST /api/auth/login → Integration API
  → Verify bcrypt password → Generate JWT (24h)
  → Store in localStorage → Render Shell with modules
```

### Contact Created in Twenty
```
Twenty CRM → webhook → POST /sync/webhooks/twenty
  → SyncService.sync_twenty_contact_to_chatwoot()
    → Search Chatwoot by email/phone
    → Create or update Chatwoot contact
    → Set custom_attribute: twenty_id
```

### Message Received on WhatsApp
```
WhatsApp → Evolution API → Chatwoot Inbox
  → Chatwoot webhook → POST /sync/webhooks/chatwoot
    → If contact_created: sync to Twenty
    → If message_created: route to AI agent (TODO)
```

### Booking Created in Cal.com
```
Cal.com → webhook → POST /sync/webhooks/calcom
  → SyncService.sync_calcom_booking_to_twenty()
    → Find/create contact in Twenty
    → Create/update opportunity (stage: MEETING_SCHEDULED)
  → SyncService.send_booking_notification_to_chatwoot()
    → Find contact's open conversation
    → Send booking confirmation message
```

## Database Schema (MedFlow)

```
agencies
  ├── clinics (multi-tenant)
  └── users (superuser, agency_staff, clinic_owner, clinic_staff)
```

Managed by Alembic migrations in `/integration/alembic/`.

## Security

- **JWT Auth:** HS256 tokens, 24h expiration, bcrypt password hashing (12 rounds)
- **Cross-subdomain Auth:** `medflow_token` cookie on `.trafegoparaconsultorios.com.br` (7-day expiry, Secure, SameSite=Lax)
- **ForwardAuth:** Traefik middleware verifies JWT via `/api/auth/verify` for intel-web, intel-api, creative-studio
- **RBAC:** 4 roles with multi-tenant clinic isolation
- **Webhook Verification:** HMAC-SHA256 signatures on all webhook endpoints
- **Iframe Security:** CSP `frame-ancestors` restricts embedding to shell domain
- **Environment Isolation:** Secrets validated at startup
- **CORS:** Configurable origins via `CORS_ORIGINS_RAW`

## Networking

All services run in Docker on the same host, connected via the `coolify` Docker network. Traefik handles TLS termination and routing via labels. Internal communication uses Docker DNS.

## Related Docs

- [Auth Strategy](./AUTH_STRATEGY.md)
- [Navigation Architecture](./NAVIGATION_ARCHITECTURE.md)
- [Design System](./DESIGN_SYSTEM.md)
- [Iframe Configuration](./IFRAME_CONFIG.md)
- [Creative Studio Analysis](./CREATIVE_STUDIO_ANALYSIS.md)
- [Viral Finder Deploy](./VIRAL_FINDER_DEPLOY.md)
- [API Endpoints](./ENDPOINTS.md)
