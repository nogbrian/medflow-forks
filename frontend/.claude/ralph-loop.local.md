---
active: true
iteration: 2
max_iterations: 75
completion_promise: "COMPLETE"
started_at: "2026-01-23T02:31:46Z"
---


# Integração Creative Studio + Navegação Unificada
## Tráfego para Consultórios - UI Unificada

---

## CONTEXTO

### Sistemas já funcionando (do deploy anterior):
- Twenty CRM: crm.trafegoparaconsultorios.com.br
- Chatwoot: chat.trafegoparaconsultorios.com.br
- Cal.com: agenda.trafegoparaconsultorios.com.br

### Novo módulo a integrar:
- Creative Studio: /Users/brian/Documents/_backups-agencia-20260118/tpc-brain/creative-studio
- Funcionalidade: Geração de criativos/imagens para marketing médico
- Status: Já funciona bem isoladamente, só precisa integrar

### Objetivo:
1. Deploy do Creative Studio atrás do middleware de auth
2. Menu lateral UNIFICADO em todos os 4 sistemas
3. Navegação fluida entre módulos
4. Estilização consistente

---

## FASE 1: ANÁLISE DO CREATIVE STUDIO

- [ ] 1.1 Examinar estrutura do projeto em /Users/brian/Documents/_backups-agencia-20260118/tpc-brain/creative-studio
- [ ] 1.2 Identificar:
      - Framework usado (React, Next, Vue, etc)
      - Sistema de auth atual (se houver)
      - Dependências principais
      - Variáveis de ambiente necessárias
- [ ] 1.3 Documentar em /docs/CREATIVE_STUDIO_ANALYSIS.md
- [ ] 1.4 Identificar pontos de integração com outros módulos
- [ ] **HARD STOP** - Apresentar análise antes de prosseguir

---

## FASE 2: DEPLOY DO CREATIVE STUDIO

- [ ] 2.1 Criar configuração para Coolify
- [ ] 2.2 Configurar variáveis de ambiente
- [ ] 2.3 Deploy em: studio.trafegoparaconsultorios.com.br
- [ ] 2.4 Verificar funcionamento isolado
- [ ] 2.5 Testar todas as funcionalidades principais de geração
- [ ] **TESTE**: Gerar imagem de teste, funciona?

---

## FASE 3: MIDDLEWARE DE AUTENTICAÇÃO

### 3.1 Estratégia de Auth Unificada
- [ ] 3.1.1 Analisar auth existente em cada sistema:
      - Twenty: como autentica?
      - Chatwoot: como autentica?
      - Cal.com: como autentica?
- [ ] 3.1.2 Decidir estratégia:
      OPCAO A: Proxy reverso com auth central (recomendado)
      OPCAO B: SSO compartilhado entre sistemas
      OPCAO C: Token JWT compartilhado via cookie de domínio
- [ ] 3.1.3 Documentar decisão em /docs/AUTH_STRATEGY.md

### 3.2 Implementar Auth Gateway
- [ ] 3.2.1 Criar serviço de auth central se necessário
- [ ] 3.2.2 Configurar middleware que protege todos os subdomínios
- [ ] 3.2.3 Creative Studio só acessível após login
- [ ] 3.2.4 Sessão compartilhada entre módulos (cookie .trafegoparaconsultorios.com.br)
- [ ] **TESTE**: Logout em um sistema desloga de todos?

### 3.3 Proteger Creative Studio
- [ ] 3.3.1 Integrar Creative Studio com auth gateway
- [ ] 3.3.2 Redirecionar para login se não autenticado
- [ ] 3.3.3 Passar dados do usuário logado para o studio
- [ ] **TESTE**: Acessar studio sem login, redireciona para auth?

- [ ] **HARD STOP** - Auth funcionando em todos os módulos

---

## FASE 4: NAVEGAÇÃO UNIFICADA (MENU LATERAL)

### 4.1 Design do Menu
- [ ] 4.1.1 Criar componente de menu lateral compartilhado
- [ ] 4.1.2 Itens do menu:
      - Logo TPC no topo
      - CRM (Twenty) - ícone de pessoas/contatos
      - Atendimento (Chatwoot) - ícone de chat/mensagens
      - Agenda (Cal.com) - ícone de calendário
      - Creative Studio - ícone de paleta/imagem
      - Separador
      - Configurações
      - Perfil do usuário
      - Logout
