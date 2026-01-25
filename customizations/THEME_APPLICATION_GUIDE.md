# Guia de Aplicação de Temas - MedFlow

Este documento descreve como aplicar os Design Systems aos três white-labels: Twenty CRM, Cal.com e Chatwoot.

---

## Temas Disponíveis

| Tema | Arquivos | Características |
|------|----------|-----------------|
| **Industrial** | `industrial.css`, `tailwind.config.ts` | Brutalismo, hard shadows 4px, border-radius 0px |
| **Intelligent Flow** | `intelligent-flow.css`, `tailwind.intelligent-flow.config.ts` | Glassmorphism, soft shadows, border-radius 8-32px |

---

## Design System: Intelligent Flow (Recomendado)

### Princípios Fundamentais

1. **Glassmorphism** - Backgrounds translúcidos com blur
2. **Soft Shadows** - Sombras suaves com glow sutil
3. **Rounded Corners** - Border-radius de 8px a 32px
4. **Tipografia Elegante** - Clash Display (títulos), Satoshi (corpo), JetBrains Mono (dados)
5. **Micro-animações** - Transições suaves em hover e interações

### Tokens de Design

```css
/* Cores */
--color-eng-blue: #0F3038       /* Texto e elementos principais */
--color-alert: #FF6400          /* Ações primárias, CTAs */
--color-concrete: #808080       /* Texto secundário */
--color-tech-white: #F5F5F2     /* Background principal */

/* Sombras */
--shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.06)
--shadow-md: 0 4px 16px rgba(0, 0, 0, 0.08)
--shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.10)
--shadow-glow-orange: 0 8px 32px rgba(255, 100, 0, 0.3)

/* Bordas */
--border-width: 1px
--border-color: rgba(15, 48, 56, 0.08)
--border-radius-sm: 8px
--border-radius-md: 12px
--border-radius-lg: 16px
--border-radius-xl: 24px

/* Backdrop */
--backdrop-blur: 12px
```

### Fontes Necessárias

```html
<!-- Adicione ao <head> do HTML -->
<link rel="preconnect" href="https://api.fontshare.com">
<link href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@400,500,600,700&display=swap" rel="stylesheet">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

---

## Design System: Industrial (Legado)

### Princípios Fundamentais

1. **Brutalismo Funcional** - Estrutura exposta, sem decoração
2. **Hard Shadows** - Sombras sólidas de 4px, sem blur
3. **Zero Border-Radius** - Todos elementos retangulares
4. **Tipografia Mono** - Dados sempre em monospace
5. **Grid Visível** - Bordas pretas delimitando áreas

### Tokens de Design

```css
/* Cores */
--paper: #F2F0E9              /* Background principal */
--ink: #111111                /* Texto principal */
--graphite: #000000           /* Bordas */
--accent-orange: #F24E1E      /* Ações primárias */
--accent-blue: #0047AB        /* Links, info */
--steel: #666666              /* Texto secundário */

/* Sombras */
--shadow-hard: 4px 4px 0px 0px #000000
--shadow-hard-orange: 4px 4px 0px 0px #F24E1E

/* Bordas */
--border-width: 2px
--border-radius: 0px (SEMPRE)
```

---

## Twenty CRM

### Método 1: CSS Injection (Recomendado)

1. Monte o arquivo CSS no container Docker:

```yaml
# docker-compose.yml
services:
  twenty:
    image: twentycrm/twenty:latest
    volumes:
      # Para Intelligent Flow:
      - ./customizations/twenty/theme/intelligent-flow.css:/app/packages/twenty-front/dist/theme.css
      # Para Industrial:
      # - ./customizations/twenty/theme/industrial.css:/app/packages/twenty-front/dist/theme.css
    environment:
      - CUSTOM_CSS_URL=/theme.css
```

2. Ou injete via script no build:

```dockerfile
# Dockerfile.twenty
FROM twentycrm/twenty:latest

# Para Intelligent Flow:
COPY ./customizations/twenty/theme/intelligent-flow.css /app/packages/twenty-front/public/
RUN echo '<link rel="stylesheet" href="/intelligent-flow.css">' >> /app/packages/twenty-front/dist/index.html
```

### Método 2: Fork do Código

1. Clone o Twenty CRM
2. Substitua/merge o `tailwind.config.ts`:

```typescript
// packages/twenty-front/tailwind.config.ts
// Para Intelligent Flow:
import intelligentFlowConfig from '../../customizations/twenty/theme/tailwind.intelligent-flow.config';
import merge from 'lodash/merge';

