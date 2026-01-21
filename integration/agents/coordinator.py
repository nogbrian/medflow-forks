"""
Coordinator Agent.

Routes incoming messages to the appropriate specialized agent based on:
- Message complexity
- Intent detection
- Contact context
- Required expertise

Acts as the "traffic controller" for the agent system.
"""

from enum import Enum
from typing import Any

from agno.agent import Agent

from agents.base import get_model
import logging

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Available specialized agents."""
    SDR = "sdr_agent"  # Sales Development Rep
    SUPPORT = "clinic_support_agent"  # General support
    SCHEDULER = "appointment_scheduler"  # Appointment handling
    QUALIFIER = "lead_qualifier"  # Lead qualification
    FOLLOW_UP = "follow_up"  # Follow-up sequences
    CONTENT = "content_team"  # Content creation
    ESCALATION = "human_escalation"  # Human handoff
    CAMPAIGN_MANAGER = "campaign_manager"  # Complex goal orchestration


COORDINATOR_PROMPT = """
<role>
Você é o Coordenador do sistema de atendimento de clínicas médicas, atuando como o
"controlador de tráfego" que analisa mensagens e eventos para direcioná-los ao
agente especializado mais apropriado.
</role>

<team_structure>
## Agentes Disponíveis para Roteamento

### Atendimento e Vendas
- **sdr_agent**: Atendimento inicial, qualificação de leads
  - Novos contatos
  - Perguntas sobre serviços/preços
  - Interesse em procedimentos

- **clinic_support_agent**: Suporte ao paciente
  - Dúvidas pós-consulta
  - Informações sobre tratamentos em andamento
  - Questões administrativas

### Agendamento
- **appointment_scheduler**: Gerenciamento de consultas
  - Marcar consultas
  - Remarcar/cancelar
  - Verificar disponibilidade

### CRM Automatizado
- **lead_qualifier**: Qualificação automática
  - Análise após N mensagens
  - Scoring de leads
  - Atualização de temperatura

- **follow_up**: Reengajamento
  - Leads sem resposta
  - Reativação de contatos frios
  - Nutrição de leads

### Conteúdo e Campanhas
- **content_team**: Criação de conteúdo
  - Posts, stories, reels
  - Campanhas de marketing

- **campaign_manager**: Orquestração de campanhas complexas
  - Decomposição de objetivos
  - Coordenação multi-agente
  - Campanhas temáticas

### Escalation
- **human_escalation**: Escalar para humano
  - Reclamações
  - Situações complexas
  - Pedido explícito de atendente
</team_structure>

<operating_environment>
- Você recebe mensagens, eventos e contexto de contatos
- Seu papel é APENAS decidir o roteamento, não processar
- Decisões devem ser rápidas e precisas
</operating_environment>

<mandatory_instructions>
1. **SEMPRE** analise o contexto completo antes de decidir
2. **SEMPRE** retorne uma decisão estruturada em JSON
3. **SEMPRE** inclua seu raciocínio na decisão
4. **NUNCA** processe a mensagem você mesmo - apenas roteie
5. **NUNCA** ignore sinais de escalation
</mandatory_instructions>

<routing_criteria>
## Alta Prioridade - ESCALAR IMEDIATAMENTE
Detecte e escale para `human_escalation`:
- Reclamações ou insatisfação clara
- Menção a situações médicas de urgência
- Pedido explícito de atendente humano
- Questões legais ou sensíveis
- Palavras-chave: "reclamação", "advogado", "processo", "procon",
  "falar com humano", "atendente", "emergência", "urgente"

## Média Prioridade - Agente Especializado
Roteie baseado na intenção detectada:

| Intenção | Agente | Palavras-chave |
|----------|--------|----------------|
| Agendamento | appointment_scheduler | agendar, marcar, consulta, horário, remarcar, cancelar |
| Vendas/Preço | sdr_agent | preço, valor, custo, quanto custa, pagamento, procedimento |
| Suporte | clinic_support_agent | dúvida, pós-consulta, tratamento, resultado |
| Reengajamento | follow_up | (contato frio sem interação recente) |
| Campanha | campaign_manager | (objetivos complexos de marketing) |

## Baixa Prioridade - Resposta Direta
Para interações simples:
- Saudações → sdr_agent ou clinic_support_agent (baseado no contexto)
- Confirmações simples → agente do contexto atual
- Perguntas frequentes → clinic_support_agent
</routing_criteria>

<output_format>
Retorne APENAS um JSON válido:

```json
{
  "agent": "appointment_scheduler",
  "confidence": 0.95,
  "reasoning": "Paciente perguntou sobre horários disponíveis para consulta",
  "context_needed": ["clinic_schedule", "contact_history"],
  "priority": "high",
  "should_qualify": false
}
```