- [ ] 4.1.3 Indicador visual de módulo ativo
- [ ] 4.1.4 Menu colapsável (ícones only vs expandido)

### 4.2 Implementação - Estratégia
Escolher UMA das abordagens:

OPCAO A - Shell Container (RECOMENDADO):
- [ ] 4.2.A1 Criar app shell em app.trafegoparaconsultorios.com.br
- [ ] 4.2.A2 Menu lateral fixo no shell
- [ ] 4.2.A3 Iframe ou micro-frontend para cada módulo
- [ ] 4.2.A4 Comunicação entre shell e módulos via postMessage

OPCAO B - Inject em cada sistema:
- [ ] 4.2.B1 Criar pacote/componente standalone do menu
- [ ] 4.2.B2 Injetar via script em cada sistema
- [ ] 4.2.B3 Posicionar com CSS fixo

OPCAO C - Proxy com inject:
- [ ] 4.2.C1 Nginx/Caddy como proxy reverso
- [ ] 4.2.C2 Injetar HTML do menu em todas as respostas
- [ ] 4.2.C3 Menos invasivo nos sistemas originais

- [ ] 4.2.X Documentar abordagem escolhida em /docs/NAVIGATION_ARCHITECTURE.md

### 4.3 Implementar Menu
- [ ] 4.3.1 Desenvolver componente de menu
- [ ] 4.3.2 Estilizar conforme design system (ver Fase 5)
- [ ] 4.3.3 Implementar navegação entre módulos
- [ ] 4.3.4 Manter estado do usuário ao navegar
- [ ] 4.3.5 Deep linking funciona (ex: app.../crm/contacts/123)
- [ ] **TESTE**: Navegar por todos os 4 módulos sem perder sessão

### 4.4 Integrar Menu em Cada Sistema
- [ ] 4.4.1 Twenty com menu lateral funcionando
- [ ] 4.4.2 Chatwoot com menu lateral funcionando
- [ ] 4.4.3 Cal.com com menu lateral funcionando
- [ ] 4.4.4 Creative Studio com menu lateral funcionando
- [ ] **TESTE**: Em cada sistema, clicar em outro módulo navega corretamente?

- [ ] **HARD STOP** - Navegação unificada funcionando nos 4 sistemas

---

## FASE 5: ESTILIZAÇÃO CONSISTENTE

### 5.1 Design System Base
- [ ] 5.1.1 Definir paleta de cores TPC:
      - Primária: cor principal da marca
      - Secundária: cor de destaque
      - Neutras: backgrounds, textos, bordas
      - Feedback: sucesso, erro, warning, info
- [ ] 5.1.2 Tipografia:
      - Font family principal
      - Escalas de tamanho
      - Pesos
- [ ] 5.1.3 Espacamentos padronizados
- [ ] 5.1.4 Border radius padronizado
- [ ] 5.1.5 Sombras padronizadas
- [ ] 5.1.6 Documentar em /docs/DESIGN_SYSTEM.md

### 5.2 Componentes Comuns
- [ ] 5.2.1 Menu lateral (já feito na Fase 4)
- [ ] 5.2.2 Header/topbar se aplicável
- [ ] 5.2.3 Botões primários e secundários
- [ ] 5.2.4 Cards
- [ ] 5.2.5 Modais
- [ ] 5.2.6 Inputs e forms
- [ ] 5.2.7 Tabelas
- [ ] 5.2.8 Loading states
- [ ] 5.2.9 Empty states
- [ ] 5.2.10 Criar biblioteca de componentes ou CSS compartilhado

### 5.3 Aplicar Estilo em Cada Módulo
- [ ] 5.3.1 Twenty: customizar tema/CSS para match TPC
      - Cores do sidebar
      - Botões
      - Headers
- [ ] 5.3.2 Chatwoot: customizar tema para match TPC
      - Cores do chat
      - Botões de ação
      - Badges e status
- [ ] 5.3.3 Cal.com: customizar tema para match TPC
      - Página de booking
      - Calendário
      - Confirmações
- [ ] 5.3.4 Creative Studio: ajustar para match TPC
      - Consistência com outros módulos
      - Paleta de cores
      - Componentes de UI

