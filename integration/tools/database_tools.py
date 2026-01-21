"""Direct database query tools for agents."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select

from core.database import AsyncSessionLocal
from core.logging import get_logger
from core.models import Aprovacao, AprovacaoStatus, AprovacaoTipo, Cliente, Conversa, Mensagem

logger = get_logger(__name__)


async def buscar_contexto_cliente(cliente_id: str) -> dict[str, Any] | None:
    """
    Fetch complete client context for agent use.

    Args:
        cliente_id: Client UUID

    Returns:
        Client context data if found, None otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Cliente).where(Cliente.id == cliente_id)
            )
            cliente = result.scalar_one_or_none()

            if not cliente:
                logger.warning("Client not found", cliente_id=cliente_id)
                return None

            logger.info("Client context fetched", cliente_id=cliente_id)

            return {
                "id": cliente.id,
                "nome": cliente.nome,
                "especialidade": cliente.especialidade,
                "cidade": cliente.cidade,
                "estado": cliente.estado,
                "evolution_instance": cliente.evolution_instance,
                "google_calendar_id": cliente.google_calendar_id,
                "contexto": cliente.contexto,
            }

    except Exception as e:
        logger.error("Failed to fetch client context", cliente_id=cliente_id, error=str(e))
        return None


async def salvar_mensagem(
    conversa_id: str,
    dados: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Save a message to the conversation history.

    Args:
        conversa_id: Conversation UUID
        dados: Message data (direcao, tipo, conteudo, wamid)

    Returns:
        Created message data if successful, None otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            mensagem = Mensagem(
                conversa_id=conversa_id,
                direcao=dados["direcao"],
                tipo=dados["tipo"],
                conteudo=dados["conteudo"],
                wamid=dados.get("wamid"),
            )

            session.add(mensagem)

            # Update conversation timestamps
            conversa = await session.get(Conversa, conversa_id)
            if conversa:
                if dados["direcao"] == "inbound":
                    conversa.ultima_msg_usuario = datetime.utcnow()
                    # Extend 24h window
                    conversa.janela_expira_em = datetime.utcnow() + timedelta(hours=24)
                else:
                    conversa.ultima_msg_enviada = datetime.utcnow()

            await session.commit()
            await session.refresh(mensagem)

            logger.info("Message saved", message_id=mensagem.id, conversa_id=conversa_id)

            return {
                "id": mensagem.id,
                "conversa_id": mensagem.conversa_id,
                "direcao": mensagem.direcao.value,
                "tipo": mensagem.tipo.value,
                "created_at": mensagem.created_at.isoformat(),
            }

    except Exception as e:
        logger.error("Failed to save message", conversa_id=conversa_id, error=str(e))
        return None


async def criar_aprovacao(dados: dict[str, Any]) -> dict[str, Any] | None:
    """
    Create an approval request for content.

    Args:
        dados: Approval data (cliente_id, tipo, conteudo, criado_por_agent, agendado_para)

    Returns:
        Created approval data if successful, None otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            aprovacao = Aprovacao(
                cliente_id=dados["cliente_id"],
                tipo=AprovacaoTipo(dados["tipo"]),
                conteudo=dados["conteudo"],
                criado_por_agent=dados["criado_por_agent"],
                agendado_para=dados.get("agendado_para"),
            )

            session.add(aprovacao)
            await session.commit()
            await session.refresh(aprovacao)

            logger.info(
                "Approval created",
                approval_id=aprovacao.id,
                tipo=aprovacao.tipo.value,
                cliente_id=aprovacao.cliente_id,
            )

            return {
                "id": aprovacao.id,
                "cliente_id": aprovacao.cliente_id,
                "tipo": aprovacao.tipo.value,
                "status": aprovacao.status.value,
                "criado_por_agent": aprovacao.criado_por_agent,
                "created_at": aprovacao.created_at.isoformat(),
            }

    except Exception as e:
        logger.error("Failed to create approval", error=str(e))
        return None


async def atualizar_aprovacao(
    aprovacao_id: str,
    status: str,
    aprovado_por: str | None = None,
    feedback: str | None = None,
) -> dict[str, Any] | None:
    """
    Update an approval status.

    Args:
        aprovacao_id: Approval UUID
        status: New status (aprovado, rejeitado, editado)
        aprovado_por: User ID who approved/rejected
        feedback: Optional feedback message

    Returns:
        Updated approval data if successful, None otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            aprovacao = await session.get(Aprovacao, aprovacao_id)

            if not aprovacao:
                logger.warning("Approval not found", aprovacao_id=aprovacao_id)
                return None

            aprovacao.status = AprovacaoStatus(status)
            if aprovado_por:
                aprovacao.aprovado_por = aprovado_por
            if feedback:
                aprovacao.feedback = feedback

            await session.commit()
            await session.refresh(aprovacao)

            logger.info(
                "Approval updated",
                approval_id=aprovacao.id,
                status=aprovacao.status.value,
            )

            return {
                "id": aprovacao.id,
                "status": aprovacao.status.value,
                "aprovado_por": aprovacao.aprovado_por,
                "feedback": aprovacao.feedback,
                "updated_at": aprovacao.updated_at.isoformat(),
            }

    except Exception as e:
        logger.error("Failed to update approval", aprovacao_id=aprovacao_id, error=str(e))
        return None


async def buscar_historico_conversa(
    conversa_id: str,
    limite: int = 50,
) -> list[dict[str, Any]]:
    """
    Fetch conversation message history.

    Args:
        conversa_id: Conversation UUID
        limite: Maximum messages to return

    Returns:
        List of messages in chronological order
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Mensagem)
                .where(Mensagem.conversa_id == conversa_id)
                .order_by(Mensagem.created_at.desc())
                .limit(limite)
            )
            mensagens = result.scalars().all()

            # Return in chronological order
            return [
                {
                    "id": m.id,
                    "direcao": m.direcao.value,
                    "tipo": m.tipo.value,
                    "conteudo": m.conteudo,
                    "created_at": m.created_at.isoformat(),
                }
                for m in reversed(mensagens)
            ]

    except Exception as e:
        logger.error("Failed to fetch conversation history", conversa_id=conversa_id, error=str(e))
        return []


async def buscar_aprovacoes_pendentes(
    cliente_id: str | None = None,
    limite: int = 20,
) -> list[dict[str, Any]]:
    """
    Fetch pending approvals.

    Args:
        cliente_id: Optional client ID filter
        limite: Maximum approvals to return

    Returns:
        List of pending approvals
    """
    try:
        async with AsyncSessionLocal() as session:
            query = select(Aprovacao).where(
                Aprovacao.status == AprovacaoStatus.PENDENTE
            )

            if cliente_id:
                query = query.where(Aprovacao.cliente_id == cliente_id)

            query = query.order_by(Aprovacao.created_at.desc()).limit(limite)

            result = await session.execute(query)
            aprovacoes = result.scalars().all()

            return [
                {
                    "id": a.id,
                    "cliente_id": a.cliente_id,
                    "tipo": a.tipo.value,
                    "conteudo": a.conteudo,
                    "criado_por_agent": a.criado_por_agent,
                    "agendado_para": a.agendado_para.isoformat() if a.agendado_para else None,
                    "created_at": a.created_at.isoformat(),
                }
                for a in aprovacoes
            ]

    except Exception as e:
        logger.error("Failed to fetch pending approvals", error=str(e))
        return []
