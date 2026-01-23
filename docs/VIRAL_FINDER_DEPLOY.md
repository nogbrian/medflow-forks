# Viral Finder - Deployment Guide

## Overview

Viral Finder (Intel module) provides Instagram intelligence, ads transparency search, and AI-powered content analysis. It consists of two services deployed as part of the medflow-forks Docker Compose stack.

## Services

| Service | Port | Domain | Stack |
|---------|------|--------|-------|
| intel-api | 8001 | intel.trafegoparaconsultorios.com.br/api | FastAPI + SQLAlchemy + Apify |
| intel-web | 3002 | intel.trafegoparaconsultorios.com.br | Next.js 16 + Prisma + shadcn |

## Authentication

Both services are protected by Traefik forwardAuth middleware:

```
Browser → Traefik → forwardAuth → Integration API /api/auth/verify
  → Cookie "medflow_token" verified
  → 200: pass through to intel-web/intel-api
  → 401: redirect to medflow login
```

The `medflow_token` cookie is set on `.trafegoparaconsultorios.com.br` domain, enabling SSO across all subdomains.

### Superusers

- `cto@trafegoparaconsultorios.com.br` (superuser role)
- `heloisa@trafegoparaconsultorios.com.br` (superuser role)

## API Endpoints (intel-api)

### Scraping
- `POST /api/instagram-orchestrator` — Trigger Instagram profile/posts/reels scraping via Apify

### Ads Transparency
- `POST /api/ads/meta-ads/search` — Search Meta Ad Library by keywords
- `POST /api/ads/meta-ads/by-page` — Get ads from a specific Facebook page
- `POST /api/ads/google-ads/search` — Search Google Ads Transparency Center

### AI Chat
- `GET /api/ai/providers` — List available AI providers
- `POST /api/ai/chat` — Chat with streaming/non-streaming support
- `POST /api/ai/chat/compare` — Multi-model comparison
- `POST /api/ai/generate-image` — Generate images via AI
- `GET /api/ai/models` — List frontier models

### Conversations
- `GET/POST /api/ai/conversations` — List/create conversations
- `GET/PATCH/DELETE /api/ai/conversations/{id}` — CRUD
- `POST /api/ai/conversations/{id}/consolidate` — Consolidate to long-term memory

### Brand Profiles
- `GET/POST /api/ai/brand-profiles` — List/create brand profiles
- `GET/PATCH/DELETE /api/ai/brand-profiles/{id}` — CRUD

### Memory
- `POST /api/ai/memory/store` — Store memories with embeddings
- `POST /api/ai/memory/search` — Semantic memory search (pgvector)

### Health
- `GET /health` — Service health check

## Environment Variables

### intel-api
| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| APIFY_TOKEN | No | Apify API token for scraping |
| META_ACCESS_TOKEN | No | Meta Ad Library API token |
| OPENAI_API_KEY | No | OpenAI API key |
| ANTHROPIC_API_KEY | No | Anthropic API key |
| GEMINI_API_KEY | No | Google Gemini API key |
| XAI_API_KEY | No | xAI (Grok) API key |
| DEBUG | No | Enable debug mode (default: false) |

### intel-web
| Variable | Required | Description |
|----------|----------|-------------|
| NEXT_PUBLIC_API_URL | Yes | Public API URL for client-side calls |
| INTEL_API_URL | Yes | Internal API URL for SSR |
| DATABASE_URL | Yes | PostgreSQL for Prisma |
| NODE_ENV | No | Node environment (default: production) |

## Traefik Configuration

```yaml
# intel-api: only /api and /health paths
traefik.http.routers.intel-api.rule=Host(`intel.trafegoparaconsultorios.com.br`) && (PathPrefix(`/api`) || Path(`/health`))
traefik.http.routers.intel-api.middlewares=intel-auth
traefik.http.middlewares.intel-auth.forwardauth.address=http://integration:8000/api/auth/verify

# intel-web: all other paths
traefik.http.routers.intel-web.rule=Host(`intel.trafegoparaconsultorios.com.br`)
traefik.http.routers.intel-web.middlewares=intel-web-auth
traefik.http.middlewares.intel-web-auth.forwardauth.address=http://integration:8000/api/auth/verify
```

## Navigation

- **MedFlow → Intel:** Sidebar link "Viral Finder" under "Inteligência" section
- **Intel → MedFlow:** Footer link "Voltar ao MedFlow" in intel-web sidebar
- **Logout:** Clears `medflow_token` cookie on root domain and redirects to MedFlow login

## Database

Intel-api uses the same PostgreSQL instance as the integration API. Tables:
- `workspaces` — Multi-tenant workspace isolation
- `instagram_profiles` — Tracked Instagram profiles
- `instagram_posts` — Scraped posts and reels
- `scrape_runs` — Scraping job history
- `ai_conversations` — Chat conversation threads
- `ai_messages` — Individual messages
- `ai_memories` — Long-term memory with pgvector embeddings
- `ai_knowledge` — Knowledge base entries for RAG
- `brand_profiles` — Brand context for AI conversations
- `ad_results` — Cached ad search results

## Deployment

The services are deployed as part of the medflow-forks Docker Compose stack on Coolify:

1. Push changes to `main` branch on GitHub
2. In Coolify: Reload Compose File → Redeploy
3. All 5 services rebuild and restart together
4. Health checks verify services are operational

## Troubleshooting

- **401 on all requests:** Check that `medflow_token` cookie is set (login via medflow first)
- **502 Bad Gateway:** intel-api or intel-web container may not be healthy yet (check logs)
- **Routing conflicts:** Ensure no other Coolify app serves the same domain (check for standalone viral-finder apps)