### 5.4 Consistência Visual
- [ ] 5.4.1 Todos os módulos parecem parte do mesmo produto
- [ ] 5.4.2 Transição entre módulos é suave visualmente
- [ ] 5.4.3 Nenhum módulo destoa dos demais
- [ ] **TESTE**: Screenshot de cada módulo, parecem da mesma família?

- [ ] **HARD STOP** - Estilização aprovada visualmente

---

## FASE 6: INTEGRAÇÕES DO CREATIVE STUDIO

### 6.1 Creative Studio com Twenty
- [ ] 6.1.1 Listar contatos/clientes do Twenty no Studio
- [ ] 6.1.2 Associar criativos gerados a contatos específicos
- [ ] 6.1.3 Histórico de criativos por cliente no Twenty
- [ ] **TESTE**: Gerar criativo para cliente X, aparece no histórico do Twenty?

### 6.2 Creative Studio com Chatwoot
- [ ] 6.2.1 Enviar criativo gerado diretamente no chat
- [ ] 6.2.2 Botão no Chatwoot para abrir Studio com contexto do lead
- [ ] 6.2.3 Preview do criativo antes de enviar
- [ ] **TESTE**: No chat, enviar criativo, lead recebe no WhatsApp?

### 6.3 Creative Studio com Cal.com
- [ ] 6.3.1 Gerar material de confirmação de reunião customizado
- [ ] 6.3.2 Criativos para follow-up pós-reunião
- [ ] **TESTE**: Agendar reunião, material de confirmação é gerado?

- [ ] **HARD STOP** - Creative Studio integrado com os 3 sistemas

---

## FASE 7: QA COMPLETO

### 7.1 Testes de Navegação
- [ ] Twenty -> Chatwoot -> Cal.com -> Studio -> Twenty (ciclo completo)
- [ ] Deep links funcionam de qualquer origem
- [ ] Back button do browser funciona corretamente
- [ ] Refresh mantém no módulo correto

### 7.2 Testes de Auth
- [ ] Login uma vez, acesso a todos os módulos
- [ ] Logout desloga de todos
- [ ] Sessão expira, redireciona para login
- [ ] Usuário sem permissão não acessa Studio

### 7.3 Testes de Estilo
- [ ] Consistência visual em todos os módulos
- [ ] Responsivo em desktop (1920, 1440, 1280)
- [ ] Responsivo em tablet
- [ ] Menu lateral funciona em todas as resoluções

### 7.4 Testes de Integração do Studio
- [ ] Gerar criativo, salvar, associar a cliente
- [ ] Enviar criativo via Chatwoot
- [ ] Acessar Studio com contexto de lead
- [ ] Histórico de criativos por cliente

### 7.5 Documentar
- [ ] /docs/QA_UNIFIED_UI.md com resultados
- [ ] /docs/BUGS_UI.md com bugs encontrados
- [ ] Corrigir bugs críticos

- [ ] **HARD STOP** - 100% dos testes passando

---

## FASE 8: DOCUMENTAÇÃO FINAL

- [ ] /docs/UNIFIED_ARCHITECTURE.md - arquitetura completa com 4 módulos
- [ ] /docs/NAVIGATION.md - como a navegação funciona
- [ ] /docs/DESIGN_SYSTEM.md - cores, fontes, componentes
- [ ] /docs/CREATIVE_STUDIO_INTEGRATION.md - APIs e integrações do studio
- [ ] Atualizar /docs/ENDPOINTS.md com novos endpoints
- [ ] Atualizar README.md

---

## CRITÉRIOS DE SUCESSO

1. Creative Studio deployado em studio.trafegoparaconsultorios.com.br
2. Todos os 4 módulos atrás do middleware de auth
3. Menu lateral unificado presente em todos os 4 sistemas
4. Navegação fluida entre módulos sem perder sessão
5. Estilização consistente - parecem o mesmo produto
6. Creative Studio integrado com Twenty, Chatwoot e Cal.com
7. Todos os usuários (cto@, heloisa@, brian@) acessam todos os módulos
8. Documentação completa

---

## SE BLOQUEADO

Após 10 iterações sem progresso:
1. Documentar bloqueio exato
2. Listar abordagens tentadas
3. Propor alternativas
4. Output: BLOCKED

Se precisa decisão de design/UX: usar AskUserQuestion
Se precisa credencial: usar AskUserQuestion

---

Quando TODOS os critérios cumpridos: COMPLETE

