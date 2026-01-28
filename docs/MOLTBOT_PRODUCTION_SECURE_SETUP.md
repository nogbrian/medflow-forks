# Moltbot Production Setup — Stack Completo Seguro

> **Stack**: Moltbot + Crabwalk + Claude Code + Cloudflare Tunnel + Zero Trust

---

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TELEGRAM                                        │
│                                                                              │
│   Você: "Adiciona validação de CPF no cadastro e faz deploy"                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLOUDFLARE EDGE                                    │
│         Zero Trust Access (Identity + MFA) → Tunnel (Encrypted)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ══════════════════╪══════════════════ (Tunnel)
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                              KVM 8 (VPS)                                     │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      127.0.0.1 (localhost only)                      │   │
│   │                                                                      │   │
│   │  ┌─────────────────┐         ┌─────────────────┐                    │   │
│   │  │    MOLTBOT      │◄───────►│    CRABWALK     │                    │   │
│   │  │    Gateway      │ WebSocket│    Dashboard    │                    │   │
│   │  │    :18789       │         │    :3000        │                    │   │
│   │  └────────┬────────┘         └─────────────────┘                    │   │
│   │           │                                                          │   │
│   │           ▼                                                          │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │                      SKILLS                                  │    │   │
│   │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │    │   │
│   │  │  │ claude-code  │  │   devops     │  │  marketing   │       │    │   │
│   │  │  │              │  │              │  │              │       │    │   │
│   │  │  │ Spawns CLI   │  │ Coolify API  │  │ Content Gen  │       │    │   │
│   │  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘       │    │   │
│   │  └─────────┼─────────────────┼──────────────────────────────────┘    │   │
│   │            │                 │                                       │   │
│   │            ▼                 ▼                                       │   │
│   │  ┌─────────────────┐  ┌─────────────────┐                           │   │
│   │  │  CLAUDE CODE    │  │    COOLIFY      │                           │   │
│   │  │  (subprocess)   │  │    (Deploy)     │                           │   │
│   │  │                 │  │                 │                           │   │
│   │  │  - Read files   │  │  - Build        │                           │   │
│   │  │  - Write code   │  │  - Deploy       │                           │   │
│   │  │  - Run tests    │  │  - Rollback     │                           │   │
│   │  │  - Git commit   │  │  - Logs         │                           │   │
│   │  └─────────────────┘  └─────────────────┘                           │   │
│   │                                                                      │   │
│   └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   Security: UFW (SSH only) + fail2ban + SSH keys only                        │
└──────────────────────────────────────────────────────────────────────────────┘

FLUXO DE CODING:
  1. Você envia comando no Telegram
  2. Moltbot detecta intenção de coding
  3. Skill claude-code spawna Claude Code CLI
  4. Claude Code: analisa → codifica → testa → commita
  5. Skill devops: push → deploy via Coolify
  6. Moltbot reporta resultado no Telegram
```

---

## Pré-requisitos

| Item | Onde Obter |
|------|------------|
| **Domínio no Cloudflare** | https://dash.cloudflare.com |
| **API Key Anthropic** | https://console.anthropic.com |
| **Token Telegram Bot** | @BotFather no Telegram |
| **SSH Key** | `ssh-keygen -t ed25519` |
| **Acesso SSH à KVM 8** | Suas credenciais |

---

## Parte 1: Hardening do Servidor

### 1.1 Conectar e Atualizar

```bash
# Conectar
ssh root@kvm8.trafegoparaconsultorios.com.br

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar pacotes essenciais
sudo apt install -y curl wget git build-essential unzip jq
```

### 1.2 Criar Usuário Deploy

```bash
# Criar usuário (se não existir)
sudo adduser deploy --disabled-password --gecos ""
sudo usermod -aG sudo deploy

# Configurar sudo sem senha para deploy (opcional, para automação)
echo "deploy ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/deploy

# Copiar SSH key
sudo mkdir -p /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# IMPORTANTE: Testar login em OUTRA janela antes de continuar!
# ssh deploy@kvm8.trafegoparaconsultorios.com.br
```

### 1.3 Hardening SSH

```bash
sudo nano /etc/ssh/sshd_config
```

Configurações de segurança:
```bash
# === SEGURANÇA BÁSICA ===
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# === LIMITAR ACESSO ===
AllowUsers deploy
MaxAuthTries 3
MaxSessions 5

# === TIMEOUTS ===
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30

# === DESABILITAR FEATURES DESNECESSÁRIAS ===
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
PermitTunnel no
```

```bash
# Validar configuração
sudo sshd -t

# Se OK, reiniciar (MANTENHA SESSÃO ATUAL ABERTA!)
sudo systemctl restart ssh

# Testar em OUTRA janela
ssh deploy@kvm8.trafegoparaconsultorios.com.br
```

### 1.4 Firewall UFW

```bash
# Instalar
sudo apt install -y ufw

# Reset para estado limpo
sudo ufw --force reset

# Configurar políticas padrão
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH (CRÍTICO: fazer ANTES de enable)
sudo ufw allow OpenSSH