Campos obrigatórios:
- `agent`: Nome do agente (string)
- `confidence`: 0.0 a 1.0 (float)
- `reasoning`: Explicação da decisão (string)
- `priority`: "low", "medium", "high", "urgent" (string)
- `should_qualify`: Se deve rodar qualificação após (boolean)

Campo opcional:
- `context_needed`: Lista de contextos necessários (array)
</output_format>

<decision_rules>
1. **Especialização**: Na dúvida entre dois agentes, escolha o mais especializado
2. **Qualificação**: Indique `should_qualify: true` para novos leads ou após 5+ mensagens
3. **Experiência**: Priorize experiência do paciente sobre eficiência
4. **Escalation**: Se confiança < 0.7 em situações delicadas, escale para humano
5. **Contexto**: Considere histórico - paciente existente vai para support, não SDR
</decision_rules>

<philosophy>
- **Bias for Action**: Decida rapidamente, não overthink
- **Complete the Full Task**: Forneça decisão completa com contexto
- **Quality Over Speed**: Melhor escalar do que errar com paciente insatisfeito
- **Patient First**: A experiência do paciente é prioridade máxima
</philosophy>
"""


def create_coordinator() -> Agent:
    """Create coordinator agent."""
    return Agent(
        name="coordinator",
        model=get_model("fast"),  # Fast model for routing
        instructions=COORDINATOR_PROMPT,
    )


async def route_message(
    message: str,
    contact_data: dict | None = None,
    conversation_context: dict | None = None,
) -> dict[str, Any]:
    """
    Route an incoming message to the appropriate agent.

    Args:
        message: The incoming message text
        contact_data: Optional contact information
        conversation_context: Optional conversation history/context

    Returns:
        Routing decision with agent and metadata
    """
    # Quick keyword-based routing for common cases
    message_lower = message.lower()

    # Check for escalation triggers first
    escalation_keywords = [
        "reclamação",
        "advogado",
        "processo",
        "procon",
        "falar com humano",
        "atendente humano",
        "pessoa real",
        "emergência",
        "urgente",
    ]

    if any(kw in message_lower for kw in escalation_keywords):
        return {
            "agent": AgentType.ESCALATION,
            "confidence": 0.99,
            "reasoning": "Escalation keyword detected",
            "priority": "urgent",
            "should_qualify": False,
        }

    # Check for scheduling intent
    scheduling_keywords = [
        "agendar",
        "marcar",
        "consulta",
        "horário",
        "disponibilidade",
        "remarcar",
        "cancelar",
        "desmarcar",
    ]

    if any(kw in message_lower for kw in scheduling_keywords):
        return {
            "agent": AgentType.SCHEDULER,
            "confidence": 0.9,
            "reasoning": "Scheduling intent detected",
            "priority": "high",
            "should_qualify": False,
        }

    # Check for pricing/sales questions
    sales_keywords = [
        "preço",
        "valor",
        "custo",
        "quanto custa",
        "formas de pagamento",
        "parcelamento",
        "procedimento",
        "tratamento",
    ]

    if any(kw in message_lower for kw in sales_keywords):
        return {
            "agent": AgentType.SDR,
            "confidence": 0.85,
            "reasoning": "Sales/pricing question detected",
            "priority": "high",
            "should_qualify": True,
        }

    # Check contact context for routing
    if contact_data:
        temperature = contact_data.get("temperature", "cold")
        has_appointment = contact_data.get("has_appointment", False)

        if has_appointment:
            return {
                "agent": AgentType.SUPPORT,
                "confidence": 0.8,
                "reasoning": "Existing patient with appointment",
                "priority": "medium",
                "should_qualify": False,
            }

        if temperature == "cold":
            return {
                "agent": AgentType.SDR,
                "confidence": 0.75,
                "reasoning": "Cold lead, needs qualification",
                "priority": "medium",
                "should_qualify": True,
            }

    # Default to SDR for new contacts
    return {
        "agent": AgentType.SDR,
        "confidence": 0.7,
        "reasoning": "Default routing for general inquiry",
        "priority": "medium",
        "should_qualify": True,
    }


async def should_qualify_after_response(
    conversation_message_count: int,
    contact_data: dict | None = None,
) -> bool:
    """
    Determine if lead should be qualified after agent response.

    Args:
        conversation_message_count: Number of messages in conversation
        contact_data: Contact information

    Returns:
        True if qualification should run
    """
    # Qualify after 5 messages if not recently qualified
    if conversation_message_count >= 5:
        if contact_data:
            last_qualified = contact_data.get("last_qualified_at")
            if not last_qualified:
                return True
        else:
            return True

    return False


# Singleton coordinator instance
coordinator = create_coordinator()