const config = merge(baseConfig, intelligentFlowConfig);
export default config;
```

3. Importe o CSS no entry point:

```typescript
// packages/twenty-front/src/index.tsx
// Para Intelligent Flow:
import '../../../customizations/twenty/theme/intelligent-flow.css';
```

### Variáveis de Ambiente

```env
# .env
FRONT_BASE_URL=https://crm.medflow.com.br
FRONT_DOMAIN=medflow.com.br
```

---

## Cal.com

### Método 1: Branding via Dashboard

Cal.com suporta customização via painel:

1. Acesse: **Settings → Appearance**
2. Configure:
   - Primary Color: `#FF6400` (Intelligent Flow) ou `#F24E1E` (Industrial)
   - Brand Color: `#FF6400`
   - Dark Brand Color: `#E55A00`
   - Hide Branding: `true`

### Método 2: Env Vars + Docker

```env
# .env.local ou Docker env
NEXT_PUBLIC_WEBAPP_URL=https://agenda.medflow.com.br
NEXT_PUBLIC_WEBSITE_URL=https://medflow.com.br
CALCOM_TELEMETRY_DISABLED=1

# Branding (Intelligent Flow)
NEXT_PUBLIC_APP_NAME=MedFlow Agenda
NEXT_PUBLIC_COMPANY_NAME=MedFlow
NEXT_PUBLIC_LOGO_URL=https://cdn.medflow.com.br/logo.svg
NEXT_PUBLIC_BRAND_COLOR=#FF6400
NEXT_PUBLIC_DARK_BRAND_COLOR=#E55A00
```

### Método 3: Fork do Código

1. Clone o Cal.com
2. Adicione ao `tailwind.config.ts`:

```typescript
// apps/web/tailwind.config.ts
// Para Intelligent Flow:
import intelligentFlowConfig from '../../customizations/calcom/theme/tailwind.intelligent-flow.config';

export default {
  ...baseConfig,
  theme: {
    ...baseConfig.theme,
    extend: {
      ...baseConfig.theme.extend,
      ...intelligentFlowConfig.theme.extend,
    },
  },
};
```

3. Adicione CSS global:

```css
/* apps/web/styles/globals.css */
/* Para Intelligent Flow: */
@import '../../../customizations/calcom/theme/intelligent-flow.css';
```

### Método 4: Docker Override

```yaml
# docker-compose.yml
services:
  calcom:
    image: calcom/cal.com:latest
    volumes:
      # Para Intelligent Flow:
      - ./customizations/calcom/theme/intelligent-flow.css:/calcom/apps/web/public/custom.css
    environment:
      - NEXT_PUBLIC_CUSTOM_CSS_URL=/custom.css
```

---

## Chatwoot

### Método 1: Custom CSS via Admin (Mais Fácil)

1. Acesse: **Settings → Account Settings → Custom CSS**
2. Cole todo o conteúdo de `intelligent-flow.css` (ou `industrial.css`)
3. Salve

### Método 2: Env Vars + Docker

```env
# .env
INSTALLATION_NAME=MedFlow Inbox
LOGO_URL=https://cdn.medflow.com.br/logo.svg
LOGO_THUMBNAIL_URL=https://cdn.medflow.com.br/logo-small.svg
BRAND_URL=https://medflow.com.br
DISPLAY_MANIFEST=true

# Widget branding (Intelligent Flow)
WIDGET_BRAND_COLOR="#FF6400"
```

### Método 3: Docker com CSS Montado

```yaml
# docker-compose.yml
services:
  chatwoot:
    image: chatwoot/chatwoot:latest
    volumes:
      # Para Intelligent Flow:
      - ./customizations/chatwoot/theme/intelligent-flow.css:/app/public/packs/css/custom.css
    environment:
      - CUSTOM_STYLESHEET_PATH=/packs/css/custom.css
```

### Método 4: Fork do Código

1. Clone o Chatwoot
2. Edite `app/javascript/widget/assets/scss/_variables.scss`:

```scss
// Override brand colors (Intelligent Flow)
$color-woot: #FF6400;
$color-primary: #FF6400;
$color-bg: #F5F5F2;
$color-border: rgba(15, 48, 56, 0.08);
$border-radius: 12px;
```

3. Adicione o CSS:

```scss
// app/javascript/dashboard/assets/scss/app.scss
// Para Intelligent Flow:
@import '../../../../customizations/chatwoot/theme/intelligent-flow';
```

---

## Branding Dinâmico por Agency

### Backend (FastAPI)

O serviço de branding injeta CSS dinâmico baseado na agency:

```python
# integration/services/branding.py
async def get_branding_css(agency_id: str) -> str:
    agency = await get_agency(agency_id)
    branding = agency.branding

    return f"""
    :root {{
      --color-eng-blue: {branding.colors.primary};
      --color-alert: {branding.colors.accent};
      --color-tech-white: {branding.colors.background};
    }}
    """
```

### Endpoint

```
GET /api/branding/{agency_id}/theme.css
```

Retorna CSS customizado baseado nas configurações da agency.

### Frontend (Next.js)

```tsx
// app/layout.tsx
export default async function RootLayout({ children }) {
  const agency = await getAgency();

  return (
    <html>
      <head>
        <link
          rel="stylesheet"
          href={`/api/branding/${agency.id}/theme.css`}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

---

## Verificação de Aplicação

### Checklist Visual - Intelligent Flow

- [ ] Background principal é `#F5F5F2` (tech-white)
- [ ] Botões têm shadow glow laranja em hover
- [ ] Elementos têm border-radius de 8-16px
- [ ] Headlines em Clash Display
- [ ] Corpo de texto em Satoshi
- [ ] Dados/métricas em JetBrains Mono
- [ ] Bordas são 1px com rgba(15, 48, 56, 0.08)
- [ ] Cor de ação principal é `#FF6400` (alert orange)
- [ ] Cards têm backdrop-blur e fundo translúcido

### Checklist Visual - Industrial

- [ ] Background principal é `#F2F0E9` (paper)
- [ ] Todos os botões têm hard shadow de 4px
- [ ] Nenhum elemento tem border-radius
- [ ] Headlines em Inter Tight, uppercase
- [ ] Dados/métricas em JetBrains Mono
- [ ] Bordas são 2px solid preto
- [ ] Cor de ação principal é `#F24E1E` (orange)

### Teste de Consistência

```bash
# Verificar se CSS foi aplicado (Intelligent Flow)
curl -s https://crm.medflow.com.br | grep "F5F5F2"
curl -s https://agenda.medflow.com.br | grep "F5F5F2"
curl -s https://inbox.medflow.com.br | grep "F5F5F2"

# Verificar se CSS foi aplicado (Industrial)
curl -s https://crm.medflow.com.br | grep "F2F0E9"
```

---

## Troubleshooting

### CSS não carrega

1. Verifique se o arquivo está montado corretamente
2. Verifique permissões do arquivo (deve ser legível)
3. Limpe cache do navegador (Ctrl+Shift+R)

### Estilos não sobrescrevem

1. Adicione `!important` onde necessário
2. Verifique especificidade dos seletores
3. Carregue o CSS após os estilos padrão

### Fontes não carregam

Intelligent Flow:
```html
<link rel="preconnect" href="https://api.fontshare.com">
<link href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@400,500,600,700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

Industrial:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

---

## Estrutura de Arquivos

```
customizations/
├── THEME_APPLICATION_GUIDE.md
├── twenty/
│   └── theme/
│       ├── industrial.css
│       ├── tailwind.config.ts
│       ├── intelligent-flow.css          # Novo
│       └── tailwind.intelligent-flow.config.ts  # Novo
├── chatwoot/
│   └── theme/
│       ├── industrial.css
│       ├── tailwind.config.ts
│       ├── intelligent-flow.css          # Novo
│       └── tailwind.intelligent-flow.config.ts  # Novo
└── calcom/
    └── theme/
        ├── industrial.css
        ├── tailwind.config.ts
        ├── intelligent-flow.css          # Novo
        └── tailwind.intelligent-flow.config.ts  # Novo
```

---

## Contato

Para dúvidas sobre aplicação de temas, consulte a equipe de desenvolvimento.
