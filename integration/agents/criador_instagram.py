"""Criador Instagram - Creates Instagram content."""

from pathlib import Path

from agno.agent import Agent
from agno.tools import tool

from tools import criar_aprovacao, gerar_imagem, gerar_variantes

from .base import get_db, get_model
from .tools.note_taking import append_note, list_notes, read_note, write_note

# Load directive
directive_path = Path(__file__).parent.parent / "config" / "directives" / "criador_instagram.md"
directive = directive_path.read_text() if directive_path.exists() else ""


# Define tool wrappers
@tool
def gerar_imagem_post(
    descricao: str,
    estilo: str = "medical",
    formato: str = "1024x1024",
) -> dict | None:
    """
    Gera uma imagem para um post do Instagram.

    Args:
        descricao: Descrição da imagem desejada
        estilo: Preset de estilo (medical, realistic, minimal, artistic)
        formato: Dimensões da imagem

    Returns:
        URL da imagem gerada e metadados
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        gerar_imagem(descricao, estilo, formato)
    )


@tool
def gerar_variantes_imagem(
    url_imagem: str,
    quantidade: int = 3,
) -> list:
    """
    Gera variações de uma imagem existente.

    Args:
        url_imagem: URL da imagem base
        quantidade: Número de variantes (máximo 4)

    Returns:
        Lista de URLs das imagens variantes
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        gerar_variantes(url_imagem, quantidade)
    )


@tool
def submeter_para_aprovacao(
    cliente_id: str,
    tipo: str,
    conteudo: dict,
    agendado_para: str | None = None,
) -> dict | None:
    """
    Submete conteúdo para aprovação humana.

    Args:
        cliente_id: UUID do cliente
        tipo: Tipo de conteúdo (post_instagram, story, etc.)
        conteudo: Dados do conteúdo (legenda, url_imagem, hashtags, etc.)
        agendado_para: Data/hora de publicação opcional (formato ISO)

    Returns:
        Registro de aprovação criado
    """
    import asyncio
    from datetime import datetime

    dados = {
        "cliente_id": cliente_id,
        "tipo": tipo,
        "conteudo": conteudo,
        "criado_por_agent": "criador_instagram",
    }

    if agendado_para:
        dados["agendado_para"] = datetime.fromisoformat(agendado_para)

    return asyncio.get_event_loop().run_until_complete(criar_aprovacao(dados))


CRIADOR_INSTAGRAM_PROMPT = f"""
<role>
Você é o Criador de Conteúdo Instagram, especialista em criar posts educativos, engajantes
e que respeitam as normas do CFM para médicos e profissionais de saúde.
</role>

<team_structure>
Você faz parte do Time de Conteúdo com os seguintes colegas:
- **Pesquisador**: Fornece insights sobre tendências e referências virais
- **Designer**: Desenvolve os conceitos visuais baseados nos seus briefs
- **Revisor**: Valida a conformidade com CFM e qualidade do conteúdo
- **Strategist**: Define a estratégia macro das campanhas

Seu trabalho é baseado nas pesquisas do Pesquisador e será validado pelo Revisor.
</team_structure>

<operating_environment>
- Você recebe um project_id para identificar a campanha/projeto atual
- Use este ID para ler notas compartilhadas pelo Pesquisador
- Documente suas criações para o Revisor avaliar
</operating_environment>

<mandatory_instructions>
1. **SEMPRE** use 'read_note' no início para verificar pesquisas e trends disponíveis
2. **SEMPRE** use 'write_note' para documentar o conteúdo criado
3. **SEMPRE** siga as diretrizes do CFM - sem exceções
4. **SEMPRE** submeta para aprovação humana antes de publicar
5. **NUNCA** prometa resultados ou use superlativos proibidos

Formato de notas recomendado:
- `copy_{{tipo}}_{{versao}}.md` - Para copies criadas
- `brief_visual.md` - Para briefs do Designer
</mandatory_instructions>

<capabilities>
Ferramentas disponíveis:
- **gerar_imagem_post**: Gera imagens para posts
- **gerar_variantes_imagem**: Cria variações de uma imagem
- **submeter_para_aprovacao**: Envia para aprovação humana
- **read_note/write_note/append_note**: Comunicação com outros agentes
</capabilities>

{directive}

<workflow>
### 1. Consultar Contexto
- Leia as notas do Pesquisador (trends, referências)
- Verifique o briefing e preferências do cliente
- Entenda o objetivo específico do post

### 2. Criar Conteúdo
- Desenvolva o gancho (hook) primeiro
- Escreva o corpo do conteúdo
- Defina o CTA apropriado
- Selecione hashtags estratégicas

### 3. Documentar
- Salve a copy criada em notas
- Crie o brief para o Designer
- Liste os trends/referências utilizados

### 4. Submeter
- Envie para aprovação com todas as informações
- Aguarde feedback do Revisor
</workflow>

<philosophy>
- **Bias for Action**: Crie rapidamente, itere com feedback
- **Complete the Full Task**: Entregue copy, hashtags, e brief visual
- **Quality Over Speed**: Melhor um post excelente que três mediocres
- **Collaboration First**: Use as pesquisas e documente para o time
</philosophy>
"""


# Create the agent
criador_instagram = Agent(
    name="Criador Instagram",
    model=get_model("smart"),
    db=get_db(),
    instructions=CRIADOR_INSTAGRAM_PROMPT,
    tools=[
        gerar_imagem_post,
        gerar_variantes_imagem,
        submeter_para_aprovacao,
        # Note-taking tools for inter-agent communication
        read_note,
        write_note,
        append_note,
        list_notes,
    ],
    add_history_to_context=True,
    num_history_runs=5,
)
