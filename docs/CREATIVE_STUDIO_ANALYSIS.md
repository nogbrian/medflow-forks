# Creative Studio - Analysis

## Project Location
`/Users/brian/Documents/_backups-agencia-20260118/tpc-brain/creative-studio`

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

## Deployment Requirements

**Current state:** No Dockerfile or container config exists.

**Needed for Coolify deployment:**
- Dockerfile (Node.js, install deps, build, serve static)
- `.env` with GEMINI_API_KEY
- Domain: studio.trafegoparaconsultorios.com.br

### Build Output
- `vite build` → `dist/` directory (static files)
- Can be served by any static file server (nginx, serve, etc.)
- Dev server runs on port 3000

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

## Recommended Integration Strategy

### For Deploy (Coolify)
1. Create Dockerfile: multi-stage (build with Node, serve with nginx)
2. Pass GEMINI_API_KEY as env var at build time (Vite bakes it in)
3. Deploy as static site behind Traefik

### For Auth
Since the app has no auth, options:
- **Option A**: Add auth check in App.tsx (redirect to central login if no session cookie)
- **Option B**: Traefik forward-auth middleware (check session before allowing access)
- **Option C**: Wrap in shell app that handles auth

### For Navigation
The app is a full-page SPA. Integration options:
- **Iframe inside shell** - simplest, no code changes to Studio
- **Inject menu component** - requires modifying App.tsx layout
- **Micro-frontend** - most complex but cleanest UX

### For Cross-System Integration
The app runs entirely client-side, so integrations need:
- API calls to Twenty/Chatwoot from the browser (CORS considerations)
- OR a thin backend proxy for cross-service calls
