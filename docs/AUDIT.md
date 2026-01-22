# Auditoria de Infraestrutura Coolify
## Tráfego para Consultórios - Stack Unificada
**Data:** 2026-01-22
**Atualizado:** 2026-01-22 18:30 (Todos serviços verificados + Integrações configuradas)

---

## 1. RESUMO EXECUTIVO

### Infraestrutura Base
- **Coolify URL:** https://coolify.trafegoparaconsultorios.com.br/
- **Servidor:** localhost (Coolify host)
- **IP Público:** 72.61.37.176
- **Proxy:** Traefik 3.6.7 (running)
- **Domínio Principal:** trafegoparaconsultorios.com.br

### Status Geral
| Serviço | Status | HTTP |
|---------|--------|------|
| Twenty | running:healthy | **200 OK** |
| Chatwoot | running:healthy | 302 OK |
| Cal.com | running:healthy | 307 OK |
| Evolution API | running:unknown | 200 OK |

---

## 2. SERVIÇOS DO PROJETO TPC-Stack

### 2.1 Twenty CRM - OK (RESOLVIDO)
| Campo | Valor |
|-------|-------|
| UUID | `m8w8gso08k44wc0cs4oswosg` |
| Status | `running:healthy` |
| Endpoint Temp | http://twenty-m8w8gso08k44wc0cs4oswosg.72.61.37.176.sslip.io |
| Endpoint Final | https://crm.trafegoparaconsultorios.com.br |
| HTTP Test | **200 OK** |

**Problema Resolvido:**
O Twenty estava com dois problemas:
1. Labels Traefik duplicadas entre containers `twenty` e `worker` (resolvido removendo labels do worker)
2. Container não conectado à rede `coolify` (resolvido com `docker network connect coolify twenty-m8w8gso08k44wc0cs4oswosg`)

**Componentes:**
- `twenty` - running:healthy
- `worker` - running
- `postgres` - running:healthy
- `redis` - running:healthy

---

### 2.2 Chatwoot - OK
| Campo | Valor |
|-------|-------|
| UUID | `d8gc84okgccw84g444wgswko` |
| Status | `running:healthy` |
| Endpoint Temp | http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io |
| Endpoint Final | https://chat.trafegoparaconsultorios.com.br |
| HTTP Test | **302 (OK)** |

**Componentes:**
- `chatwoot` - Aplicação Rails
- `sidekiq` - Background jobs
- `postgres` - PostgreSQL (pgvector)
- `redis` - Redis

---

### 2.3 Cal.com - OK
| Campo | Valor |
|-------|-------|
| UUID | `bk0k00wkoog8ck48c4k8k4gc` |
| Status | `running:healthy` |
| Endpoint Temp | http://calcom-bk0k00wkoog8ck48c4k8k4gc.72.61.37.176.sslip.io |
| Endpoint Final | https://agenda.trafegoparaconsultorios.com.br |
| HTTP Test | **307 (OK)** |

---

## 3. SERVIÇOS MANTIDOS

### 3.1 Evolution API (WhatsApp)
| Campo | Valor |
|-------|-------|
| UUID | `jscos8sgwws0sgcckso4swwc` |
| Status | `running:unknown` |
| Endpoint | https://evo.trafegoparaconsultorios.com.br |
| HTTP Test | **200 OK** |

---

### 3.2 CloudBeaver (DB Admin)
| Campo | Valor |
|-------|-------|
| UUID | `m0wwwogck08gccwo8040g0s8` |
| Status | `running:healthy` |

---

## 4. OUTROS PROJETOS (Não alterados)

### MedFlow
- API: https://api.trafegoparaconsultorios.com.br (OK)
- Web: https://medflow.trafegoparaconsultorios.com.br (OK)

---

## 5. MAPA DE ENDPOINTS ATUAIS

| Serviço | URL Temporária | URL Final Planejada | Status |
|---------|----------------|---------------------|--------|
| Twenty | http://twenty-m8w8gso08k44wc0cs4oswosg.72.61.37.176.sslip.io | crm.trafegoparaconsultorios.com.br | **200 OK** |
| Chatwoot | http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io | chat.trafegoparaconsultorios.com.br | 302 OK |
| Cal.com | http://calcom-bk0k00wkoog8ck48c4k8k4gc.72.61.37.176.sslip.io | agenda.trafegoparaconsultorios.com.br | 307 OK |
| Evolution | https://evo.trafegoparaconsultorios.com.br | - | 200 OK |

---

## 6. PRÓXIMAS AÇÕES

1. ~~**BLOQUEADO - Twenty:**~~ **RESOLVIDO**
2. ~~**Usuário Twenty:**~~ **RESOLVIDO** - Admin criado: admin@trafegoparaconsultorios.com.br
3. **Domínios:** Configurar domínios finais via Coolify UI
4. **Usuários:** Criar usuários admin em Chatwoot e Cal.com
5. **Integrações:** Configurar webhooks entre sistemas

---

## 7. LOGS DE TENTATIVAS (Twenty) - RESOLVIDO

| Tentativa | Ação | Resultado |
|-----------|------|-----------|
| 1 | Criar Twenty template | Container exited |
| 2 | Deletar e recriar | Container exited |
| 3 | connect_to_docker_network: true | 504 Timeout |
| 4 | connect_to_docker_network: false | 504 Timeout |
| 5 | Stop/Start | 504 Timeout |
| 6 | Restart | 504 Timeout |
| 7 | Remover labels Traefik do worker | Container OK, 504 persiste |
| 8 | `docker network connect coolify twenty-xxx` | **200 OK - RESOLVIDO** |

