# Moltbot Production Setup — Seguro com Cloudflare Tunnel

> **Stack Final**: Moltbot + Crabwalk + Cloudflare Tunnel + Zero Trust + SSH Hardening

---

## Arquitetura de Segurança

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CLOUDFLARE EDGE                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │  Zero Trust     │    │   TLS/HTTPS     │    │   DDoS Shield   │      │
│  │  Access Gate    │    │   Termination   │    │                 │      │
│  │  (Identity+MFA) │    │                 │    │                 │      │
│  └────────┬────────┘    └────────┬────────┘    └─────────────────┘      │
│           │                      │                                       │
│           └──────────────────────┘                                       │
│                          │                                               │
│              ┌───────────▼───────────┐                                   │
│              │   Cloudflare Tunnel   │                                   │
│              │   (Outbound Only)     │                                   │
│              └───────────┬───────────┘                                   │
└──────────────────────────┼──────────────────────────────────────────────┘
                           │
              ═════════════╪═══════════════  (Encrypted Tunnel)
                           │
┌──────────────────────────▼──────────────────────────────────────────────┐
│                         KVM 8 (VPS)                                      │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    127.0.0.1 (localhost only)                    │   │
│   │                                                                  │   │
│   │  ┌─────────────────┐              ┌─────────────────┐           │   │
│   │  │   Moltbot       │◄────────────►│   Crabwalk      │           │   │
│   │  │   Gateway       │   WebSocket  │   Dashboard     │           │   │
│   │  │   :18789        │              │   :3000         │           │   │
│   │  └─────────────────┘              └─────────────────┘           │   │
│   │           │                                                      │   │
│   │           ▼                                                      │   │
│   │  ┌─────────────────┐                                            │   │
│   │  │   Telegram      │                                            │   │
│   │  │   Bot API       │                                            │   │
│   │  │   (Outbound)    │                                            │   │
│   │  └─────────────────┘                                            │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   Firewall: UFW (only SSH inbound)                                       │
│   fail2ban: SSH brute-force protection                                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

RESULTADO:
✅ Nenhuma porta pública exposta (exceto SSH)
✅ Dashboard só acessível via Cloudflare (com identity check)
✅ VPS IP não aparece no Shodan
✅ Defense-in-depth: Access → Token → Pairing
```

---

## Pré-requisitos

| Item | Onde Obter |
|------|------------|
| Domínio no Cloudflare | https://dash.cloudflare.com |
| API Key Anthropic | https://console.anthropic.com |
| Token Telegram Bot | @BotFather |
| SSH Key configurada | `ssh-keygen -t ed25519` |
| Acesso SSH à KVM 8 | Suas credenciais |

---

## Parte 1: Setup Base do Servidor

### 1.1 Conectar e Atualizar

```bash
# Conectar
ssh deploy@kvm8.trafegoparaconsultorios.com.br

# Atualizar sistema
sudo apt update && sudo apt upgrade -y
```

### 1.2 Criar Usuário Deploy (se não existir)

```bash
# Como root, criar usuário
sudo adduser deploy
sudo usermod -aG sudo deploy

# Copiar sua SSH key para o novo usuário
sudo mkdir -p /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# Testar login em outra janela antes de continuar!
ssh deploy@kvm8.trafegoparaconsultorios.com.br
```

### 1.3 Hardening SSH

```bash
sudo nano /etc/ssh/sshd_config
```

Configurar:
```bash
# Segurança básica
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no

# Limitar usuários
AllowUsers deploy

# Timeout
ClientAliveInterval 300
ClientAliveCountMax 2

# Desabilitar features desnecessárias
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
```

```bash
# Validar config antes de aplicar
sudo sshd -t

# Se ok, reiniciar (MANTENHA A SESSÃO ATUAL ABERTA!)
sudo systemctl restart ssh

# Testar em OUTRA janela
ssh deploy@kvm8.trafegoparaconsultorios.com.br
```

### 1.4 Firewall UFW

```bash
# Instalar UFW
sudo apt install -y ufw

# Configurar regras ANTES de ativar
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH (IMPORTANTE: fazer isso ANTES de enable)
sudo ufw allow OpenSSH

