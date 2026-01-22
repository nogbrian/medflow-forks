# Endpoints

## Service URLs

| Service | Temporary URL (sslip.io) | Final Domain |
|---------|--------------------------|--------------|
| MedFlow API | - | `https://api.trafegoparaconsultorios.com.br` |
| Twenty CRM | `http://twenty-m8w8gso08k44wc0cs4oswosg.72.61.37.176.sslip.io` | `https://crm.trafegoparaconsultorios.com.br` |
| Chatwoot | `http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io` | `https://chat.trafegoparaconsultorios.com.br` |
| Cal.com | `http://calcom-bk0k00wkoog8ck48c4k8k4gc.72.61.37.176.sslip.io` | `https://agenda.trafegoparaconsultorios.com.br` |
| Evolution API | `https://evo.trafegoparaconsultorios.com.br` | Same |

## MedFlow Integration API

Base URL: `https://api.trafegoparaconsultorios.com.br`

### Health & Status

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check |
| GET | `/` | None | API info |
| GET | `/sync/status` | JWT | Service connection status |

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | None | Login (email + password) |
| GET | `/api/auth/me` | JWT | Current user info |

### Admin

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/admin/db-status` | None* | Database status |
| POST | `/api/admin/run-migrations` | None* | Run Alembic migrations |
| POST | `/api/admin/seed` | None* | Seed initial data |
| POST | `/api/admin/reset-db` | None* | Drop all tables |

*Admin endpoints are unprotected - restrict in production.

### Sync Operations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/sync/clinic` | JWT (superuser) | Full clinic sync |
| POST | `/sync/webhooks/setup` | JWT (superuser) | Register all webhooks |

### Webhook Receivers

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/sync/webhooks/twenty` | HMAC signature | Twenty CRM events |
| POST | `/sync/webhooks/calcom` | HMAC signature | Cal.com booking events |
| POST | `/sync/webhooks/chatwoot` | HMAC signature | Chatwoot events |

## Twenty CRM API

Base URL: `http://twenty-m8w8gso08k44wc0cs4oswosg.72.61.37.176.sslip.io`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api` | GraphQL endpoint |
| POST | `/api/webhooks` | Webhook management |
| GET | `/api/open-api/core` | OpenAPI spec |

Login: `admin@trafegoparaconsultorios.com.br`

## Chatwoot API

Base URL: `http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io`

Auth header: `api_access_token: THnVEkiFXps1PefAxgRWDyKg`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/sign_in` | Web login |
| GET | `/api/v1/accounts/1/contacts` | List contacts |
| POST | `/api/v1/accounts/1/contacts` | Create contact |
| GET | `/api/v1/accounts/1/contacts/search?q=` | Search contacts |
| GET | `/api/v1/accounts/1/conversations` | List conversations |
| POST | `/api/v1/accounts/1/conversations/{id}/messages` | Send message |
| GET | `/api/v1/accounts/1/agents` | List agents |
| POST | `/api/v1/accounts/1/agents` | Create agent |

## Cal.com API

Base URL: `http://calcom-bk0k00wkoog8ck48c4k8k4gc.72.61.37.176.sslip.io`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/brian/15min` | 15-minute booking page |
| GET | `/brian/30min` | 30-minute booking page |
| GET | `/api/v1/event-types` | List event types |
| POST | `/api/v1/bookings` | Create booking |

## Evolution API

Base URL: `https://evo.trafegoparaconsultorios.com.br`

Auth header: `apikey: Comandos95A2025M2026`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/manager` | Web manager UI |
| GET | `/instance/fetchInstances` | List instances |
| POST | `/message/sendText/{instance}` | Send text message |
| GET | `/instance/connectionState/{instance}` | Connection status |

## Internal Docker Network

Services communicate internally via the `coolify` Docker network using container names:

| Service | Internal Hostname |
|---------|-------------------|
| Twenty DB | `postgres-m8w8gso08k44wc0cs4oswosg:5432` |
| Twenty Redis | `redis-m8w8gso08k44wc0cs4oswosg:6379` |
| Chatwoot | `chatwoot-d8gc84okgccw84g444wgswko:3000` |
| MedFlow DB | `postgres:5432` (within compose) |
| MedFlow Redis | `redis:6379` (within compose) |