# Ativar
sudo ufw --force enable

# Verificar
sudo ufw status verbose
```

**Output esperado:**
```
Status: active
Default: deny (incoming), allow (outgoing)
To                         Action      From
--                         ------      ----
22/tcp (OpenSSH)           ALLOW IN    Anywhere
```

### 1.5 Fail2ban

```bash
# Instalar
sudo apt install -y fail2ban

# Criar configuração local
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
EOF

# Iniciar
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

# Verificar
sudo fail2ban-client status sshd
```

---

## Parte 2: Instalar Node.js 22

```bash
# Mudar para usuário deploy
sudo su - deploy

# Instalar Node.js 22 via NodeSource
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar versões
node --version   # v22.x.x
npm --version    # 10.x.x

# Instalar pnpm (opcional, mais rápido)
sudo npm install -g pnpm
```

---

## Parte 3: Instalar Claude Code

### 3.1 Instalação

```bash
# Instalar Claude Code globalmente
sudo npm install -g @anthropic-ai/claude-code

# Verificar instalação
claude --version

# Criar diretório de workspace
mkdir -p ~/workspaces/medflow
```

### 3.2 Configurar Claude Code

```bash
# Primeira execução para configurar
cd ~/workspaces/medflow

# Clonar repositório (se ainda não existir)
git clone https://github.com/nogbrian/medflow-forks.git .

# Configurar git
git config user.name "MedFlow Bot"
git config user.email "bot@medflow.com.br"

# Testar Claude Code (interativo)
claude --print "Olá, liste os arquivos neste diretório"
```

### 3.3 Arquivo de Configuração Claude Code

```bash
# Criar settings para Claude Code
mkdir -p ~/.claude

cat > ~/.claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(pnpm *)",
      "Bash(git *)",
      "Bash(node *)",
      "Bash(npx *)",
      "Bash(python *)",
      "Bash(pip *)",
      "Bash(cat *)",
      "Bash(ls *)",
      "Bash(mkdir *)",
      "Bash(cp *)",
      "Bash(mv *)",
      "Bash(rm *)",
      "Bash(touch *)",
      "Bash(chmod *)",
      "Bash(grep *)",
      "Bash(find *)",
      "Bash(head *)",
      "Bash(tail *)",
      "Bash(wc *)",
      "Bash(curl *)",
      "Bash(docker *)",
      "Read",
      "Write",
      "Edit",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(sudo *)",
      "Bash(rm -rf /)",
      "Bash(shutdown *)",
      "Bash(reboot *)"
    ]
  },
  "model": "claude-sonnet-4-20250514"
}
EOF
```

### 3.4 Criar Wrapper Script para Execução Não-Interativa

```bash
cat > ~/bin/claude-task << 'EOF'
#!/bin/bash
# Wrapper para executar Claude Code em modo não-interativo

set -e

WORKSPACE="${CLAUDE_WORKSPACE:-$HOME/workspaces/medflow}"
TIMEOUT="${CLAUDE_TIMEOUT:-600}"
OUTPUT_FILE=$(mktemp)

cd "$WORKSPACE"

# Executar Claude Code com timeout
timeout "$TIMEOUT" claude \
  --print \
  --dangerously-skip-permissions \
  --output-format json \
  -p "$1" > "$OUTPUT_FILE" 2>&1

EXIT_CODE=$?

# Retornar output
cat "$OUTPUT_FILE"
rm -f "$OUTPUT_FILE"

exit $EXIT_CODE
EOF

chmod +x ~/bin/claude-task

# Adicionar ao PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Parte 4: Instalar Moltbot

### 4.1 Instalação

```bash
# Instalar Moltbot globalmente
sudo npm install -g moltbot@latest

# Verificar
moltbot --version
moltbot doctor
```

### 4.2 Criar Arquivo de Secrets

```bash
# Criar arquivo de secrets (NÃO versionar!)
sudo tee /etc/moltbot.env << 'EOF'
# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-api03-SUA_KEY_AQUI

# Telegram Bot Token (do @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Coolify API (para deploys)
COOLIFY_API_URL=https://coolify.trafegoparaconsultorios.com.br
COOLIFY_API_TOKEN=seu_token_coolify

# Claude Code workspace
CLAUDE_WORKSPACE=/home/deploy/workspaces/medflow
CLAUDE_TIMEOUT=600
EOF

# Proteger arquivo
sudo chmod 600 /etc/moltbot.env
sudo chown deploy:deploy /etc/moltbot.env
```

### 4.3 Gerar Token Seguro do Gateway

```bash
# Gerar token aleatório de 64 caracteres
GATEWAY_TOKEN=$(openssl rand -hex 32)
echo "Gateway Token: $GATEWAY_TOKEN"

# Salvar para uso posterior
echo "$GATEWAY_TOKEN" > ~/.moltbot_gateway_token
chmod 600 ~/.moltbot_gateway_token
```

### 4.4 Configuração Principal do Moltbot

