# Plano de Implementação: Integração Twenty + Chatwoot + Cal.com
## Tráfego para Consultórios
**Data:** 2026-01-22

---

## DECISÃO: CONSERTAR EXISTENTE + ADICIONAR CAL.COM

### Justificativa

A auditoria revelou que a infraestrutura existente está **funcionando**:

| Serviço | Status | Ação |
|---------|--------|------|
| Twenty CRM | OK (200) | Manter, configurar webhooks |
| Chatwoot | OK (200) | Manter, configurar webhooks |
| Evolution API | OK (200) | Manter, verificar integração WhatsApp |
| Cal.com | NÃO EXISTE | **DEPLOY NECESSÁRIO** |
| PostgreSQL/Redis | Isolados | Manter (não migrar) |

**NÃO vamos limpar e reconstruir** - isso causaria downtime desnecessário.

---

## PLANO DE EXECUÇÃO

### FASE 2: Verificar Serviços Isolados

#### 2.1 PostgreSQL Central
- [x] Já existe e está saudável
- [ ] Criar schemas: twenty_production, chatwoot_production, calcom_production
  - **DECISÃO:** NÃO FAZER - cada serviço já tem seu banco isolado
- [ ] Usuários de banco - **NÃO NECESSÁRIO** (bancos isolados)

#### 2.2 Twenty CRM
- [x] Deploy existente no Coolify
- [x] UI acessível: https://twenty.trafegoparaconsultorios.com.br
- [ ] Verificar se API está funcionando (`/api/open-api`)
- [ ] Verificar se superuser admin existe
- [ ] Testar CRUD de contato

#### 2.3 Chatwoot
- [x] Deploy existente no Coolify
- [x] UI acessível: https://chatwoot.trafegoparaconsultorios.com.br
- [ ] Verificar se API está funcionando
- [ ] Verificar se superuser admin existe
- [ ] Verificar se WhatsApp está conectado (Evolution API)

#### 2.4 Cal.com - **DEPLOY NECESSÁRIO**
- [ ] Deploy no Coolify usando template oficial
- [ ] Configurar variáveis de ambiente
- [ ] UI acessível: https://agenda.trafegoparaconsultorios.com.br
- [ ] Criar superuser admin
- [ ] Criar evento: "Consulta Inicial 30min"

---

### FASE 3: Camada de Integração

#### 3.1 Microserviço de Integração
O serviço `integration` do MedFlow (https://api.trafegoparaconsultorios.com.br) pode ser reutilizado ou podemos criar um novo específico.

**Endpoints necessários:**
```
POST /webhooks/twenty      - Recebe eventos do Twenty
POST /webhooks/chatwoot    - Recebe eventos do Chatwoot
POST /webhooks/calcom      - Recebe eventos do Cal.com
GET  /booking-link/:id     - Gera link de agendamento
```

#### 3.2 Twenty ↔ Chatwoot (Sync de Contatos)
- Twenty webhook `contact.created` → criar contato no Chatwoot
- Chatwoot webhook `contact.created` → criar no Twenty
- Deduplicação por email/telefone

#### 3.3 Chatwoot → Twenty (Conversas = Leads)
- Chatwoot webhook `conversation.created` → criar lead no Twenty (stage: New)
- Chatwoot webhook `conversation.status_changed` → atualizar stage

#### 3.4 Cal.com → Twenty + Chatwoot
- Cal.com webhook `BOOKING_CREATED` → Twenty (stage: Meeting Scheduled)
- Cal.com webhook `BOOKING_CREATED` → Chatwoot (msg confirmação)

---

### FASE 4-7: Conforme Plano Original

Após as fases 2-3 funcionando, seguir com:
- FASE 4: Fluxo E2E do Lead + Bot de Qualificação
- FASE 5: Criação de Usuários
- FASE 6: QA Exaustivo
- FASE 7: Documentação

---

## PRÓXIMA AÇÃO IMEDIATA

### Verificar Twenty CRM

1. Acessar https://twenty.trafegoparaconsultorios.com.br
2. Verificar se consegue fazer login
3. Verificar API: `GET /api/open-api`
4. Se não tiver usuário, criar via CLI ou seed

### Verificar Chatwoot

1. Acessar https://chatwoot.trafegoparaconsultorios.com.br
2. Verificar se consegue fazer login
3. Verificar se tem inbox WhatsApp configurado
4. Testar conexão com Evolution API

### Deploy Cal.com

1. Usar template Coolify para Cal.com
2. Configurar DATABASE_URL para banco interno
3. Configurar NEXTAUTH_SECRET e CALENDSO_ENCRYPTION_KEY
4. Acessar e criar admin

---

## APROVAÇÃO NECESSÁRIA

Antes de prosseguir com a FASE 2, preciso de aprovação para:

1. **Confirmar que podemos usar a infraestrutura existente** (Twenty, Chatwoot, Evolution já deployados)
2. **Confirmar o endpoint do Cal.com:** agenda.trafegoparaconsultorios.com.br
3. **Confirmar se devo criar o serviço de integração** como parte do MedFlow ou separado
4. **Credenciais necessárias:**
   - Login do Twenty CRM (já existe usuário?)
   - Login do Chatwoot (já existe usuário?)
   - API Key do Evolution API (para testar)

---

## RISCOS

| Risco | Mitigação |
|-------|-----------|
| Twenty não tem API habilitada | Ativar via config |
| Chatwoot não conectado ao WhatsApp | Reconfigurar Evolution |
| Cal.com conflitar com outros serviços | Usar domínio dedicado |
| Webhooks não funcionarem | Logs + retry + dead letter queue |

---

**Aguardando aprovação para prosseguir com FASE 2.**
