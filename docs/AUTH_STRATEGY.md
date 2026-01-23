# Auth Strategy

## Decision: JWT via Integration API (Option C - Shared JWT)

The frontend shell authenticates via the existing MedFlow Integration API at `api.trafegoparaconsultorios.com.br`.

## Flow

```
User → /login → POST /api/auth/login → JWT token
     → Stored in localStorage
     → Shell components check token presence
     → Protected routes redirect to /login if missing
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Frontend Shell (medflow.trafegoparaconsultorios)    │
│                                                     │
│  /login → authenticates against Integration API     │
│  /* → Shell checks localStorage for JWT             │
│        └─ No token → redirect /login                │
│        └─ Has token → render Shell + iframes        │
│                                                     │
│  Iframes load external services:                    │
│    /crm → crm.trafegoparaconsultorios (Twenty)     │
│    /inbox → inbox.trafegoparaconsultorios (Chatwoot)│
│    /agenda → agenda.trafegoparaconsultorios (Cal)   │
│    /creative → studio.trafegoparaconsultorios       │
└─────────────────────────────────────────────────────┘
```

## Components

| File | Purpose |
|------|---------|
| `src/lib/auth.ts` | Token storage, login API call, types |
| `src/components/auth/auth-provider.tsx` | React context, auth state management |
| `src/app/login/page.tsx` | Login form UI |
| `src/components/layout/shell.tsx` | Route protection (redirect if no auth) |

## Token Details

- **Algorithm:** HS256
- **Expiration:** 24 hours (configurable via `access_token_expire_minutes`)
- **Payload:** `{ sub: user_id, exp: timestamp }`
- **Storage:** localStorage (`medflow_token`, `medflow_user`)

## User Roles

| Role | Access |
|------|--------|
| superuser | All modules, all clinics |
| agency_staff | All modules, agency clinics |
| clinic_owner | All modules, own clinic |
| clinic_staff | Limited modules, own clinic |

## External Services Auth

Each iframe-embedded service (Twenty, Chatwoot, Cal.com) has its own auth system. The shell JWT does NOT provide SSO to these services. Users may need to login separately to each service if accessing directly.

The shell acts as a navigation layer - it gates access to the unified interface but does not proxy auth to individual services.

## Future: Unified SSO

To achieve true SSO across all modules:
1. Configure Traefik forward-auth middleware with the Integration API
2. Set session cookie on `.trafegoparaconsultorios.com.br` domain
3. Each service checks the shared cookie or accepts forwarded auth headers