```bash
mkdir -p ~/.clawdbot

cat > ~/.clawdbot/moltbot.json << EOF
{
  "agent": {
    "model": "anthropic/claude-sonnet-4-20250514",
    "thinking": "medium",
    "maxTokens": 8192
  },
  "gateway": {
    "port": 18789,
    "bind": "127.0.0.1",
    "auth": {
      "mode": "token",
      "token": "$(cat ~/.moltbot_gateway_token)"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "pairing",
      "groups": {
        "*": {
          "requireMention": false
        }
      }
    },
    "whatsapp": {
      "enabled": false
    }
  },
  "workspace": {
    "root": "/home/deploy/moltbot-workspace"
  },
  "security": {
    "pairing": {
      "enabled": true,
      "requireApproval": true
    }
  },
  "skills": {
    "directory": "/home/deploy/moltbot-workspace/skills"
  }
}
EOF
```

### 4.5 Criar Workspace do Moltbot

```bash
mkdir -p ~/moltbot-workspace/skills

# Personalidade do agente
cat > ~/moltbot-workspace/AGENTS.md << 'EOF'
# MedFlow AI Assistant

Você é o assistente de IA da MedFlow, uma plataforma de marketing e automação para clínicas médicas brasileiras.

## Capacidades

### 🔧 Desenvolvimento (via Claude Code)
- Implementar features no codebase MedFlow
- Corrigir bugs
- Refatorar código
- Criar testes
- Fazer commits

### 🚀 DevOps
- Fazer deploy via Coolify
- Verificar status dos serviços
- Ver logs de aplicações
- Reiniciar serviços

### 📱 Marketing
- Criar posts para Instagram
- Escrever copy para anúncios
- Gerar ideias de conteúdo
- Planejar campanhas

### 📅 Atendimento
- Agendar consultas
- Responder dúvidas
- Qualificar leads

## Compliance Obrigatório (CFM)

- NUNCA prometa resultados específicos de procedimentos médicos
- NUNCA divulgue preços publicamente (apenas em conversa privada)
- NUNCA use fotos antes/depois sem autorização documentada
- SEMPRE sugira agendamento para discussão de valores
- SEMPRE mantenha sigilo médico (LGPD)

## Formato de Respostas

- Máximo 3 parágrafos para respostas gerais
- Use bullet points para listas
- Seja direto e acionável
- Emojis com moderação (máx 2 por mensagem)
- Para código, mostre apenas o relevante (não dumps completos)

## Comandos Especiais

O usuário pode pedir diretamente:
- "implementa [feature]" → Usa Claude Code
- "deploy" → Faz deploy via Coolify
- "status" → Mostra status dos serviços
- "logs [serviço]" → Mostra logs recentes
EOF
```

### 4.6 Serviço Systemd do Moltbot

```bash
sudo tee /etc/systemd/system/moltbot.service << 'EOF'
[Unit]
Description=Moltbot AI Assistant Gateway
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=deploy
Group=deploy
EnvironmentFile=/etc/moltbot.env
WorkingDirectory=/home/deploy
ExecStart=/usr/bin/moltbot gateway --verbose
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/deploy/.clawdbot /home/deploy/moltbot-workspace /home/deploy/workspaces /tmp
PrivateTmp=true

# Limites
LimitNOFILE=65535
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Ativar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable moltbot
sudo systemctl start moltbot

# Verificar
sudo systemctl status moltbot
journalctl -u moltbot -f --no-pager -n 50
```

---

## Parte 5: Instalar Docker e Crabwalk

### 5.1 Instalar Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sudo sh

# Adicionar deploy ao grupo docker
sudo usermod -aG docker deploy

# Aplicar grupo (ou relogar)
newgrp docker

# Verificar
docker --version
docker run --rm hello-world
```

### 5.2 Configurar Crabwalk

```bash
mkdir -p ~/crabwalk

cat > ~/crabwalk/docker-compose.yml << 'EOF'
version: '3.8'

services:
  crabwalk:
    image: ghcr.io/luccast/crabwalk:latest
    container_name: crabwalk
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - CLAWDBOT_API_TOKEN=${CLAWDBOT_API_TOKEN}
      - CLAWDBOT_URL=ws://host.docker.internal:18789
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  default:
    driver: bridge
EOF

# Criar .env
cat > ~/crabwalk/.env << EOF
CLAWDBOT_API_TOKEN=$(cat ~/.moltbot_gateway_token)
EOF

chmod 600 ~/crabwalk/.env

# Iniciar
cd ~/crabwalk
docker compose up -d

# Verificar
docker compose logs -f
```

---

## Parte 6: Cloudflare Tunnel

### 6.1 Instalar Cloudflared

```bash
# Adicionar repositório Cloudflare
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null

echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Instalar
sudo apt update
sudo apt install -y cloudflared

# Verificar
cloudflared --version
```

### 6.2 Autenticar e Criar Tunnel

```bash
# Autenticar (abre browser)
cloudflared tunnel login

# Criar tunnel
cloudflared tunnel create medflow-moltbot

