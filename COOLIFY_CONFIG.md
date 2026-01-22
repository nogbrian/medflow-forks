# MedFlow Forks - Coolify Configuration

## Link Direto para Environment Variables
https://coolify.trafegoparaconsultorios.com.br/project/igsckco404k4gww4kgwccgcs/environment/okk4s4kcg4kkkcssgckwo0sc/application/qgskkcw0o88404g8cwk0880w/environment-variables

---

## VARIÁVEIS OBRIGATÓRIAS

### 1. DATABASE_URL
**Pegar do PostgreSQL do Coolify** - Clique no recurso PostgreSQL no mesmo projeto e copie a connection string.
Formato: `postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE`

### 2. REDIS_URL
**Pegar do Redis do Coolify** - Clique no recurso Redis no mesmo projeto e copie a connection string.
Formato: `redis://HOST:6379`

### 3. JWT_SECRET (copie exatamente)
```
aoSFZlTRQ9Cq4fylhnzt9sUkxv9-pGoLWQRsYi_Q05A
```

### 4. WEBHOOK_SECRET (copie exatamente)
```
sznx1iz1QEA13sQGXmQ_4PQbtTrBrdEDIHck6iw1VCw
```

### 5. APP_ENV
```
production
```

### 6. DEBUG
```
false
```

### 7. LLM_PROVIDER
```
anthropic
```

### 8. CORS_ORIGINS
```
["https://medflow.trafegoparaconsultorios.com.br"]
```

---

## VARIÁVEIS LLM (pelo menos uma obrigatória)

### ANTHROPIC_API_KEY
Sua chave da Anthropic (você configura)

### OPENAI_API_KEY (opcional)
Sua chave da OpenAI

---

## VARIÁVEIS OPCIONAIS (deixe vazias por enquanto)

```
TWENTY_API_URL=
TWENTY_API_KEY=
CALCOM_API_URL=
CALCOM_API_KEY=
CHATWOOT_API_URL=
CHATWOOT_API_KEY=
EVOLUTION_API_URL=
EVOLUTION_API_KEY=
REPLICATE_API_KEY=
```

---

## PASSOS

1. Vá para: Environment Variables (link acima)
2. Clique em "Add" para cada variável
3. Preencha Key e Value
4. Clique "Save"
5. Após adicionar todas, clique "Redeploy" no topo da página

---

## PARA COPIAR/COLAR (formato key=value)

```env
APP_ENV=production
DEBUG=false
JWT_SECRET=aoSFZlTRQ9Cq4fylhnzt9sUkxv9-pGoLWQRsYi_Q05A
WEBHOOK_SECRET=sznx1iz1QEA13sQGXmQ_4PQbtTrBrdEDIHck6iw1VCw
LLM_PROVIDER=anthropic
CORS_ORIGINS=["https://medflow.trafegoparaconsultorios.com.br"]
DATABASE_URL=<PEGAR_DO_POSTGRESQL>
REDIS_URL=<PEGAR_DO_REDIS>
ANTHROPIC_API_KEY=<SUA_CHAVE>
```
