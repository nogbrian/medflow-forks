# QA - Unified UI

## Build Status

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend Shell (Next.js) | PASS | All 8 pages compile, no type errors |
| Creative Studio (Vite) | PASS | Builds to ~618KB, placeholder injected |
| Integration API (Python) | PASS | Syntax valid, routes registered |
| Docker Compose | PASS | 3 services configured with health checks |

## Pages Verified (Build Output)

| Route | Size | Status |
|-------|------|--------|
| `/` (Dashboard) | 2.94 kB | OK |
| `/login` | 2.38 kB | OK |
| `/crm` | 1.15 kB | OK |
| `/crm/contacts` | 2.89 kB | OK |
| `/agenda` | 1.15 kB | OK |
| `/inbox` | 1.15 kB | OK |
| `/creative` | 1.81 kB | OK |

## Feature Checklist

### Auth (Phase 3)
- [x] Login page renders at `/login`
- [x] AuthProvider wraps all pages
- [x] Shell redirects to `/login` when no token
- [x] JWT token stored in localStorage
- [x] User info displayed in sidebar footer
- [x] Logout button clears token and redirects
- [ ] Login against live API (requires deployment)
- [ ] Token expiration handling (24h)

### Navigation (Phase 4)
- [x] Sidebar renders with all sections
- [x] Active link indicator (orange left border)
- [x] Mobile menu toggle works (hamburger → slide in)
- [x] Desktop sidebar always visible (w-64)
- [x] All iframe pages load correct env URLs
- [x] Refresh, Fullscreen, Open in New Tab buttons
- [ ] Live iframe loading (requires deployed services)
- [ ] Cross-origin cookie/session persistence

### Creative Studio Integration (Phase 6)
- [x] Creative Studio builds with postMessage bridge
- [x] Shell page listens for `creative:generated` events
- [x] "Enviar ao Chat" button appears after image generation
- [x] API endpoint `/api/creative-lab/send-to-chat` registered
- [x] Creative Lab routes registered in main.py
- [ ] Live postMessage flow (requires running services)
- [ ] Actual Chatwoot image delivery (requires CHATWOOT_API_KEY)

### Styling (Phase 5)
- [x] Industrial/Swiss design system defined in Tailwind config
- [x] Consistent color palette across shell (paper, ink, accent-orange)
- [x] JetBrains Mono for data, Inter Tight for headers
- [x] Hard drop shadows (no blur)
- [x] Grid background pattern
- [x] Zero border-radius (industrial aesthetic)

## Requires Live Environment

The following items cannot be verified locally and require deployment to Coolify:

1. **Iframe loading** - Each service must allow framing via CSP headers
2. **Auth flow end-to-end** - Requires Integration API with database
3. **Creative → Chatwoot** - Requires both services running
4. **Cross-module navigation** - Requires all services on same domain

## Deployment Steps (for Coolify)

1. Push code to repository
2. Coolify builds docker-compose services
3. Verify Traefik routes resolve:
   - `medflow.trafegoparaconsultorios.com.br` → web:3000
   - `studio.trafegoparaconsultorios.com.br` → creative-studio:3001
   - `api.trafegoparaconsultorios.com.br` → integration:8000
4. Apply iframe CSP labels to Twenty, Chatwoot, Cal.com (see IFRAME_CONFIG.md)
5. Set GEMINI_API_KEY in Coolify env vars
6. Test login with seeded users
7. Verify each iframe loads within shell