# Listar para pegar UUID
cloudflared tunnel list
```

### 6.3 Configurar Tunnel

```bash
# Pegar UUID
TUNNEL_UUID=$(cloudflared tunnel list --output json | jq -r '.[] | select(.name=="medflow-moltbot") | .id')
echo "Tunnel UUID: $TUNNEL_UUID"

# Criar configuração
cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_UUID
credentials-file: /home/deploy/.cloudflared/${TUNNEL_UUID}.json

ingress:
  # Dashboard Crabwalk
  - hostname: moltbot.trafegoparaconsultorios.com.br
    service: http://127.0.0.1:3000
    originRequest:
      noTLSVerify: true

  # Gateway WebSocket
  - hostname: gateway.trafegoparaconsultorios.com.br
    service: http://127.0.0.1:18789
    originRequest:
      noTLSVerify: true

  # Fallback
  - service: http_status:404
EOF
```

### 6.4 Criar DNS e Iniciar

```bash
# Criar registros DNS
cloudflared tunnel route dns medflow-moltbot moltbot.trafegoparaconsultorios.com.br
cloudflared tunnel route dns medflow-moltbot gateway.trafegoparaconsultorios.com.br

# Testar (foreground)
cloudflared tunnel run medflow-moltbot

# Se funcionar, Ctrl+C e instalar como serviço
sudo cloudflared --config /home/deploy/.cloudflared/config.yml service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Verificar
sudo systemctl status cloudflared
```

---

## Parte 7: Cloudflare Access (Zero Trust)

### 7.1 Configurar no Dashboard

1. Acesse: https://one.dash.cloudflare.com/
2. Vá em **Access** → **Applications** → **Add application**
3. Selecione **Self-hosted**

### 7.2 Application: Dashboard Crabwalk

**Application Configuration:**
- Name: `MedFlow Moltbot Dashboard`
- Domain: `moltbot.trafegoparaconsultorios.com.br`
- Session Duration: `24 hours`

**Policies:**

Policy 1 - Allow:
- Name: `Allow MedFlow Team`
- Action: `Allow`
- Include: Emails = `seu@email.com` (ou domínio `@empresa.com`)

Policy 2 - Block:
- Name: `Block All Others`
- Action: `Block`
- Include: `Everyone`

### 7.3 Application: Gateway (Mesmo processo)

- Domain: `gateway.trafegoparaconsultorios.com.br`
- Mesmas policies

### 7.4 Habilitar MFA

1. **Settings** → **Authentication** → **Login methods**
2. Adicionar: One-time PIN, Google, ou GitHub
3. Em **MFA**: Require for all users

---

## Parte 8: Instalar Skills

### 8.1 Skill: Claude Code

```bash
mkdir -p ~/moltbot-workspace/skills/claude-code

cat > ~/moltbot-workspace/skills/claude-code/index.ts << 'EOF'
import { Skill, Context } from 'moltbot';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

interface ClaudeCodeResult {
  success: boolean;
  filesModified: string[];
  testsRun: boolean;
  testsPassed: boolean;
  commitHash: string | null;
  summary: string;
  error?: string;
}

export default class ClaudeCodeSkill extends Skill {
  name = 'claude-code';
  description = 'Executa tarefas de desenvolvimento usando Claude Code CLI';

  triggers = [
    'implementa', 'implemente', 'cria', 'crie', 'adiciona', 'adicione',
    'corrige', 'corrija', 'fix', 'bug', 'refatora', 'refatore',
    'escreve código', 'desenvolve', 'desenvolva', 'código para',
    'feature', 'funcionalidade', 'endpoint', 'componente'
  ];

  private workspaceRoot = process.env.CLAUDE_WORKSPACE || '/home/deploy/workspaces/medflow';
  private timeout = parseInt(process.env.CLAUDE_TIMEOUT || '600') * 1000;

  async execute(ctx: Context): Promise<void> {
    const task = ctx.message;

    // Notificar início
    await ctx.reply('🔧 Iniciando Claude Code...\n\n_Isso pode levar alguns minutos._');

    try {
      // Executar Claude Code
      const result = await this.runClaudeCode(task, ctx);

      // Formatar e enviar resultado
      await ctx.reply(this.formatResult(result));

    } catch (error: any) {
      await ctx.reply(`❌ **Erro no Claude Code:**\n\`\`\`\n${error.message}\n\`\`\``);
    }
  }

