---
active: true
iteration: 4
max_iterations: 75
completion_promise: "COMPLETE"
started_at: "2026-01-22T15:34:42Z"
---


# Integração Completa: Twenty + Chatwoot + Cal.com
## Tráfego para Consultórios - Stack Unificada

---

## CONTEXTO CRÍTICO
Sistema é INTEGRAÇÃO de 3 forks open-source que DEVEM conversar entre si:
- **Twenty CRM**: Fonte de verdade para contatos e pipeline
- **Chatwoot**: Central de atendimento (WhatsApp via Evolution API)
- **Cal.com**: Agendamento de consultas/reuniões

Integrações via webhooks diretos + APIs nativas - SEM intermediários.

Infraestrutura (Coolify):
- PostgreSQL central
- Redis central
- Evolution API para WhatsApp
- Domínio: trafegoparaconsultorios.com.br
- Coolify: https://coolify.trafegoparaconsultorios.com.br/

---

## FASE 1: AUDITORIA E LIMPEZA

- [ ] 1.1 Mapear TODOS os containers rodando no Coolify
- [ ] 1.2 Identificar serviços quebrados/mal configurados
- [ ] 1.3 Criar /docs/AUDIT.md com serviços, endpoints, env vars, conexões
- [ ] 1.4 Criar /docs/ISSUES.md com problemas encontrados
- [ ] 1.5 DECISÃO: Limpar e reconstruir OU consertar existente?
- [ ] **HARD STOP** - Aprovar plano antes de prosseguir

---

## FASE 2: SERVIÇOS ISOLADOS (Camada 0)
Cada sistema funcionando 100% SOZINHO antes de integrar.

### 2.1 PostgreSQL Central
- [ ] 2.1.1 Verificar/criar schemas: twenty_production, chatwoot_production, calcom_production
- [ ] 2.1.2 Usuários de banco com permissões corretas
- [ ] 2.1.3 Testar conexões

### 2.2 Twenty CRM
- [ ] 2.2.1 Deploy limpo no Coolify
- [ ] 2.2.2 Variáveis de ambiente configuradas
- [ ] 2.2.3 Migrations rodadas
- [ ] 2.2.4 UI acessível: crm.trafegoparaconsultorios.com.br
- [ ] 2.2.5 API funcionando
- [ ] 2.2.6 Superuser admin criado
- [ ] **TESTE**: CRUD de contato via UI e via API

### 2.3 Chatwoot
- [ ] 2.3.1 Deploy limpo no Coolify
- [ ] 2.3.2 Variáveis de ambiente configuradas
- [ ] 2.3.3 Migrations rodadas
- [ ] 2.3.4 UI acessível: chat.trafegoparaconsultorios.com.br
- [ ] 2.3.5 API funcionando
- [ ] 2.3.6 Superuser admin criado
- [ ] 2.3.7 Inbox WhatsApp conectado (Evolution API)
- [ ] **TESTE**: Enviar msg para WhatsApp, aparece no Chatwoot?

### 2.4 Cal.com
- [ ] 2.4.1 Deploy limpo no Coolify
- [ ] 2.4.2 Variáveis de ambiente configuradas
- [ ] 2.4.3 Migrations rodadas
- [ ] 2.4.4 UI acessível: agenda.trafegoparaconsultorios.com.br
- [ ] 2.4.5 API funcionando
- [ ] 2.4.6 Superuser admin criado
- [ ] 2.4.7 Evento padrão criado: Consulta Inicial 30min
- [ ] **TESTE**: Agendar via link público funciona?

- [ ] **HARD STOP** - 3 sistemas funcionando ISOLADAMENTE

---

## FASE 3: CAMADA DE INTEGRAÇÃO (Webhooks Diretos)

### 3.1 Microserviço de Integração
- [ ] 3.1.1 Criar /integrations/ com serviço leve (Node ou Python)
- [ ] 3.1.2 Endpoints: POST /webhooks/twenty, /webhooks/chatwoot, /webhooks/calcom
- [ ] 3.1.3 Deploy em: integrations.trafegoparaconsultorios.com.br
- [ ] 3.1.4 Health check funcionando

### 3.2 Twenty ↔ Chatwoot (Sync de Contatos)
- [ ] 3.2.1 Twenty webhook contact.created -> criar contato no Chatwoot
- [ ] 3.2.2 Twenty webhook contact.updated -> sync Chatwoot
- [ ] 3.2.3 Chatwoot webhook contact.created -> criar no Twenty
- [ ] 3.2.4 Deduplicação por email/telefone
- [ ] **TESTE**: Criar contato em cada sistema, aparece no outro?

### 3.3 Chatwoot -> Twenty (Conversas = Leads)
- [ ] 3.3.1 Chatwoot webhook conversation.created -> criar lead no Twenty (stage: New)
- [ ] 3.3.2 Chatwoot webhook conversation.status_changed -> atualizar stage no Twenty
- [ ] **TESTE**: Nova conversa WhatsApp, lead aparece no Twenty?

