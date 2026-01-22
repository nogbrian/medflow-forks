"""Internal notification tools."""

from typing import Any

from core.config import get_settings
from core.logging import get_logger

from .whatsapp import get_whatsapp_service

logger = get_logger(__name__)
settings = get_settings()


async def notificar_esposa(
    mensagem: str,
    lead_id: str | None = None,
    tipo: str = "info",
) -> bool:
    """
    Send notification to wife (commercial partner) via WhatsApp.

    Args:
        mensagem: Notification message
        lead_id: Optional lead ID for context
        tipo: Notification type (info, urgente, lead_quente)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        whatsapp = get_whatsapp_service()

        # Format message with context
        emoji_map = {
            "info": "📋",
            "urgente": "🚨",
            "lead_quente": "🔥",
            "aprovacao": "✅",
            "erro": "❌",
        }

        emoji = emoji_map.get(tipo, "📋")
        formatted_message = f"{emoji} *{tipo.upper()}*\n\n{mensagem}"

        if lead_id:
            formatted_message += f"\n\n_Lead ID: {lead_id}_"

        # Get wife's number from environment or config
        # This should be configured in a more secure way in production
        numero_esposa = "5511999999999"  # Placeholder

        result = await whatsapp.enviar_mensagem(
            instance=settings.evolution_instance_agencia,
            destinatario=numero_esposa,
            mensagem=formatted_message,
        )

        if result.success:
            logger.info(
                "Wife notified",
                tipo=tipo,
                lead_id=lead_id,
            )
            return True

        logger.error("Failed to notify wife", error=result.error)
        return False

    except Exception as e:
        logger.error("Failed to notify wife", error=str(e))
        return False


async def notificar_admin(
    tipo: str,
    dados: dict[str, Any],
) -> bool:
    """
    Send notification to admin dashboard/system.

    Args:
        tipo: Notification type (erro, alerta, info, metrica)
        dados: Notification data

    Returns:
        True if recorded successfully, False otherwise
    """
    try:
        # For now, just log the notification
        # In production, this could:
        # - Push to a real-time dashboard via WebSocket
        # - Send to Slack/Discord
        # - Store in Redis for dashboard polling
        # - Trigger email alerts for critical issues

        log_method = logger.error if tipo == "erro" else logger.info

        log_method(
            "Admin notification",
            notification_type=tipo,
            data=dados,
        )

        # Store in Redis for dashboard
        from core.redis import cache_set

        notification = {
            "tipo": tipo,
            "dados": dados,
            "timestamp": "now",  # Will be set properly
        }

        # Store with TTL of 24 hours
        await cache_set(
            f"notification:{tipo}:{dados.get('id', 'unknown')}",
            notification,
            expire=86400,
        )

        return True

    except Exception as e:
        logger.error("Failed to notify admin", error=str(e))
        return False


async def notificar_cliente_medico(
    cliente_id: str,
    mensagem: str,
    tipo: str = "info",
) -> bool:
    """
    Send notification to a medical client.

    Args:
        cliente_id: Client (doctor) ID
        mensagem: Notification message
        tipo: Notification type

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Get client data from database
        from core.database import AsyncSessionLocal
        from core.models import Cliente
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Cliente).where(Cliente.id == cliente_id)
            )
            cliente = result.scalar_one_or_none()

            if not cliente:
                logger.error("Client not found", cliente_id=cliente_id)
                return False

            whatsapp = get_whatsapp_service()

            emoji_map = {
                "info": "ℹ️",
                "aprovacao_pendente": "📝",
                "publicado": "🎉",
                "relatorio": "📊",
            }

            emoji = emoji_map.get(tipo, "ℹ️")
            formatted_message = f"{emoji} *Tráfego para Consultórios*\n\n{mensagem}"

            result = await whatsapp.enviar_mensagem(
                instance=cliente.evolution_instance,
                destinatario=cliente.whatsapp,
                mensagem=formatted_message,
            )

            if result.success:
                logger.info(
                    "Client notified",
                    cliente_id=cliente_id,
                    tipo=tipo,
                )
                return True

            return False

    except Exception as e:
        logger.error("Failed to notify client", cliente_id=cliente_id, error=str(e))
        return False
