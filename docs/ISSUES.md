# Problemas Encontrados na Auditoria
## Tráfego para Consultórios - Stack Unificada
**Data:** 2026-01-22

---

## PROBLEMAS CRÍTICOS

### 1. ~~Cal.com NÃO EXISTE~~ RESOLVIDO
- **Severidade:** ~~CRÍTICA~~ RESOLVIDO
- **Descrição:** Cal.com deployado com sucesso
- **UUID:** `bk0k00wkoog8ck48c4k8k4gc`
- **Status:** running:healthy
- **Endpoint Temp:** http://calcom-bk0k00wkoog8ck48c4k8k4gc.72.61.37.176.sslip.io
- **Endpoint Final:** https://agenda.trafegoparaconsultorios.com.br

---

### 2. Creative Studio retornando 503
- **Severidade:** MÉDIA
- **Descrição:** O container creative-studio existe mas não está servindo
- **Endpoint:** https://studio.trafegoparaconsultorios.com.br
- **Possível Causa:** GEMINI_API_KEY não configurada
- **Ação:** Verificar logs e configurar API key

---

### 3. Bancos de Dados Isolados (Não Centralizados)
- **Severidade:** INFORMACIONAL
- **Descrição:** Cada serviço (Twenty, Chatwoot, Evolution) usa seu próprio PostgreSQL e Redis
- **Impacto:**
  - Mais consumo de recursos
  - Dados não compartilhados diretamente
  - Backups mais complexos
- **Decisão Necessária:** Migrar para banco central ou manter isolado?

**Bancos atuais:**
| Serviço | PostgreSQL | Redis |
|---------|------------|-------|
| Twenty | twenty-db (interno) | twenty-redis (interno) |
| Chatwoot | postgres-z0o4ck00... (interno) | redis-z0o4ck00... (interno) |
| Evolution | postgres-jscos8sg... (interno) | redis-jscos8sg... (interno) |
| MedFlow | v08k4wg4cc... (Coolify DB) | r8gc48w4wgs... (Coolify DB) |

---

### 4. ~~Twenty CRM - Conflito de Rotas Traefik + Conflito DNS PostgreSQL~~ TOTALMENTE RESOLVIDO
- **Severidade:** ~~CRÍTICA~~ RESOLVIDO
- **UUID:** `m8w8gso08k44wc0cs4oswosg`
- **Descrição:** Dois problemas identificados e corrigidos:

**Problema 1: Conflito de Labels Traefik**
- Container `twenty` e `worker` tinham labels Traefik idênticas
- Container não estava conectado à rede `coolify`

**Problema 2: Conflito DNS PostgreSQL**
- O hostname `postgres` resolvia para `coolify-db` (IP 10.0.1.4) na rede coolify
- Twenty tentava conectar no banco errado causando "password authentication failed"
- Twenty deveria conectar em `postgres-m8w8gso08k44wc0cs4oswosg` (IP 10.0.9.2)

**Solução Aplicada:**
1. Modificar docker-compose via Coolify UI:
   - Trocar `@postgres:5432` por `@postgres-m8w8gso08k44wc0cs4oswosg:5432`
   - Trocar `redis://redis:6379` por `redis://redis-m8w8gso08k44wc0cs4oswosg:6379`
2. Stop + Deploy (não apenas Restart) para recriar containers com nova config
3. Conectar container à rede coolify: `docker network connect coolify twenty-m8w8gso08k44wc0cs4oswosg`
4. Reiniciar Traefik: `docker restart coolify-proxy`

- **Endpoint Temp:** http://twenty-m8w8gso08k44wc0cs4oswosg.72.61.37.176.sslip.io (**FUNCIONANDO**)
- **Status:** 200 OK - UI carregando, admin criado, workspace configurado

**Admin Criado:**
- Email: `admin@trafegoparaconsultorios.com.br`
- Senha: `TPC@Admin2026!`
- Workspace: `Tráfego para Consultórios`

---

