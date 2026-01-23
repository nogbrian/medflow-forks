# Navigation Architecture

## Approach: Shell Container (Option A)

A Next.js shell app hosts all modules via iframes, providing unified navigation without modifying individual services.

## System Diagram

```
┌───────────────────────────────────────────────────────────────┐
│  medflow.trafegoparaconsultorios.com.br (Next.js Shell)       │
│                                                               │
│  ┌──────────┐  ┌──────────────────────────────────────────┐  │
│  │           │  │                                          │  │
│  │  Sidebar  │  │            Iframe Content                │  │
│  │           │  │                                          │  │
│  │ Dashboard │  │  Route      → Iframe src                 │  │
│  │ CRM       │  │  /crm       → crm.trafego...            │  │
│  │ Agenda    │  │  /agenda    → agenda.trafego...          │  │
│  │ Inbox     │  │  /inbox     → inbox.trafego...           │  │
│  │ Creative  │  │  /creative  → studio.trafego...          │  │
│  │           │  │                                          │  │
│  │ [Logout]  │  │  Each iframe is full-height              │  │
│  │           │  │  h-[calc(100dvh-8rem)]                   │  │
│  └──────────┘  └──────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Components

### Shell (`src/components/layout/shell.tsx`)
- Root layout wrapper
- Auth gate: redirects to `/login` if no JWT token
- Renders Header + Sidebar + main content area

### Header (`src/components/layout/header.tsx`)
- Fixed top bar (h-16, z-50)
- Mobile menu toggle
- Logo + status indicator
- Desktop nav links

### Sidebar (`src/components/layout/sidebar.tsx`)
- Fixed left panel (w-64, below header)
- Sections: Principal, CRM, Agenda, Inbox, Creative Lab, Configurações
- Active state with orange left border
- Mobile: slide-in with overlay
- Desktop: always visible
- Footer: user info + logout button

### Module Pages
Each module page follows the same pattern:

```tsx
<Shell>
  <ServiceHeader title="..." badge="..." />
  <IframeContainer src={envUrl} id="frame-id" />
</Shell>
```

**Actions per iframe:**
- Refresh (reload iframe src)
- Fullscreen (requestFullscreen API)
- Open in new tab

## Routes

| Path | Module | Iframe Source |
|------|--------|---------------|
| `/` | Dashboard | Custom React page (no iframe) |
| `/crm` | Twenty CRM | `NEXT_PUBLIC_TWENTY_URL` |
| `/crm/contacts` | Contacts | Custom React page (no iframe) |
| `/agenda` | Cal.com | `NEXT_PUBLIC_CALCOM_URL` |
| `/inbox` | Chatwoot | `NEXT_PUBLIC_CHATWOOT_URL` |
| `/creative` | Creative Studio | `NEXT_PUBLIC_CREATIVE_STUDIO_URL` |
| `/login` | Login | Custom React page (no iframe) |

## Iframe Security

### CSP Headers (nginx.conf on Creative Studio)
```
Content-Security-Policy: frame-ancestors 'self' https://medflow.trafegoparaconsultorios.com.br
```

### Traefik Middleware (for Twenty, Chatwoot, Cal.com)
Each service needs Traefik labels to allow framing:
```
traefik.http.middlewares.<svc>-frame.headers.customResponseHeaders.X-Frame-Options=
traefik.http.middlewares.<svc>-frame.headers.contentSecurityPolicy=frame-ancestors 'self' https://medflow.trafegoparaconsultorios.com.br
```

See `docs/IFRAME_CONFIG.md` for per-service configuration.

## Environment Variables

```env
NEXT_PUBLIC_TWENTY_URL=https://crm.trafegoparaconsultorios.com.br
NEXT_PUBLIC_CHATWOOT_URL=https://inbox.trafegoparaconsultorios.com.br
NEXT_PUBLIC_CALCOM_URL=https://agenda.trafegoparaconsultorios.com.br
NEXT_PUBLIC_CREATIVE_STUDIO_URL=https://studio.trafegoparaconsultorios.com.br
NEXT_PUBLIC_API_URL=https://api.trafegoparaconsultorios.com.br
```

## Why Shell Container?

| Approach | Pros | Cons |
|----------|------|------|
| **Shell Container** | No modifications to services, clean separation, easy to add modules | Double sidebars possible, cross-origin limitations |
| Inject via script | Native feel in each service | Must modify each service, maintenance burden |
| Proxy with inject | Transparent to services | Complex proxy config, response body manipulation |

The Shell Container approach was chosen because:
1. External services (Twenty, Chatwoot, Cal.com) are complex apps we don't control
2. Adding a unified sidebar via proxy injection is fragile
3. The shell provides auth gating without touching service code
4. New modules can be added by creating a new page with an iframe
