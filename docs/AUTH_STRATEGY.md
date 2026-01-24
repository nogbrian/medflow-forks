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

## SSO for Embedded Services

The Integration API provides an SSO endpoint (`GET /api/sso/{service}`) that generates
authenticated URLs for each embedded service. The frontend calls this before loading iframes.

### Architecture

```
User loads /inbox →
  Frontend calls GET /api/sso/chatwoot (with Bearer JWT) →
    Integration API calls Chatwoot Platform API →
      Returns single-use SSO URL →
        Frontend sets iframe.src = SSO URL →
          User auto-logged into Chatwoot
```

### SSO Endpoint

| Path | Service | Method |
|------|---------|--------|
| `GET /api/sso/chatwoot` | Chatwoot | Platform API single-use token URL |
| `GET /api/sso/twenty` | Twenty CRM | Base URL (SSO TBD) |
| `GET /api/sso/calcom` | Cal.com | Base URL (public pages no auth needed) |

### Chatwoot SSO Setup

1. **Create Platform App** (one-time, on self-hosted Chatwoot via Rails console):
   ```ruby
   app = PlatformApp.create(name: 'medflow_sso')
   puts app.access_token.token  # Save this token
   ```

2. **Set environment variable** in Coolify:
   ```
   CHATWOOT_PLATFORM_TOKEN=<token from step 1>
   ```

3. **Map users**: Each MedFlow user needs `chatwoot_user_id` set in the database.
   Users must be created via Chatwoot's Platform API first.

4. **Result**: When a user navigates to `/inbox`, the SSO endpoint generates a
   single-use login URL. The iframe loads this URL and the user is auto-logged in.

### Twenty CRM SSO (Future)

Twenty CRM does not natively support SSO token-via-URL. Options:
- **OIDC/SAML**: Twenty supports OIDC providers (requires Enterprise-level setup)
- **GraphQL signIn**: Call `signIn` mutation to get tokens, set via redirect/cookie
- **Impersonation**: Use admin impersonation to generate session for target user

Currently falls back to the base URL (user logs in manually on first visit).

### Cal.com SSO (Future)

Cal.com's public booking pages don't require authentication.
For admin pages (event types, availability), options:
- **CNAME mapping**: Make Cal.com a subdomain to avoid cross-origin cookie issues
- **OAuth Managed Users**: Use Cal.com API v2 with managed users and access tokens
- **Custom UI**: Build booking management UI using Cal.com REST API

### Fallback Behavior

If SSO is not configured or fails:
- The iframe loads the service's base URL
- A "Login manual" badge appears in the service header
- Users log in manually within the iframe (credentials stored by the service)

### Frontend Hook

All iframe pages use the `useSsoUrl` hook:
```tsx
const { url, loading, error } = useSsoUrl("chatwoot", fallbackUrl);
```

This hook calls `/api/sso/{service}`, handles errors gracefully, and falls back to the base URL.
