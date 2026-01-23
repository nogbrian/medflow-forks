# MedFlow Atender — Simular Atendimento

Simule um atendimento completo de paciente para testar o fluxo end-to-end.

## USO
```
/medflow-atender [cenário]
```

## CENÁRIOS

### novo-paciente
Simula um novo paciente entrando em contato pelo WhatsApp:
1. Mensagem de boas-vindas
2. Qualificação (o que procura)
3. Informações sobre consulta/preço
4. Verificar disponibilidade
5. Agendar consulta
6. Criar lead no CRM
7. Confirmar agendamento

### reagendamento
Simula paciente existente querendo remarcar:
1. Buscar paciente no CRM
2. Identificar agendamento atual
3. Verificar nova disponibilidade
4. Reagendar
5. Atualizar CRM

### reclamacao
Simula paciente insatisfeito (trigger de escalation):
1. Detectar insatisfação
2. Tentar resolver
3. Escalar para humano via Chatwoot
4. Registrar no CRM

### follow-up
Simula reengajamento de lead frio:
1. Identificar lead sem resposta há 7+ dias
2. Enviar mensagem de reengajamento
3. Se responder: qualificar
4. Se não: agendar próximo follow-up

## REGRAS

1. Use dados fictícios mas realistas (nomes brasileiros, telefones 55XX)
2. Simule respostas do paciente variadas
3. Verifique que cada tool é chamada corretamente
4. Registre o fluxo completo para debugging
5. Identifique gaps no fluxo atual

## OUTPUT

Produza um relatório com:
- Fluxo executado (step by step)
- Tools chamadas e resultados
- Decisões de routing do Coordinator
- Pontos de melhoria identificados
- Score de naturalidade da conversa (1-10)