  private async runClaudeCode(task: string, ctx: Context): Promise<ClaudeCodeResult> {
    return new Promise((resolve, reject) => {
      const prompt = this.buildPrompt(task);

      const claude = spawn('claude', [
        '--print',
        '--dangerously-skip-permissions',
        '-p', prompt
      ], {
        cwd: this.workspaceRoot,
        env: {
          ...process.env,
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
          HOME: process.env.HOME,
          PATH: process.env.PATH
        },
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';
      let lastUpdate = Date.now();

      // Coletar output
      claude.stdout?.on('data', (data: Buffer) => {
        const text = data.toString();
        stdout += text;

        // Enviar updates de progresso (throttled)
        if (Date.now() - lastUpdate > 5000) {
          const lines = text.split('\n').filter(l => l.trim());
          const lastLine = lines[lines.length - 1];
          if (lastLine && lastLine.length < 200) {
            ctx.reply(`⏳ ${lastLine.slice(0, 100)}...`);
          }
          lastUpdate = Date.now();
        }
      });

      claude.stderr?.on('data', (data: Buffer) => {
        stderr += data.toString();
      });

      claude.on('close', (code: number | null) => {
        if (code === 0) {
          resolve(this.parseOutput(stdout));
        } else {
          reject(new Error(stderr || `Claude Code exited with code ${code}`));
        }
      });

      claude.on('error', (err: Error) => {
        reject(new Error(`Failed to start Claude Code: ${err.message}`));
      });

      // Timeout
      setTimeout(() => {
        claude.kill('SIGTERM');
        reject(new Error(`Timeout: tarefa excedeu ${this.timeout / 1000 / 60} minutos`));
      }, this.timeout);
    });
  }

  private buildPrompt(task: string): string {
    return `
Você está no repositório MedFlow em ${this.workspaceRoot}.

## Tarefa Solicitada
${task}

## Instruções Obrigatórias

1. **Antes de codificar**: Leia e entenda o código existente relacionado
2. **Padrões do projeto**: TypeScript strict, async/await, Pydantic para Python
3. **Testes**: Adicione ou atualize testes quando apropriado
4. **Commit**: Faça um commit atômico com mensagem descritiva (sem "Claude" na mensagem)
5. **NÃO faça push**: O push será feito pelo skill de deploy

## Formato de Resposta

Ao finalizar, inclua um resumo no formato:

FILES_MODIFIED: [lista de arquivos]
TESTS_RUN: [true/false]
TESTS_PASSED: [true/false]
COMMIT_HASH: [hash ou null]
SUMMARY: [descrição do que foi feito]
`;
  }

  private parseOutput(output: string): ClaudeCodeResult {
    const result: ClaudeCodeResult = {
      success: true,
      filesModified: [],
      testsRun: false,
      testsPassed: false,
      commitHash: null,
      summary: ''
    };

    // Tentar extrair campos estruturados
    const filesMatch = output.match(/FILES_MODIFIED:\s*\[([^\]]*)\]/);
    if (filesMatch) {
      result.filesModified = filesMatch[1].split(',').map(f => f.trim()).filter(Boolean);
    }

    const testsRunMatch = output.match(/TESTS_RUN:\s*(true|false)/i);
    if (testsRunMatch) {
      result.testsRun = testsRunMatch[1].toLowerCase() === 'true';
    }

    const testsPassedMatch = output.match(/TESTS_PASSED:\s*(true|false)/i);
    if (testsPassedMatch) {
      result.testsPassed = testsPassedMatch[1].toLowerCase() === 'true';
    }

    const commitMatch = output.match(/COMMIT_HASH:\s*([a-f0-9]{7,40}|null)/i);
    if (commitMatch && commitMatch[1] !== 'null') {
      result.commitHash = commitMatch[1];
    }

    const summaryMatch = output.match(/SUMMARY:\s*(.+?)(?:\n\n|$)/s);
    if (summaryMatch) {
      result.summary = summaryMatch[1].trim();
    } else {
      // Fallback: últimas linhas do output
      const lines = output.trim().split('\n');
      result.summary = lines.slice(-5).join('\n');
    }

    return result;
  }

  private formatResult(result: ClaudeCodeResult): string {
    let msg = result.success ? '✅ **Tarefa concluída!**\n\n' : '⚠️ **Tarefa parcialmente concluída**\n\n';

    if (result.filesModified.length > 0) {
      msg += '**Arquivos modificados:**\n';
      msg += result.filesModified.map(f => `• \`${f}\``).join('\n');
      msg += '\n\n';
    }

    if (result.testsRun) {
      msg += result.testsPassed
        ? '✅ Testes passando\n'
        : '❌ Alguns testes falharam\n';
    }

    if (result.commitHash) {
      msg += `\n**Commit:** \`${result.commitHash}\`\n`;
    }

    if (result.summary) {
      msg += `\n**Resumo:**\n${result.summary}\n`;
    }

    msg += '\n---\n_Deseja fazer deploy? Responda "deploy" ou "sim"._';

    return msg;
  }
}
EOF
```

### 8.2 Skill: DevOps

```bash
mkdir -p ~/moltbot-workspace/skills/devops

cat > ~/moltbot-workspace/skills/devops/index.ts << 'EOF'
import { Skill, Context } from 'moltbot';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface DeployResult {
  success: boolean;
  message: string;
  details?: string;
}

export default class DevOpsSkill extends Skill {
  name = 'devops';
  description = 'Gerencia deploys, logs e status de serviços';

  triggers = [
    'deploy', 'faz deploy', 'publica', 'publicar',
    'restart', 'reinicia', 'reiniciar',
    'logs', 'log', 'ver logs',
    'status', 'estado', 'health',
    'rollback', 'reverter'
  ];

  private workspaceRoot = process.env.CLAUDE_WORKSPACE || '/home/deploy/workspaces/medflow';
  private coolifyUrl = process.env.COOLIFY_API_URL || '';
  private coolifyToken = process.env.COOLIFY_API_TOKEN || '';

