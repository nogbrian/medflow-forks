"""
Lead Qualifier Agent.

Automatically qualifies leads based on conversation history and contact data.
Assigns a score from 1-100 and updates the contact's temperature.
"""

from agno.agent import Agent

from agents.base import get_db, get_model
from core.logging import get_logger

logger = get_logger(__name__)

LEAD_QUALIFIER_PROMPT = """Você é um especialista em qualificação de leads para clínicas médicas.

Sua função é analisar conversas e dados de contatos para determinar:
1. Probabilidade de agendamento (0-100)
2. Temperatura do lead (hot, warm, cold)
3. Próxima melhor ação

## Critérios de Qualificação

### Score 80-100 (HOT)
- Perguntou sobre preços/valores
- Mencionou urgência ou datas específicas
- Pediu para agendar diretamente
- Demonstrou interesse em procedimento específico
- Respondeu perguntas de qualificação positivamente

### Score 50-79 (WARM)
- Fez perguntas sobre procedimentos
- Está comparando opções
- Mencionou recomendação de alguém
- Engajou em múltiplas mensagens
- Pediu mais informações

### Score 1-49 (COLD)
- Apenas tirou dúvidas genéricas
- Não respondeu perguntas de qualificação
- Demonstrou objeções não resolvidas
- Conversa curta sem engajamento
- Apenas curiosidade, sem intenção clara

## Fatores de Ajuste

### Positivos (+5 a +15 cada)
- É paciente existente: +10
- Veio por indicação: +15
- Tem plano de saúde compatível: +10
- Respondeu rápido (< 1 hora): +5
- Enviou exames/documentos: +15

### Negativos (-5 a -15 cada)
- Menciona preço como barreira: -10
- Está "só pesquisando": -15
- Não tem disponibilidade próxima: -10
- Objeções não resolvidas: -15
- Demora para responder (> 24h): -5

## Output Esperado

Retorne um JSON com:
```json
{
  "score": 75,
  "temperature": "warm",
  "reasoning": "Lead demonstrou interesse real em rinoplastia, perguntou sobre valores e tempo de recuperação. Porém mencionou que ainda está pesquisando outras clínicas.",
  "signals": {
    "positive": ["Interesse em procedimento específico", "Perguntou sobre valores"],
    "negative": ["Está comparando opções"]
  },
  "recommended_action": "Enviar casos de sucesso e depoimentos de pacientes",
  "follow_up_priority": "high",
  "suggested_stage": "engaged"
}
```

## Estágios do Pipeline
- new: Lead novo, ainda não qualificado
- engaged: Demonstrou interesse, em negociação
- qualified: Alta probabilidade de conversão
- scheduled: Consulta agendada
- converted: Procedimento realizado
- lost: Lead perdido
"""


def create_lead_qualifier() -> Agent:
    """Create lead qualifier agent."""
    return Agent(
        name="lead_qualifier",
        model=get_model("smart"),
        instructions=LEAD_QUALIFIER_PROMPT,
        db=get_db(),
        add_history_to_context=True,
        num_history_runs=5,
    )


async def qualify_lead(
    clinic_id: str,
    contact_id: str,
    conversation_history: list[dict],
    contact_data: dict,
) -> dict:
    """
    Qualify a lead based on conversation history and contact data.

    Args:
        clinic_id: Clinic UUID
        contact_id: Contact UUID
        conversation_history: List of messages from the conversation
        contact_data: Contact information (name, source, tags, etc.)

    Returns:
        Qualification result with score, temperature, and recommendations
    """
    agent = create_lead_qualifier()

    # Build context for qualification
    context = f"""
## Dados do Contato
- Nome: {contact_data.get('name', 'Não informado')}
- Telefone: {contact_data.get('phone', 'Não informado')}
- Origem: {contact_data.get('source', 'Não informado')}
- Tags: {', '.join(contact_data.get('tags', [])) or 'Nenhuma'}
- Primeiro contato: {contact_data.get('first_contact_at', 'Não informado')}
- Último contato: {contact_data.get('last_contact_at', 'Não informado')}

## Histórico da Conversa
"""
    for msg in conversation_history[-20:]:  # Last 20 messages
        role = "Paciente" if msg.get("direction") == "inbound" else "Clínica"
        content = msg.get("content", {}).get("text", str(msg.get("content", "")))
        context += f"\n**{role}**: {content}"

    context += "\n\n## Tarefa\nAnalise os dados acima e qualifique este lead."

    response = await agent.arun(message=context)

    # Parse response
    try:
        import json
        # Extract JSON from response
        content = str(response.content)
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        else:
            json_str = content

        result = json.loads(json_str.strip())
        result["contact_id"] = contact_id
        result["clinic_id"] = clinic_id
        return result
    except (json.JSONDecodeError, IndexError):
        logger.warning("Failed to parse lead qualifier response", contact_id=contact_id)
        return {
            "contact_id": contact_id,
            "clinic_id": clinic_id,
            "score": 50,
            "temperature": "warm",
            "reasoning": "Não foi possível analisar completamente o lead.",
            "recommended_action": "Revisão manual necessária",
            "error": "parse_error",
        }


# Singleton instance
lead_qualifier = create_lead_qualifier()