**Solução Final:**
1. Remover Domain do container `worker` via Coolify UI (remove labels Traefik duplicadas)
2. Corrigir hostnames no docker-compose via Coolify UI:
   - `@postgres:5432` → `@postgres-m8w8gso08k44wc0cs4oswosg:5432`
   - `redis://redis:6379` → `redis://redis-m8w8gso08k44wc0cs4oswosg:6379`
3. Stop + Deploy (não apenas Restart) para recriar containers
4. Conectar container `twenty` à rede `coolify`: `docker network connect coolify twenty-m8w8gso08k44wc0cs4oswosg`
5. Reiniciar Traefik: `docker restart coolify-proxy`

---

## 8. CREDENCIAIS DO TWENTY CRM

| Campo | Valor |
|-------|-------|
| URL | http://twenty-m8w8gso08k44wc0cs4oswosg.72.61.37.176.sslip.io |
| Email Admin | `admin@trafegoparaconsultorios.com.br` |
| Senha | `TPC@Admin2026!` |
| Workspace | `Tráfego para Consultórios` |
| Nome Admin | `Admin TPC` |

**Banco de Dados:**
| Campo | Valor |
|-------|-------|
| Host | `postgres-m8w8gso08k44wc0cs4oswosg` |
| Port | `5432` |
| Database | `twenty-db` |
| User | `V43ESEMlrNztYL18` |
| Password | `YfOrEH7omApFqKSxvYs8a7Tk1M3aLniD` |

---

## 9. CREDENCIAIS DO CHATWOOT

| Campo | Valor |
|-------|-------|
| URL | http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io |
| Account ID | `1` |
| Account Name | `Trafego para Consultorios` |
| Admin Email | `briansouzanogueira@gmail.com` |
| Admin Name | `Brian Souza Nogueira` |
| API Token | `THnVEkiFXps1PefAxgRWDyKg` |
| Versão | v4.10.1 |

**Inbox WhatsApp:**
| Campo | Valor |
|-------|-------|
| Nome | `WhatsApp TPC` |
| Tipo | API Channel (Evolution API) |
| Status | Conectado |

---

## 10. CREDENCIAIS DO CAL.COM

| Campo | Valor |
|-------|-------|
| URL | http://calcom-bk0k00wkoog8ck48c4k8k4gc.72.61.37.176.sslip.io |
| Admin Email | `briansouzanogueira@gmail.com` |
| Admin Name | `Brian Souza Nogueira` |
| Username | `brian` |
| Versão | v.6.1.3-sh |

**Event Types Configurados:**
| Evento | Duração | Slug | Status |
|--------|---------|------|--------|
| Reunião de 15 min | 15m | `/brian/15min` | Ativo |
| Reunião de 30 min | 30m | `/brian/30min` | Ativo |
| Reunião secreta | 15m | `/brian/secret` | Oculto |

---

## 11. CREDENCIAIS DO EVOLUTION API

| Campo | Valor |
|-------|-------|
| URL | https://evo.trafegoparaconsultorios.com.br |
| Manager URL | https://evo.trafegoparaconsultorios.com.br/manager |
| API Key Global | `Comandos95A2025M2026` |
| Versão | 2.3.7 |

**Instância WhatsApp:**
| Campo | Valor |
|-------|-------|
| Nome | `Tráfego para Consultórios` |
| ID | `6d689f36-fef2-41a5-a6f4-ae12271f9a94` |
| Número | `556120176360` |
| Status | Connected |
| Contatos | 10 |
| Chats | 2 |

**Integração Chatwoot:**
| Campo | Valor |
|-------|-------|
| Enabled | true |
| Chatwoot URL | http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io |
| Account ID | 1 |
| Inbox Name | WhatsApp TPC |
| Auto Create | true |

---

## 12. WEBHOOKS CONFIGURADOS

### Twenty CRM Webhook
| Campo | Valor |
|-------|-------|
| URL | `https://api.trafegoparaconsultorios.com.br/sync/webhooks/twenty` |
| Descrição | Sync contacts to Chatwoot and Cal.com |
| Eventos | Todos os Objetos / Todos |
| Segredo | `tpc-webhook-secret-2026` |
| ID | `7cf2adbd-3f41-449e-b0cf-fc2e8e65b242` |

### Cal.com Webhook
| Campo | Valor |
|-------|-------|
| URL | `https://api.trafegoparaconsultorios.com.br/sync/webhooks/calcom` |
| Eventos | Booking created, Booking canceled, Booking rescheduled, Meeting ended, etc. |
| Segredo | `tpc-webhook-secret-2026` |
| Status | Ativo |

### Chatwoot Webhook
| Campo | Valor |
|-------|-------|
| URL | `https://api.trafegoparaconsultorios.com.br/sync/webhooks/chatwoot` |
| Nome | TPC Integration Sync |
| Eventos | conversation_created, message_created, contact_created, conversation_status_changed |
| Status | Ativo |

---

## 13. RESUMO DAS INTEGRAÇÕES

### Evolution API ↔ Chatwoot
- **Status:** ✅ Configurado
- **Inbox criado:** WhatsApp TPC
- **Fluxo:** WhatsApp → Evolution API → Chatwoot

### Twenty ↔ Chatwoot ↔ Cal.com (Webhooks)
- **Status:** ✅ Webhooks Configurados
- **Nota:** Endpoints webhook no MedFlow API (`/sync/webhooks/*`) precisam estar acessíveis
- **Secret Compartilhado:** `tpc-webhook-secret-2026`

**Fluxos Configurados:**
- [x] Twenty → MedFlow API → Chatwoot (sync contatos)
- [x] Chatwoot → MedFlow API → Twenty (leads de conversas)
- [x] Cal.com → MedFlow API → Twenty (agendamentos = stage update)
- [x] Cal.com → MedFlow API → Chatwoot (notificação de booking)
