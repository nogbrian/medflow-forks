# Setup Moltbot na KVM 8 com Telegram

> **Objetivo**: Instalar Moltbot no servidor KVM 8 e conectar via Telegram

---

## Pré-requisitos

- Acesso SSH à KVM 8
- Node.js ≥ 22
- Conta Anthropic com API Key
- Conta Telegram para criar bot

---

## Passo 1: Conectar à KVM 8

```bash
ssh root@kvm8.trafegoparaconsultorios.com.br
# ou o IP/hostname correto da sua KVM 8
```

---

## Passo 2: Instalar Node.js 22

```bash
# Verificar versão atual
node --version

# Se < 22, instalar via NodeSource
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar instalação
node --version  # Deve mostrar v22.x.x
npm --version
```

---

## Passo 3: Instalar Moltbot

```bash
# Instalar globalmente
npm install -g moltbot@latest

# Verificar instalação
moltbot --version

# Rodar diagnóstico
moltbot doctor
```

---

## Passo 4: Criar Bot no Telegram

1. Abra o Telegram no celular ou desktop
2. Procure por **@BotFather**
3. Envie `/newbot`
4. Siga as instruções:
   - **Nome do bot**: `MedFlow Assistant` (ou o que preferir)
   - **Username**: `medflow_assistant_bot` (deve terminar em `bot`)