  async execute(ctx: Context): Promise<void> {
    const message = ctx.message.toLowerCase();

    try {
      if (this.matchesAny(message, ['deploy', 'publica'])) {
        await this.deploy(ctx);
      } else if (this.matchesAny(message, ['restart', 'reinicia'])) {
        await this.restart(ctx);
      } else if (this.matchesAny(message, ['logs', 'log'])) {
        await this.showLogs(ctx);
      } else if (this.matchesAny(message, ['status', 'estado', 'health'])) {
        await this.showStatus(ctx);
      } else if (this.matchesAny(message, ['rollback', 'reverter'])) {
        await this.rollback(ctx);
      } else {
        await ctx.reply('🤔 Comando não reconhecido. Use: deploy, restart, logs, status, ou rollback.');
      }
    } catch (error: any) {
      await ctx.reply(`❌ **Erro:**\n\`\`\`\n${error.message}\n\`\`\``);
    }
  }

  private matchesAny(text: string, keywords: string[]): boolean {
    return keywords.some(k => text.includes(k));
  }

  private async deploy(ctx: Context): Promise<void> {
    await ctx.reply('🚀 Iniciando deploy...');

    // 1. Git push
    await ctx.reply('📤 Fazendo push para origin...');
    try {
      await execAsync('git push origin main', { cwd: this.workspaceRoot });
    } catch (e: any) {
      if (!e.message.includes('Everything up-to-date')) {
        throw e;
      }
    }

    // 2. Trigger Coolify deploy
    await ctx.reply('🔄 Triggerando deploy no Coolify...');

    if (this.coolifyUrl && this.coolifyToken) {
      const response = await fetch(`${this.coolifyUrl}/api/v1/deploy`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.coolifyToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          uuid: 'medflow-forks', // ajustar conforme necessário
          force: false
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Coolify deploy failed: ${error}`);
      }
    }

    // 3. Aguardar e verificar
    await ctx.reply('⏳ Aguardando deploy...');
    await new Promise(r => setTimeout(r, 30000)); // 30s

    const status = await this.getServiceStatus('medflow-api');

    if (status.includes('Up') || status.includes('running')) {
      await ctx.reply('✅ **Deploy concluído com sucesso!**\n\nAplicação rodando em produção.');
    } else {
      await ctx.reply(`⚠️ **Deploy finalizado, mas status incerto:**\n\`\`\`\n${status}\n\`\`\``);
    }
  }

  private async restart(ctx: Context): Promise<void> {
    const service = this.extractService(ctx.message) || 'moltbot';

    await ctx.reply(`🔄 Reiniciando ${service}...`);

    if (service === 'moltbot') {
      await execAsync('sudo systemctl restart moltbot');
    } else if (service === 'crabwalk') {
      await execAsync('cd ~/crabwalk && docker compose restart');
    } else if (service === 'cloudflared') {
      await execAsync('sudo systemctl restart cloudflared');
    } else {
      await execAsync(`docker restart ${service}`);
    }

    await ctx.reply(`✅ **${service}** reiniciado com sucesso!`);
  }

  private async showLogs(ctx: Context, lines: number = 50): Promise<void> {
    const service = this.extractService(ctx.message) || 'moltbot';

    await ctx.reply(`📋 Buscando logs de ${service}...`);

    let logs: string;

    if (service === 'moltbot' || service === 'cloudflared') {
      const { stdout } = await execAsync(`journalctl -u ${service} --no-pager -n ${lines}`);
      logs = stdout;
    } else {
      const { stdout } = await execAsync(`docker logs --tail ${lines} ${service}`);
      logs = stdout;
    }

    // Truncar se muito longo
    const maxLen = 3000;
    if (logs.length > maxLen) {
      logs = '...(truncado)\n' + logs.slice(-maxLen);
    }

    await ctx.reply(`📋 **Logs de ${service}** (últimas ${lines} linhas):\n\`\`\`\n${logs}\n\`\`\``);
  }

  private async showStatus(ctx: Context): Promise<void> {
    const services = [
      { name: 'moltbot', cmd: 'systemctl is-active moltbot' },
      { name: 'cloudflared', cmd: 'systemctl is-active cloudflared' },
      { name: 'crabwalk', cmd: 'docker ps --filter name=crabwalk --format "{{.Status}}"' },
      { name: 'fail2ban', cmd: 'systemctl is-active fail2ban' },
    ];

    let status = '📊 **Status dos Serviços**\n\n';

    for (const svc of services) {
      try {
        const { stdout } = await execAsync(svc.cmd);
        const isUp = stdout.includes('active') || stdout.includes('Up');
        status += `${isUp ? '✅' : '❌'} **${svc.name}:** ${stdout.trim()}\n`;
      } catch {
        status += `❌ **${svc.name}:** offline\n`;
      }
    }

    // Disk usage
    try {
      const { stdout } = await execAsync("df -h / | awk 'NR==2 {print $5}'");
      status += `\n💾 **Disco:** ${stdout.trim()} usado`;
    } catch {}

    // Memory
    try {
      const { stdout } = await execAsync("free -h | awk 'NR==2 {print $3\"/\"$2}'");
      status += `\n🧠 **Memória:** ${stdout.trim()}`;
    } catch {}

    await ctx.reply(status);
  }