# Ativar
sudo ufw enable

# Verificar
sudo ufw status verbose
```

**Output esperado:**
```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp (OpenSSH)           ALLOW IN    Anywhere
```

### 1.5 Fail2ban

```bash
# Instalar
sudo apt install -y fail2ban

# Criar config local
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

Adicionar/modificar:
```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
```

```bash
# Iniciar
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Verificar
sudo fail2ban-client status sshd
```

---

## Parte 2: Instalar Node.js e Moltbot

### 2.1 Node.js 22

```bash
# Instalar Node 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar
node --version  # v22.x.x
npm --version
```

### 2.2 Moltbot

```bash
# Instalar globalmente
sudo npm install -g moltbot@latest

# Verificar
moltbot --version
moltbot doctor
```

### 2.3 Configuração Moltbot

```bash
# Criar diretórios
mkdir -p ~/.clawdbot
mkdir -p ~/moltbot-workspace/skills

# Criar arquivo de secrets (NÃO commitar!)
sudo nano /etc/moltbot.env
```

Conteúdo de `/etc/moltbot.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-sua-key-aqui
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

```bash
# Proteger arquivo
sudo chmod 600 /etc/moltbot.env
sudo chown deploy:deploy /etc/moltbot.env
```

### 2.4 Config Principal do Moltbot

```bash
cat > ~/.clawdbot/moltbot.json << 'EOF'
{
  "agent": {
    "model": "anthropic/claude-sonnet-4-20250514",
    "thinking": "medium"
  },
  "gateway": {
    "port": 18789,
    "bind": "127.0.0.1",
    "auth": {
      "mode": "token",
      "token": "GERAR_TOKEN_SEGURO_AQUI"
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
    "root": "~/moltbot-workspace"
  },
  "security": {
    "pairing": {
      "enabled": true,
      "requireApproval": true
    }
  }
}
EOF
```

**Gerar token seguro:**
```bash
# Gerar token aleatório
TOKEN=$(openssl rand -hex 32)
echo "Seu token: $TOKEN"

# Atualizar no config
sed -i "s/GERAR_TOKEN_SEGURO_AQUI/$TOKEN/" ~/.clawdbot/moltbot.json

# Salvar para usar depois
echo $TOKEN > ~/.clawdbot/.gateway_token
chmod 600 ~/.clawdbot/.gateway_token
```

### 2.5 Workspace e Personalidade

```bash
cat > ~/moltbot-workspace/AGENTS.md << 'EOF'
# MedFlow AI Assistant

Você é o assistente de IA da MedFlow, plataforma de marketing para clínicas médicas.

## Personalidade
- Profissional, competente e acolhedor
- Respostas concisas e acionáveis
- Tom consultivo, não robótico

## Expertise
- Marketing digital para área médica
- Gestão de tráfego pago (Meta Ads, Google Ads)
- Criação de conteúdo para Instagram/TikTok
- Atendimento e agendamento de consultas
- CRM e automações

## Compliance Obrigatório (CFM)
- NUNCA prometa resultados específicos de procedimentos
- NUNCA divulgue preços publicamente
- NUNCA use fotos antes/depois sem autorização documentada
- SEMPRE sugira agendamento para discussão de valores
- SEMPRE mantenha sigilo médico (LGPD)

## Formato de Respostas
- Máximo 3 parágrafos para respostas gerais
- Use bullet points para listas
- Seja direto ao ponto
- Emojis com moderação (máx 2 por mensagem)
EOF
```

### 2.6 Serviço Systemd do Moltbot

```bash
sudo cat > /etc/systemd/system/moltbot.service << 'EOF'
[Unit]
Description=Moltbot AI Assistant Gateway
After=network.target
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
ReadWritePaths=/home/deploy/.clawdbot /home/deploy/moltbot-workspace
PrivateTmp=true

# Limites
LimitNOFILE=65535
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF
```

```bash
# Ativar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable moltbot
sudo systemctl start moltbot

# Verificar
sudo systemctl status moltbot
journalctl -u moltbot -f
```

---

## Parte 3: Instalar Crabwalk (Dashboard)

### 3.1 Instalar Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sudo sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker deploy

# Relogar para aplicar grupo
exit
ssh deploy@kvm8.trafegoparaconsultorios.com.br

# Verificar
docker --version
docker run hello-world
```

### 3.2 Criar Docker Compose para Crabwalk

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
      - "127.0.0.1:3000:3000"  # Apenas localhost!
    environment:
      - CLAWDBOT_API_TOKEN=${CLAWDBOT_API_TOKEN}
      - CLAWDBOT_URL=ws://host.docker.internal:18789
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - moltbot-net

networks:
  moltbot-net:
    driver: bridge
EOF
```

### 3.3 Criar arquivo .env para Crabwalk

```bash
# Pegar o token do moltbot
GATEWAY_TOKEN=$(cat ~/.clawdbot/.gateway_token)

cat > ~/crabwalk/.env << EOF
CLAWDBOT_API_TOKEN=$GATEWAY_TOKEN
EOF

chmod 600 ~/crabwalk/.env
```

### 3.4 Iniciar Crabwalk

```bash
cd ~/crabwalk
docker compose up -d

# Verificar
docker compose logs -f

# Testar localmente
curl http://127.0.0.1:3000
```

---

## Parte 4: Cloudflare Tunnel (Zero Trust Network)

### 4.1 Instalar Cloudflared

```bash
# Adicionar repo Cloudflare
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Instalar
sudo apt update
sudo apt install -y cloudflared

# Verificar
cloudflared --version
```

### 4.2 Autenticar no Cloudflare

```bash
cloudflared tunnel login
```

Isso abre um link no browser. Selecione seu domínio e autorize.
Será criado: `~/.cloudflared/cert.pem`

### 4.3 Criar Tunnel

```bash
# Criar tunnel
cloudflared tunnel create medflow-moltbot

# Isso cria: ~/.cloudflared/<UUID>.json
# Anote o UUID!

# Listar tunnels
cloudflared tunnel list
```

### 4.4 Configurar Tunnel

```bash
# Pegar o UUID do tunnel
TUNNEL_UUID=$(cloudflared tunnel list | grep medflow-moltbot | awk '{print $1}')
echo "Tunnel UUID: $TUNNEL_UUID"

# Criar config
cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_UUID
credentials-file: /home/deploy/.cloudflared/$TUNNEL_UUID.json

ingress:
  # Dashboard Crabwalk
  - hostname: moltbot.trafegoparaconsultorios.com.br
    service: http://127.0.0.1:3000

  # Gateway WebSocket (para conexões remotas)
  - hostname: gateway.trafegoparaconsultorios.com.br
    service: http://127.0.0.1:18789

  # Fallback obrigatório
  - service: http_status:404
EOF
```

### 4.5 Criar DNS Records

```bash
# Criar DNS para dashboard
cloudflared tunnel route dns medflow-moltbot moltbot.trafegoparaconsultorios.com.br

# Criar DNS para gateway
cloudflared tunnel route dns medflow-moltbot gateway.trafegoparaconsultorios.com.br
```

### 4.6 Testar Tunnel (Foreground)

```bash
cloudflared tunnel run medflow-moltbot
```

Em outro terminal, testar:
```bash
curl https://moltbot.trafegoparaconsultorios.com.br
```

Se funcionar, Ctrl+C e continuar.

### 4.7 Instalar como Serviço

```bash
# Instalar serviço
sudo cloudflared --config /home/deploy/.cloudflared/config.yml service install

# Habilitar e iniciar
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Verificar
sudo systemctl status cloudflared
journalctl -u cloudflared -f
```

---

## Parte 5: Cloudflare Access (Identity Gate)

### 5.1 Configurar no Dashboard Cloudflare

1. Acesse: https://one.dash.cloudflare.com/
2. Selecione sua conta
3. Vá em **Access** → **Applications**
4. Clique **Add an application**
5. Selecione **Self-hosted**

### 5.2 Configurar Application: Dashboard

**Application Configuration:**
- Application name: `MedFlow Moltbot Dashboard`
- Session Duration: `24 hours`
- Application domain: `moltbot.trafegoparaconsultorios.com.br`

**Policy Configuration:**
- Policy name: `Allow MedFlow Team`
- Action: `Allow`
- Include:
  - **Emails**: `seu@email.com`
  - (Ou) **Emails ending in**: `@suaempresa.com`
  - (Ou) **Login Methods**: `GitHub` / `Google`

**Adicionar regra de Deny-All:**
- Policy name: `Deny All Others`
- Action: `Block`
- Include: `Everyone`

### 5.3 Configurar Application: Gateway (opcional)

Repita para `gateway.trafegoparaconsultorios.com.br` com as mesmas políticas.

### 5.4 Habilitar MFA (Recomendado)

1. Vá em **Settings** → **Authentication**
2. Em **Login methods**, adicione:
   - One-time PIN (email)
   - Google / GitHub
3. Em **MFA**, configure:
   - Require MFA for all users

---

## Parte 6: Aprovar Pairing

### 6.1 Acessar Dashboard pela Primeira Vez

1. Acesse: `https://moltbot.trafegoparaconsultorios.com.br`
2. Cloudflare Access vai pedir login (email ou GitHub)
3. Após autenticar, você verá o dashboard do Crabwalk
4. Pode aparecer: `disconnected (1008): pairing required`

### 6.2 Aprovar Device do Dashboard

```bash
# No servidor, listar pairings pendentes
moltbot pairing list

# Aprovar o dashboard
moltbot pairing approve <CÓDIGO>
```

### 6.3 Aprovar seu Telegram

1. Envie uma mensagem para seu bot no Telegram
2. Você receberá um código de pairing
3. No servidor:

```bash
moltbot pairing approve telegram <CÓDIGO>
```

---

## Parte 7: Verificação Final

### 7.1 Checklist de Segurança

```bash
# Executar verificações
echo "=== Verificação de Segurança ==="

# 1. SSH não aceita password
echo -n "SSH Password Auth: "
grep -E "^PasswordAuthentication" /etc/ssh/sshd_config

# 2. SSH não aceita root
echo -n "SSH Root Login: "
grep -E "^PermitRootLogin" /etc/ssh/sshd_config

# 3. UFW ativo
echo -n "UFW Status: "
sudo ufw status | head -1

# 4. Portas abertas (deve ser só SSH)
echo "Portas listening:"
sudo ss -tlnp | grep LISTEN

# 5. Fail2ban rodando
echo -n "Fail2ban: "
sudo systemctl is-active fail2ban

# 6. Moltbot rodando
echo -n "Moltbot: "
sudo systemctl is-active moltbot

# 7. Crabwalk rodando
echo -n "Crabwalk: "
docker ps --filter name=crabwalk --format "{{.Status}}"

# 8. Cloudflared rodando
echo -n "Cloudflared: "
sudo systemctl is-active cloudflared

# 9. Gateway só em localhost
echo -n "Gateway binding: "
sudo ss -tlnp | grep 18789

# 10. Crabwalk só em localhost
echo -n "Crabwalk binding: "
sudo ss -tlnp | grep 3000
```

**Output esperado:**
```
=== Verificação de Segurança ===
SSH Password Auth: PasswordAuthentication no
SSH Root Login: PermitRootLogin no
UFW Status: Status: active
Portas listening:
LISTEN  0  128  127.0.0.1:18789  *  users:(("node",pid=xxx))
LISTEN  0  128  127.0.0.1:3000   *  users:(("node",pid=xxx))
LISTEN  0  128  0.0.0.0:22       *  users:(("sshd",pid=xxx))
Fail2ban: active
Moltbot: active
Crabwalk: Up 2 minutes
Cloudflared: active
Gateway binding: 127.0.0.1:18789
Crabwalk binding: 127.0.0.1:3000
```

### 7.2 Testar Acesso Externo

```bash
# Do seu computador local (NÃO do servidor):

# 1. Tentar acessar porta diretamente (DEVE FALHAR)
curl http://IP_DO_SERVIDOR:18789
# Timeout ou connection refused ✓

# 2. Tentar acessar via Cloudflare (DEVE PEDIR LOGIN)
curl -I https://moltbot.trafegoparaconsultorios.com.br
# 302 redirect para Cloudflare Access ✓

# 3. Verificar Shodan (depois de 24h)
# https://www.shodan.io/host/IP_DO_SERVIDOR
# Não deve mostrar porta 18789 ou 3000
```

### 7.3 Testar Telegram

1. Envie mensagem para seu bot
2. Deve responder normalmente
3. Verifique no Crabwalk se a sessão aparece no grafo

---

## Comandos de Manutenção

### Logs

```bash
# Moltbot
journalctl -u moltbot -f

# Cloudflared
journalctl -u cloudflared -f

# Crabwalk
cd ~/crabwalk && docker compose logs -f

# Fail2ban
sudo fail2ban-client status sshd
```

### Restart

```bash
# Moltbot
sudo systemctl restart moltbot

# Crabwalk
cd ~/crabwalk && docker compose restart

# Cloudflared
sudo systemctl restart cloudflared
```

### Atualizar

```bash
# Moltbot
sudo npm update -g moltbot@latest
sudo systemctl restart moltbot

# Crabwalk
cd ~/crabwalk
docker compose pull
docker compose up -d

# Sistema
sudo apt update && sudo apt upgrade -y
```

### Pairing

```bash
# Listar
moltbot pairing list

# Aprovar
moltbot pairing approve <channel> <code>

# Revogar
moltbot pairing revoke <channel> <device-id>
```

---

## Estrutura Final de Arquivos

```
/etc/
├── moltbot.env                          # Secrets (API keys)
├── ssh/sshd_config                      # SSH hardened
├── fail2ban/jail.local                  # Fail2ban config
└── systemd/system/
    ├── moltbot.service                  # Moltbot daemon
    └── cloudflared.service              # Tunnel daemon

/home/deploy/
├── .clawdbot/
│   ├── moltbot.json                     # Config principal
│   └── .gateway_token                   # Token do gateway
├── .cloudflared/
│   ├── cert.pem                         # Certificado Cloudflare
│   ├── <UUID>.json                      # Credenciais tunnel
│   └── config.yml                       # Config tunnel
├── moltbot-workspace/
│   ├── AGENTS.md                        # Personalidade
│   └── skills/                          # Skills customizados
└── crabwalk/
    ├── docker-compose.yml               # Crabwalk container
    └── .env                             # Token para Crabwalk
```

---

## Stack de Segurança Final

```
┌─────────────────────────────────────────────────────────────┐
│                    DEFENSE IN DEPTH                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Cloudflare Access                                  │
│           └─ Identity verification (email/GitHub/MFA)        │
│                                                              │
│  Layer 2: Cloudflare Tunnel                                  │
│           └─ No public ports exposed                         │
│           └─ TLS encryption                                  │
│                                                              │
│  Layer 3: Gateway Token                                      │
│           └─ 256-bit random token                            │
│                                                              │
│  Layer 4: Device Pairing                                     │
│           └─ Explicit approval required                      │
│           └─ Per-device trust                                │
│                                                              │
│  Layer 5: Firewall (UFW)                                     │
│           └─ Only SSH inbound                                │
│                                                              │
│  Layer 6: Fail2ban                                           │
│           └─ Auto-ban brute force                            │
│                                                              │
│  Layer 7: SSH Hardening                                      │
│           └─ Keys only, no root, no password                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### 502 Bad Gateway no Cloudflare

```bash
# Verificar se serviços estão rodando
sudo systemctl status moltbot
docker ps

# Verificar se estão em localhost
sudo ss -tlnp | grep -E "18789|3000"

# Verificar logs do tunnel
journalctl -u cloudflared -n 50
```

### Pairing Required (1008)

```bash
# Listar e aprovar
moltbot pairing list
moltbot pairing approve <code>
```

### Telegram não responde

```bash
# Verificar logs
journalctl -u moltbot | grep -i telegram

# Verificar token
cat /etc/moltbot.env | grep TELEGRAM

# Testar token
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Cloudflare Access loop infinito

1. Limpe cookies do browser para o domínio
2. Tente em aba anônima
3. Verifique se seu email está na policy de Allow

---

*Setup criado em: 2026-01-27*
*Baseado em: Moltbot + Crabwalk + Cloudflare Zero Trust*