5. **COPIE O TOKEN** que o BotFather enviar (formato: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Configurações opcionais no BotFather:

```
/setdescription - Definir descrição do bot
/setabouttext - Texto "Sobre" do bot
/setuserpic - Foto de perfil do bot
/setprivacy - DISABLE (para funcionar em grupos sem mention)
```

---

## Passo 5: Obter API Key da Anthropic

1. Acesse: https://console.anthropic.com/
2. Vá em **API Keys**
3. Crie uma nova key ou copie existente
4. **GUARDE A KEY** (formato: `sk-ant-api03-...`)

---

## Passo 6: Configurar Variáveis de Ambiente

```bash
# Criar arquivo de ambiente
sudo nano /etc/moltbot.env
```

Conteúdo:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-sua-key-aqui
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

```bash
# Proteger o arquivo
sudo chmod 600 /etc/moltbot.env
```

---

## Passo 7: Criar Configuração do Moltbot

```bash
# Criar diretório de config
mkdir -p ~/.clawdbot

# Criar arquivo de configuração
cat > ~/.clawdbot/moltbot.json << 'EOF'
{
  "agent": {
    "model": "anthropic/claude-sonnet-4-20250514",
    "thinking": "medium"
  },
  "gateway": {
    "port": 18789,
    "bind": "127.0.0.1"
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
  }
}
EOF
```

### Opções de modelo:

| Modelo | Uso | Custo |
|--------|-----|-------|
| `anthropic/claude-sonnet-4-20250514` | Balanceado (recomendado) | $$ |
| `anthropic/claude-opus-4-5-20251101` | Máxima qualidade | $$$$ |
| `anthropic/claude-haiku-3-5-20241022` | Rápido e barato | $ |

---

## Passo 8: Criar Workspace

```bash
# Criar diretório do workspace
mkdir -p ~/moltbot-workspace/skills

# Criar arquivo AGENTS.md (personalidade do bot)
cat > ~/moltbot-workspace/AGENTS.md << 'EOF'
# MedFlow Assistant

Você é o assistente de IA da MedFlow, uma plataforma de marketing médico.

## Personalidade
- Profissional mas acolhedor
- Respostas concisas e diretas
- Foco em ajudar com tarefas de marketing e atendimento

## Capacidades
- Responder dúvidas sobre marketing médico
- Ajudar com criação de conteúdo
- Auxiliar em estratégias de tráfego pago
- Suporte a automações

## Compliance
- Nunca prometa resultados garantidos
- Respeite as normas do CFM
- Mantenha privacidade de dados (LGPD)
EOF
```

---

## Passo 9: Criar Serviço Systemd

```bash
# Criar arquivo de serviço
sudo cat > /etc/systemd/system/moltbot.service << 'EOF'
[Unit]
Description=Moltbot AI Assistant Gateway
After=network.target

[Service]
Type=simple
User=root
EnvironmentFile=/etc/moltbot.env
ExecStart=/usr/bin/moltbot gateway --port 18789 --verbose
Restart=always
RestartSec=10

# Logs
StandardOutput=journal
StandardError=journal

# Limites
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar para iniciar no boot
sudo systemctl enable moltbot

# Iniciar o serviço
sudo systemctl start moltbot

# Verificar status
sudo systemctl status moltbot
```

---

## Passo 10: Verificar Logs

```bash
# Ver logs em tempo real
journalctl -u moltbot -f

# Ver últimas 100 linhas
journalctl -u moltbot -n 100

# Ver logs desde o início do serviço
journalctl -u moltbot --no-pager
```

Você deve ver algo como:
```
[moltbot] Gateway starting on ws://127.0.0.1:18789
[moltbot] Telegram channel initializing...
[moltbot] Telegram bot @medflow_assistant_bot connected
[moltbot] Ready to receive messages
```

---

## Passo 11: Aprovar seu Telegram (Pairing)

1. **No Telegram**, envie qualquer mensagem para seu bot (ex: `Olá`)

2. O bot vai responder com um **código de pairing** (ex: `ABC123`)

3. **No servidor**, aprove o pairing:

```bash
# Listar pairings pendentes
moltbot pairing list telegram

# Aprovar seu pairing
moltbot pairing approve telegram ABC123
```

4. **Pronto!** Agora o bot vai responder suas mensagens.

---

## Passo 12: Testar

No Telegram, envie mensagens para seu bot:

```
Você: Olá, quem é você?
Bot: Sou o MedFlow Assistant, um assistente de IA especializado em marketing médico...

Você: Me ajude a criar um post para Instagram sobre harmonização facial
Bot: [Gera conteúdo seguindo as diretrizes do AGENTS.md]
```

---

## Comandos Úteis

```bash
# Status do serviço
sudo systemctl status moltbot

# Reiniciar
sudo systemctl restart moltbot

# Parar
sudo systemctl stop moltbot

# Ver logs
journalctl -u moltbot -f

# Verificar saúde
moltbot doctor

# Listar pairings
moltbot pairing list telegram

# Aprovar pairing
moltbot pairing approve telegram <CODE>

# Enviar mensagem direta (teste)
moltbot message send --channel telegram --to @seu_username --message "Teste"

# Atualizar moltbot
npm update -g moltbot@latest
sudo systemctl restart moltbot
```

---

## Troubleshooting

### Bot não responde no Telegram

1. Verifique se o serviço está rodando:
```bash
sudo systemctl status moltbot
```

2. Verifique os logs:
```bash
journalctl -u moltbot -n 50
```

3. Verifique se o token está correto:
```bash
cat /etc/moltbot.env
```

4. Verifique se você aprovou o pairing:
```bash
moltbot pairing list telegram
```

### Erro de API Key

```
Error: Invalid API key
```

Solução:
```bash
# Verificar a key
cat /etc/moltbot.env

# Testar a key diretamente
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

### Erro de conexão Telegram

```
Error: 401 Unauthorized
```

Solução: Token do Telegram incorreto. Crie um novo bot no @BotFather.

### Gateway não inicia

```bash
# Verificar se a porta está em uso
sudo lsof -i :18789

# Matar processo se necessário
sudo kill -9 <PID>

# Reiniciar
sudo systemctl restart moltbot
```

### Permissão negada

```bash
# Garantir que o diretório existe e tem permissões
mkdir -p ~/.clawdbot
chmod 755 ~/.clawdbot
```

---

## Configuração Avançada: Grupos do Telegram

Para usar o bot em grupos:

1. **Desabilite Privacy Mode** no BotFather:
```
/setprivacy
Selecione seu bot
Disable
```

2. **Adicione o bot ao grupo**

3. **Configure no moltbot.json** (já feito no passo 7):
```json
"groups": {
  "*": {
    "requireMention": false
  }
}
```

4. Ou para grupos específicos:
```json
"groups": {
  "-1001234567890": {
    "requireMention": false,
    "allowFrom": ["username1", "username2"]
  }
}
```

---

## Próximos Passos

Depois que o bot estiver funcionando:

1. **Criar skills customizados** em `~/moltbot-workspace/skills/`
2. **Integrar com Twenty CRM** (ver CLAWDBOT_INTEGRATION_PLAN.md)
3. **Adicionar WhatsApp** (habilitar no moltbot.json)
4. **Configurar tools** para Cal.com e outras APIs

---

## Estrutura Final de Arquivos

```
/etc/
├── moltbot.env                 # API keys (protegido)
└── systemd/system/
    └── moltbot.service         # Serviço systemd

~/.clawdbot/
└── moltbot.json                # Configuração principal

~/moltbot-workspace/
├── AGENTS.md                   # Personalidade do bot
├── SOUL.md                     # (opcional) Diretrizes extras
├── TOOLS.md                    # (opcional) Tools disponíveis
└── skills/                     # Skills customizados
    └── medflow/
        ├── atendimento.ts
        └── marketing.ts
```

---

*Criado em: 2025-01-27*