### 5. ~~Evolution API - Status "running:unknown"~~ VERIFICADO
- **Severidade:** ~~BAIXA~~ RESOLVIDO
- **Descrição:** Healthcheck não configurado, mas serviço funcionando
- **Endpoint:** https://evo.trafegoparaconsultorios.com.br
- **Status HTTP:** 200 OK (funcionando)
- **Instância WhatsApp:** `Tráfego para Consultórios` - **CONNECTED**
- **Número:** 556120176360
- **Integração Chatwoot:** Configurada e ativa

---

### 6. TPC-Brain PARADO (Conflito de Domínio)
- **Severidade:** RESOLVIDO
- **Descrição:** Estava interceptando api.trafegoparaconsultorios.com.br
- **Status:** exited:unhealthy
- **Ação:** Manter parado ou deletar (já foi substituído por medflow-forks)

---

### 7. MedFlow - Status "running:unhealthy"
- **Severidade:** BAIXA
- **Descrição:** Container reporta unhealthy mas endpoints respondem OK
- **API:** 200 OK
- **Web:** 200 OK
- **Ação:** Verificar configuração de healthcheck no docker-compose

---

## PROBLEMAS DE INTEGRAÇÃO

### 8. Webhooks NÃO Configurados
- **Severidade:** ALTA
- **Descrição:** Não há integração entre Twenty, Chatwoot e Cal.com (que nem existe)
- **Impacto:**
  - Contatos não sincronizam
  - Leads não são criados automaticamente
  - Agendamentos não atualizam pipeline
- **Ação:** Criar serviço de integração (FASE 3 do plano)

---

### 9. ~~Evolution API ↔ Chatwoot~~ RESOLVIDO
- **Severidade:** ~~VERIFICAR~~ RESOLVIDO
- **Descrição:** Integração configurada com sucesso via Evolution Manager
- **Configuração:**
  - Chatwoot URL: `http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io`
  - Account ID: `1`
  - Token: Configurado
  - Inbox criado: `WhatsApp TPC`
- **Status:** Inbox WhatsApp criado automaticamente no Chatwoot

---

## PROBLEMAS DE SEGURANÇA

### 10. db-main (PostgreSQL) Exposto Publicamente
- **Severidade:** ALTA
- **Descrição:** Banco de dados acessível externamente na porta 5432
- **Credenciais:** postgres:comandos95 (senha fraca)
- **URL:** postgres://postgres:comandos95@72.61.37.176:5432/postgres
- **Ação URGENTE:**
  - Desabilitar acesso público OU
  - Usar senha forte + firewall

---

### 11. Senhas em Texto no Compose
- **Severidade:** MÉDIA
- **Descrição:** Algumas senhas estão hardcoded nos docker-compose
- **Exemplo:** Twenty DB: `Comandos95A2025M2026`
- **Ação:** Migrar para secrets do Coolify

---

## RESUMO DE AÇÕES PRIORITÁRIAS

1. **URGENTE:** Proteger db-main (senha/firewall)
2. ~~**CRÍTICO:** Deploy Cal.com~~ **RESOLVIDO**
3. ~~**CRÍTICO:** Corrigir Twenty CRM (conflito rotas Traefik)~~ **RESOLVIDO**
4. ~~**ALTA:** Configurar Evolution API ↔ Chatwoot~~ **RESOLVIDO**
5. **ALTA:** Criar serviço de integração Twenty ↔ Chatwoot ↔ Cal.com (webhooks)
6. **MÉDIA:** Corrigir healthchecks
7. **MÉDIA:** Configurar creative-studio (GEMINI_API_KEY)
8. **BAIXA:** Decidir sobre centralização de bancos
9. **BAIXA:** Deletar TPC-Brain (obsoleto)

---

## DECISÃO NECESSÁRIA

### Estratégia de Banco de Dados

**Opção A: Manter Isolado (Atual)**
- Pros: Já funcionando, isolamento de falhas
- Cons: Mais recursos, mais backups

**Opção B: Centralizar**
- Pros: Economia de recursos, backup único
- Cons: Risco de migração, single point of failure

**Recomendação:** Manter isolado por agora, focar nas integrações via webhooks.
