# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Coolify (PaaS)                              │
│                     72.61.37.176 + Traefik                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │  Twenty CRM  │   │   Chatwoot   │   │   Cal.com    │            │
│  │  (Contacts   │   │  (Messaging  │   │ (Scheduling) │            │
│  │   Pipeline)  │   │   WhatsApp)  │   │              │            │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │
│         │                   │                   │                    │
│         │    Webhooks       │    Webhooks        │   Webhooks        │
│         ▼                   ▼                   ▼                    │
│  ┌──────────────────────────────────────────────────────┐           │
│  │              MedFlow Integration API                  │           │
│  │           (FastAPI + PostgreSQL + Redis)               │           │
│  │                                                       │           │
│  │  /sync/webhooks/twenty   → sync contact to Chatwoot   │           │
│  │  /sync/webhooks/chatwoot → sync contact to Twenty     │           │
│  │  /sync/webhooks/calcom   → update Twenty + notify CW  │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                     │
│  ┌──────────────┐                                                   │
│  │ Evolution API│──── WhatsApp ────▶ Chatwoot Inbox                 │
│  │  (WhatsApp)  │                                                   │
│  └──────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### Twenty CRM
- **Role:** Source of truth for contacts and sales pipeline
- **Container:** `twenty-m8w8gso08k44wc0cs4oswosg`
- **Stack:** Node.js + PostgreSQL + Redis
- **Key Objects:** Person (contacts), Opportunity (pipeline stages)

### Chatwoot
- **Role:** Customer messaging hub (WhatsApp, web chat)
- **Container:** `chatwoot-d8gc84okgccw84g444wgswko`
- **Stack:** Rails + PostgreSQL (pgvector) + Redis + Sidekiq
- **Key Objects:** Contact, Conversation, Message

### Cal.com
- **Role:** Appointment scheduling
- **Container:** `calcom-bk0k00wkoog8ck48c4k8k4gc`
- **Stack:** Next.js + PostgreSQL
- **Key Objects:** Booking, EventType

### Evolution API
- **Role:** WhatsApp Business API bridge
- **URL:** `https://evo.trafegoparaconsultorios.com.br`
- **Connection:** Directly integrated with Chatwoot inbox

### MedFlow Integration API
- **Role:** Orchestration layer connecting all services
- **Stack:** FastAPI (Python 3.12) + PostgreSQL + Redis
- **Key Modules:**
  - `services/sync_service.py` - Cross-service sync logic
  - `api/routes/sync.py` - Webhook endpoints
  - `core/config.py` - Configuration with security validation

## Data Flow

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
  └── users (superuser, admin, agent roles)
```

Managed by Alembic migrations in `/integration/alembic/`.

## Security

- **Webhook Verification:** HMAC-SHA256 signatures on all webhook endpoints
- **JWT Auth:** HS256 tokens for API authentication
- **Environment Isolation:** Secrets validated at startup, random dev secrets generated in development
- **CORS:** Configurable origins via `CORS_ORIGINS_RAW`

## Networking

All services run in Docker on the same host, connected via the `coolify` Docker network. Traefik handles TLS termination and routing via labels.

Internal communication uses Docker DNS: `service-uuid.72.61.37.176.sslip.io` (HTTP).