  private async rollback(ctx: Context): Promise<void> {
    await ctx.reply('⏪ Iniciando rollback...');

    // Pegar commit anterior
    const { stdout: prevCommit } = await execAsync('git rev-parse HEAD~1', { cwd: this.workspaceRoot });

    await ctx.reply(`📌 Revertendo para commit: \`${prevCommit.trim().slice(0, 7)}\``);

    // Criar commit de revert
    await execAsync(`git revert HEAD --no-edit`, { cwd: this.workspaceRoot });
    await execAsync(`git push origin main`, { cwd: this.workspaceRoot });

    // Trigger deploy
    await this.deploy(ctx);
  }

  private extractService(message: string): string | null {
    const services = ['moltbot', 'crabwalk', 'cloudflared', 'medflow-api', 'postgres', 'redis'];
    for (const svc of services) {
      if (message.toLowerCase().includes(svc)) {
        return svc;
      }
    }
    return null;
  }

  private async getServiceStatus(service: string): Promise<string> {
    try {
      const { stdout } = await execAsync(`docker ps --filter name=${service} --format "{{.Status}}"`);
      return stdout.trim() || 'not found';
    } catch {
      return 'error checking status';
    }
  }
}
EOF
```

### 8.3 Skill: Marketing (Bônus)

```bash
mkdir -p ~/moltbot-workspace/skills/marketing

cat > ~/moltbot-workspace/skills/marketing/index.ts << 'EOF'
import { Skill, Context } from 'moltbot';

export default class MarketingSkill extends Skill {
  name = 'marketing';
  description = 'Cria conteúdo de marketing para clínicas médicas';

  triggers = [
    'post', 'cria post', 'instagram', 'conteúdo',
    'copy', 'legenda', 'carrossel', 'reel',
    'anúncio', 'ad', 'campanha'
  ];

  systemPrompt = `
Você é um copywriter especializado em marketing médico brasileiro.

## Expertise
- Posts para Instagram (feed, carrossel, reels, stories)
- Legendas persuasivas com CTAs
- Hooks que capturam atenção nos primeiros 3 segundos
- Anúncios para Meta Ads

## Compliance CFM (OBRIGATÓRIO)
- NUNCA prometa resultados específicos ("garanto", "100%", "definitivo")
- NUNCA use fotos antes/depois sem mencionar que precisa de autorização
- NUNCA divulgue preços (diga "consulte valores")
- SEMPRE use linguagem educativa, não promocional
- SEMPRE inclua "Consulte um especialista" quando apropriado

## Formato de Entrega

Para posts de Instagram:

**🎯 HOOK** (primeira linha visível)
[Frase de impacto]

**📝 CORPO**
[Conteúdo educativo em 3-4 parágrafos curtos]

**👉 CTA**
[Chamada para ação clara]

**#️⃣ HASHTAGS**
[5-10 hashtags relevantes]

---

Para carrosséis, numere os slides:
[Slide 1] Capa com hook
[Slide 2-6] Conteúdo
[Slide 7] CTA
`;

