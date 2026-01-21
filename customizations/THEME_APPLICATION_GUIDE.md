# Guia de Aplicação de Temas - MedFlow Industrial

Este documento descreve como aplicar o Design System Industrial aos três white-labels: Twenty CRM, Cal.com e Chatwoot.

---

## Design System Industrial

### Princípios Fundamentais

1. **Brutalismo Funcional** - Estrutura exposta, sem decoração
2. **Hard Shadows** - Sombras sólidas de 4px, sem blur
3. **Zero Border-Radius** - Todos elementos retangulares
4. **Tipografia Mono** - Dados sempre em monospace
5. **Grid Visível** - Bordas pretas delimitando áreas

### Tokens de Design

```css
/* Cores */
--paper: #F2F0E9      /* Background principal */
--ink: #111111        /* Texto principal */
--graphite: #000000   /* Bordas */
--accent-orange: #F24E1E  /* Ações primárias */
--accent-blue: #0047AB    /* Links, info */
--steel: #666666      /* Texto secundário */

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
      - ./customizations/twenty/theme/industrial.css:/app/packages/twenty-front/dist/industrial.css
    environment:
      - CUSTOM_CSS_URL=/industrial.css
```

2. Ou injete via script no build:

```dockerfile
# Dockerfile.twenty
FROM twentycrm/twenty:latest

COPY ./customizations/twenty/theme/industrial.css /app/packages/twenty-front/public/
RUN echo '<link rel="stylesheet" href="/industrial.css">' >> /app/packages/twenty-front/dist/index.html
```

### Método 2: Fork do Código

1. Clone o Twenty CRM
2. Substitua/merge o `tailwind.config.ts`:

```typescript
// packages/twenty-front/tailwind.config.ts
import industrialConfig from '../../customizations/twenty/theme/tailwind.config';
import merge from 'lodash/merge';

const config = merge(baseConfig, industrialConfig);
export default config;
```

3. Importe o CSS no entry point:

```typescript
// packages/twenty-front/src/index.tsx
import '../../../customizations/twenty/theme/industrial.css';
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
   - Primary Color: `#F24E1E`
   - Brand Color: `#F24E1E`
   - Dark Brand Color: `#DC2626`
   - Hide Branding: `true`

### Método 2: CSS Custom via Env

```env
# .env.local ou Docker env
NEXT_PUBLIC_WEBAPP_URL=https://agenda.medflow.com.br
NEXT_PUBLIC_WEBSITE_URL=https://medflow.com.br
CALCOM_TELEMETRY_DISABLED=1

# Branding
NEXT_PUBLIC_APP_NAME=MedFlow Agenda
NEXT_PUBLIC_COMPANY_NAME=MedFlow
NEXT_PUBLIC_LOGO_URL=https://cdn.medflow.com.br/logo.svg
NEXT_PUBLIC_BRAND_COLOR=#F24E1E
NEXT_PUBLIC_DARK_BRAND_COLOR=#DC2626
```

### Método 3: Fork do Código

1. Clone o Cal.com
2. Adicione ao `tailwind.config.ts`:

```typescript
// apps/web/tailwind.config.ts
import industrialConfig from '../../customizations/calcom/theme/tailwind.config';

export default {
  ...baseConfig,
  theme: {
    ...baseConfig.theme,
    extend: {
      ...baseConfig.theme.extend,
      ...industrialConfig.theme.extend,
    },
  },
};
```

3. Adicione CSS global:

```css
/* apps/web/styles/globals.css */
@import '../../../customizations/calcom/theme/industrial.css';
```

### Método 4: Docker Override

```yaml
# docker-compose.yml
services:
  calcom:
    image: calcom/cal.com:latest
    volumes:
      - ./customizations/calcom/theme/industrial.css:/calcom/apps/web/public/custom.css
    environment:
      - NEXT_PUBLIC_CUSTOM_CSS_URL=/custom.css
```

---

## Chatwoot

### Método 1: Custom CSS via Admin (Mais Fácil)

1. Acesse: **Settings → Account Settings → Custom CSS**
2. Cole todo o conteúdo de `industrial.css`
3. Salve

### Método 2: Env Vars + Docker

```env
# .env
INSTALLATION_NAME=MedFlow Inbox
LOGO_URL=https://cdn.medflow.com.br/logo.svg
LOGO_THUMBNAIL_URL=https://cdn.medflow.com.br/logo-small.svg
BRAND_URL=https://medflow.com.br
DISPLAY_MANIFEST=true

# Widget branding
WIDGET_BRAND_COLOR="#F24E1E"
```

### Método 3: Docker com CSS Montado

```yaml
# docker-compose.yml
services:
  chatwoot:
    image: chatwoot/chatwoot:latest
    volumes:
      - ./customizations/chatwoot/theme/industrial.css:/app/public/packs/css/custom.css
    environment:
      - CUSTOM_STYLESHEET_PATH=/packs/css/custom.css
```

### Método 4: Fork do Código

1. Clone o Chatwoot
2. Edite `app/javascript/widget/assets/scss/_variables.scss`:

```scss
// Override brand colors
$color-woot: #F24E1E;
$color-primary: #F24E1E;
$color-bg: #F2F0E9;
$color-border: #000000;
$border-radius: 0;
```

3. Adicione o CSS:

```scss
// app/javascript/dashboard/assets/scss/app.scss
@import '../../../../customizations/chatwoot/theme/industrial';
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
      --color-paper: {branding.colors.background};
      --color-accent-orange: {branding.colors.primary};
      --color-accent-blue: {branding.colors.secondary};
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

### Checklist Visual

- [ ] Background principal é `#F2F0E9` (paper)
- [ ] Todos os botões têm hard shadow de 4px
- [ ] Nenhum elemento tem border-radius
- [ ] Headlines em Inter Tight, uppercase
- [ ] Dados/métricas em JetBrains Mono
- [ ] Bordas são 2px solid preto
- [ ] Cor de ação principal é `#F24E1E` (orange)

### Teste de Consistência

```bash
# Verificar se CSS foi aplicado
curl -s https://crm.medflow.com.br | grep "F2F0E9"
curl -s https://agenda.medflow.com.br | grep "F2F0E9"
curl -s https://inbox.medflow.com.br | grep "F2F0E9"
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

1. Adicione as fontes ao projeto:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

---

## Contato

Para dúvidas sobre aplicação de temas, consulte a equipe de desenvolvimento.