### 3.4 Cal.com -> Twenty + Chatwoot
- [ ] 3.4.1 Cal.com webhook BOOKING_CREATED -> Twenty (stage: Meeting Scheduled)
- [ ] 3.4.2 Cal.com webhook BOOKING_CREATED -> Chatwoot (msg confirmação)
- [ ] 3.4.3 Cal.com webhook BOOKING_CANCELLED -> reverter stage + notificar
- [ ] **TESTE**: Agendar, Twenty e Chatwoot refletem?

### 3.5 Link de Agendamento no Chat
- [ ] 3.5.1 Endpoint GET /booking-link/:contactId gera link Cal.com com prefill
- [ ] 3.5.2 Chatwoot pode chamar via macro
- [ ] **TESTE**: Pedir link no chat, recebe link funcional?

- [ ] **HARD STOP** - Diagrama de integrações em /docs/INTEGRATIONS.md

---

## FASE 4: FLUXO E2E DO LEAD

### 4.1 Documentar Fluxo
Criar /docs/LEAD_FLOW.md descrevendo:
1. Lead manda WhatsApp
2. Evolution API entrega ao Chatwoot (conversa criada)
3. Webhook dispara, Twenty recebe lead (stage: New)
4. Qualificação no Chatwoot (bot ou humano)
5. Se qualificado, Twenty atualiza (stage: Qualified)
6. Link Cal.com enviado no chat
7. Lead agenda no Cal.com
8. Webhook dispara, Twenty atualiza (stage: Meeting Scheduled)
9. Webhook dispara, Chatwoot recebe msg confirmação
10. Heloisa faz a call de vendas

### 4.2 Bot de Qualificação
- [ ] 4.2.1 Usar automações nativas do Chatwoot OU criar bot simples
- [ ] 4.2.2 Perguntas: Nome, Especialidade, Cidade, Faturamento, Objetivo
- [ ] 4.2.3 Se qualificado: atualiza Twenty + notifica Heloisa
- [ ] 4.2.4 Se nao qualificado: resposta educada + arquiva
- [ ] **TESTE**: Simular conversa completa

### 4.3 Handoff para Heloisa
- [ ] 4.3.1 Regras de escalonamento configuradas
- [ ] 4.3.2 Notificação quando lead qualificado aguarda
- [ ] 4.3.3 View de Leads Pendentes no Twenty
- [ ] **TESTE**: Lead qualificado, notificação chega?

- [ ] **HARD STOP** - Testar fluxo E2E 3x com sucesso

---

## FASE 5: USUÁRIOS

Criar em TODOS os 3 sistemas:
- [ ] cto@trafegoparaconsultorios.com.br (Admin)
- [ ] heloisa@trafegoparaconsultorios.com.br (Admin)
- [ ] briansouzanogueira@gmail.com (Operacional)

- [ ] **TESTE**: Todos logam nos 3 sistemas?

---

## FASE 6: QA EXAUSTIVO

### 6.1 Testes de Integração
- [ ] Criar contato Twenty -> sync Chatwoot
- [ ] Nova conversa WhatsApp -> lead no Twenty
- [ ] Agendar Cal.com -> stage Twenty + msg Chatwoot
- [ ] Cancelar agendamento -> reverter tudo
- [ ] Atualizar contato -> sync bidirecional

### 6.2 Testes de Falha
- [ ] Webhook falha, tem retry?
- [ ] Serviço offline, fila funciona?
- [ ] Dado duplicado, tratamento correto?

### 6.3 Testes de UI
- [ ] Navegar todas as telas do Twenty
- [ ] Todas as funções do Chatwoot
- [ ] Fluxo completo no Cal.com
- [ ] Testar em mobile

### 6.4 Documentar
- [ ] /docs/QA_RESULTS.md com todos os testes
- [ ] /docs/BUGS.md com bugs encontrados
- [ ] Corrigir bugs CRITICOS antes de finalizar

- [ ] **HARD STOP** - 100% dos testes passando

---

## FASE 7: DOCUMENTAÇÃO

- [ ] /docs/ARCHITECTURE.md - diagrama completo
- [ ] /docs/INTEGRATIONS.md - todos os webhooks
- [ ] /docs/ENDPOINTS.md - todas as URLs
- [ ] /docs/RUNBOOK.md - operação e troubleshooting
- [ ] README.md atualizado

---

## CRITÉRIOS DE SUCESSO

1. Twenty acessível e funcional
2. Chatwoot acessível + WhatsApp conectado
3. Cal.com acessível + evento configurado
4. Sync bidirecional Twenty e Chatwoot
5. Webhooks Cal.com para Twenty + Chatwoot
6. Fluxo E2E testado 3x com sucesso
7. 3 superusers logando nos 3 sistemas
8. Documentação completa em /docs/
9. Zero bugs críticos

---

## SE BLOQUEADO

Apos 10 iterações sem progresso:
1. Documentar bloqueio exato
2. Listar abordagens tentadas
3. Propor alternativas
4. Output: BLOCKED

Se precisa credencial/acesso: usar AskUserQuestion

---

Quando TODOS os critérios cumpridos: COMPLETE