  async execute(ctx: Context): Promise<void> {
    const request = ctx.message;

    const response = await ctx.llm.chat({
      system: this.systemPrompt,
      message: `Crie conteúdo de marketing conforme solicitado:\n\n${request}`,
      maxTokens: 2000
    });

    await ctx.reply(response);
  }
}
EOF
```

### 8.4 Registrar Skills

```bash
# Criar arquivo de índice dos skills
cat > ~/moltbot-workspace/skills/index.ts << 'EOF'
export { default as ClaudeCodeSkill } from './claude-code';
export { default as DevOpsSkill } from './devops';
export { default as MarketingSkill } from './marketing';
EOF
```

---

## Parte 9: Aprovar Pairings

### 9.1 Iniciar e Verificar Serviços

```bash
# Reiniciar Moltbot para carregar skills
sudo systemctl restart moltbot

# Verificar logs
journalctl -u moltbot -f
```

### 9.2 Aprovar Telegram

1. Envie qualquer mensagem para seu bot no Telegram
2. Você receberá um código de pairing (ex: `ABC123`)
3. No servidor:

```bash
# Listar pairings pendentes
moltbot pairing list

# Aprovar
moltbot pairing approve telegram ABC123
```

### 9.3 Aprovar Dashboard (Crabwalk)

1. Acesse: `https://moltbot.trafegoparaconsultorios.com.br`
2. Faça login via Cloudflare Access
3. Verá "pairing required"
4. No servidor:

```bash
moltbot pairing list
moltbot pairing approve web <CODE>
```

---

## Parte 10: Verificação Final

### 10.1 Script de Verificação

```bash
#!/bin/bash
echo "=========================================="
echo "   VERIFICAÇÃO DE SEGURANÇA - MOLTBOT    "
echo "=========================================="

echo -e "\n[1/10] SSH Password Auth:"
grep -E "^PasswordAuthentication" /etc/ssh/sshd_config || echo "Não encontrado"

echo -e "\n[2/10] SSH Root Login:"
grep -E "^PermitRootLogin" /etc/ssh/sshd_config || echo "Não encontrado"

echo -e "\n[3/10] UFW Status:"
sudo ufw status | head -3

echo -e "\n[4/10] Portas Públicas (deve ser só 22):"
sudo ss -tlnp | grep -v "127.0.0.1" | grep LISTEN

echo -e "\n[5/10] Fail2ban:"
sudo systemctl is-active fail2ban

echo -e "\n[6/10] Moltbot:"
sudo systemctl is-active moltbot

echo -e "\n[7/10] Crabwalk:"
docker ps --filter name=crabwalk --format "{{.Names}}: {{.Status}}"

echo -e "\n[8/10] Cloudflared:"
sudo systemctl is-active cloudflared

echo -e "\n[9/10] Claude Code:"
which claude && claude --version

echo -e "\n[10/10] Gateway Binding (deve ser 127.0.0.1):"
sudo ss -tlnp | grep 18789

echo -e "\n=========================================="
echo "   VERIFICAÇÃO COMPLETA                   "
echo "=========================================="
```

### 10.2 Testar Fluxo Completo

No Telegram, envie:

```
Olá
```
→ Deve responder normalmente

```
status
```
→ Deve mostrar status dos serviços

```
Implementa uma função de hello world em utils/test.ts
```
→ Deve invocar Claude Code e criar o arquivo

```
deploy
```
→ Deve fazer push e deploy

---

## Comandos de Referência Rápida

```bash
# === MOLTBOT ===
sudo systemctl status moltbot
sudo systemctl restart moltbot
journalctl -u moltbot -f
moltbot pairing list
moltbot pairing approve <channel> <code>

# === CRABWALK ===
cd ~/crabwalk && docker compose logs -f
cd ~/crabwalk && docker compose restart
cd ~/crabwalk && docker compose pull && docker compose up -d

# === CLOUDFLARE ===
sudo systemctl status cloudflared
sudo systemctl restart cloudflared
cloudflared tunnel list

# === CLAUDE CODE ===
claude --version
claude -p "sua tarefa aqui"

# === SEGURANÇA ===
sudo fail2ban-client status sshd
sudo ufw status verbose

# === ATUALIZAÇÕES ===
sudo npm update -g moltbot@latest
sudo npm update -g @anthropic-ai/claude-code
sudo apt update && sudo apt upgrade -y
```

---

## Estrutura Final de Arquivos

```
/etc/
├── moltbot.env                              # Secrets (API keys)
├── ssh/sshd_config                          # SSH hardened
├── fail2ban/jail.local                      # Fail2ban config
└── systemd/system/
    ├── moltbot.service                      # Moltbot daemon
    └── cloudflared.service                  # Tunnel daemon

/home/deploy/
├── .clawdbot/
│   └── moltbot.json                         # Config Moltbot
├── .cloudflared/
│   ├── cert.pem                             # Cert Cloudflare
│   ├── <UUID>.json                          # Credentials tunnel
│   └── config.yml                           # Config tunnel
├── .claude/
│   └── settings.json                        # Config Claude Code
├── .moltbot_gateway_token                   # Token do gateway
├── bin/
│   └── claude-task                          # Wrapper script
├── moltbot-workspace/
│   ├── AGENTS.md                            # Personalidade
│   └── skills/
│       ├── index.ts                         # Exports
│       ├── claude-code/index.ts             # Skill de coding
│       ├── devops/index.ts                  # Skill de deploy
│       └── marketing/index.ts               # Skill de marketing
├── workspaces/
│   └── medflow/                             # Repo clonado
└── crabwalk/
    ├── docker-compose.yml                   # Container Crabwalk
    └── .env                                 # Token para Crabwalk
```

---

## Defense in Depth Final

```
┌─────────────────────────────────────────────────────────────┐
│                    7 CAMADAS DE SEGURANÇA                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Cloudflare Access                                        │
│     └─ Identity + MFA antes de qualquer acesso               │
│                                                              │
│  2. Cloudflare Tunnel                                        │
│     └─ Zero portas públicas (exceto SSH)                     │
│     └─ Conexão outbound only                                 │
│                                                              │
│  3. Gateway Token                                            │
│     └─ 256-bit random token                                  │
│                                                              │
│  4. Device Pairing                                           │
│     └─ Aprovação explícita por device                        │
│                                                              │
│  5. UFW Firewall                                             │
│     └─ Deny all incoming exceto SSH                          │
│                                                              │
│  6. Fail2ban                                                 │
│     └─ Auto-ban após 3 tentativas                            │
│                                                              │
│  7. SSH Hardening                                            │
│     └─ Keys only, no root, no password                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

*Última atualização: 2026-01-27*
*Stack: Moltbot + Crabwalk + Claude Code + Cloudflare Zero Trust*
