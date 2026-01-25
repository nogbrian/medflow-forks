# Creative Studio - Analysis

**Last Updated:** 2026-01-24

## Project Location
`/Users/brian/Documents/_backups-agencia-20260118/tpc-brain/creative-studio`

## Integration Status

| Phase | Status | Notes |
|-------|--------|-------|
| Iframe Embed | ✅ Complete | `/creative` route with iframe |
| Unified Navigation | ✅ Complete | Sidebar includes Creative Studio |
| Shell Auth Gate | ✅ Complete | JWT auth via MedFlow |
| Intelligent Flow Design | ✅ Complete | Header updated to new design |
| Cross-System Integration | ⏳ Pending | Twenty/Chatwoot connections |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | React 19.2.3 + TypeScript 5.8.2 |
| Build Tool | Vite 6.2.0 |
| Styling | Tailwind CSS (CDN) |
| Icons | Lucide React |
| AI/Image Gen | Google Gemini API (@google/genai) |
| Markdown | react-markdown |

## Project Structure

```
creative-studio/
├── components/
│   ├── BrandLogo.tsx          # TPC logo SVG
│   ├── ChatInterface.tsx      # Main chat + message handling
│   ├── MessageBubble.tsx      # Message display + image editor
│   └── Sidebar.tsx            # Project info sidebar
├── services/
│   └── geminiService.ts       # Gemini API client
├── App.tsx                    # Root component
├── index.tsx                  # React entry point
├── index.html                 # HTML shell with Tailwind CDN
├── types.ts                   # TypeScript interfaces
├── constants.ts               # System instruction + model names
├── vite.config.ts             # Build config
├── tsconfig.json              # TS config
└── package.json               # Dependencies
```

## How It Works

### Image Generation Flow
1. User sends message (text + optional reference images)
2. Gemini `gemini-3-pro-preview` processes with system instruction
3. Model calls `generate_creative` tool with style/content prompts
4. `generateImage()` calls `gemini-3-pro-image-preview`
5. Returns base64-encoded PNG displayed in chat

### Carousel Support
- Multiple slides generated with consistent style
- Auto-verification loop (up to 3 attempts) for visual continuity
- Retry with exponential backoff (2s, 4s, 8s)

### Aspect Ratios
- Stories: 9:16 (mandatory)
- Feed/Posts: 1:1 or 3:4 (never 9:16)

## Authentication

**Current:** No traditional auth. Uses:
1. Google AI Studio's `window.aistudio` object (embedded mode)
2. Fallback: `GEMINI_API_KEY` environment variable
3. Shows "Acesso Restrito" screen if no key found

**No user login/session management exists.**

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| GEMINI_API_KEY | Yes | Google Gemini API key |

Exposed via Vite's `define` config as `process.env.API_KEY`.

## Deployment (IMPLEMENTED)

**Dockerfile:** Multi-stage build (Node.js 20 → nginx:alpine)
- Build stage: `npm install && npm run build` → `dist/`
- Production: nginx serves static files on port 3001
- Runtime API key injection via `docker-entrypoint.sh`

**Docker Compose service:** `creative-studio` in root `docker-compose.yml`

**Domain:** `studio.trafegoparaconsultorios.com.br` (Traefik routing)

**Iframe security:** nginx.conf sets `Content-Security-Policy: frame-ancestors 'self' https://medflow.trafegoparaconsultorios.com.br`

### Build Output
- `vite build` → `dist/` directory (static files, ~618KB gzipped)
- API key placeholder `__GEMINI_API_KEY_PLACEHOLDER__` baked into JS at build time
- `docker-entrypoint.sh` replaces placeholder with `$GEMINI_API_KEY` at container start

## Integration Points

### With Twenty CRM
- No current integration
- Could: associate generated creatives with contacts
- Could: store creative history per client

### With Chatwoot
- No current integration
- Could: send generated images directly to WhatsApp conversations
- Could: open Studio with lead context

### With Cal.com
- No current integration
- Could: generate booking confirmation materials

## Key Observations

1. **Standalone app** - designed for Google AI Studio embedding, not as part of a platform
2. **No backend** - pure client-side React app calling Gemini directly
3. **No user management** - single-user, single-API-key model
4. **localStorage persistence** - chat history saved to `creative_studio_chat_history`
5. **No Docker** - needs containerization for Coolify deployment
6. **Tailwind via CDN** - not bundled, loads from internet

## Integration Strategy (IMPLEMENTED)

### Deploy
- Multi-stage Dockerfile: Node.js build → nginx:alpine serve
- GEMINI_API_KEY injected at runtime via docker-entrypoint.sh
- Deployed as Docker service behind Traefik

### Auth
- Shell app (Next.js) gates access via JWT auth
- Creative Studio itself has no auth (API key is server-side)
- Access controlled at the shell layer: must login to see Creative page

### Navigation
- **Chosen: Iframe inside shell** - no code changes to Studio
- Shell sidebar provides unified nav across all 4 modules
- Creative Studio loads in full-height iframe at `/creative`

### Cross-System Integration (TODO)
Future work needed:
- API calls to Twenty/Chatwoot via Integration API proxy
- Associate creatives with contacts
- Send creatives via Chatwoot conversations
