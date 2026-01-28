# Moltbot Skills para MedFlow

Skills customizados para o Moltbot integrado com Claude Code.

## Skills Disponíveis

### 🔧 claude-code
Executa tarefas de desenvolvimento usando Claude Code como subprocess.

**Triggers:** `implementa`, `cria`, `corrige`, `bug`, `refatora`, `feature`, `endpoint`

**Exemplo:**
```
"Implementa validação de CPF no cadastro de pacientes"
```

### 🚀 devops
Gerencia deploys, logs, status e rollbacks.

**Triggers:** `deploy`, `status`, `logs`, `restart`, `rollback`

**Exemplos:**
```
"deploy"
"status"
"logs moltbot"
"restart crabwalk"
"rollback"
```

### 📱 marketing
Cria conteúdo de marketing para clínicas médicas com compliance CFM.

**Triggers:** `post`, `carrossel`, `reel`, `anúncio`, `ideias`

**Exemplos:**
```
"Cria um post sobre harmonização facial"
"Gera um carrossel sobre cuidados pós botox"
"Ideias de conteúdo para dermatologista"
```

## Instalação

1. Copie os skills para o workspace do Moltbot:
```bash
cp -r moltbot-skills/* ~/moltbot-workspace/skills/
```

2. Reinicie o Moltbot:
```bash
sudo systemctl restart moltbot
```

## Variáveis de Ambiente Necessárias

```bash
# /etc/moltbot.env

# Para skill claude-code
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_WORKSPACE=/home/deploy/workspaces/medflow
CLAUDE_TIMEOUT=600

# Para skill devops
COOLIFY_API_URL=https://coolify.exemplo.com
COOLIFY_API_TOKEN=seu_token
```

## Arquitetura

```
Telegram/Discord → Moltbot → Skill Router
                               ↓
              ┌────────────────┼────────────────┐
              ↓                ↓                ↓
         claude-code       devops          marketing
              ↓                ↓                ↓
         Claude Code      Coolify API      LLM Chat
         (subprocess)     Git/Docker
```

## Segurança

- Claude Code roda com `--dangerously-skip-permissions` (cuidado!)
- Workspace isolado em `/home/deploy/workspaces/medflow`
- Comandos `sudo` são bloqueados por padrão
- Deploy requer Coolify token válido
