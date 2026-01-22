"""WhatsApp Service - Abstract interface for WhatsApp providers."""

from abc import ABC, abstractmethod
from functools import lru_cache

from core.config import get_settings

from .types import Button, ListSection, SendMessageResult


class WhatsAppServiceBase(ABC):
    """Abstract base class for WhatsApp service implementations."""

    @abstractmethod
    async def enviar_mensagem(
        self,
        instance: str,
        destinatario: str,
        mensagem: str,
    ) -> SendMessageResult:
        """Send a text message."""
        pass

    @abstractmethod
    async def enviar_imagem(
        self,
        instance: str,
        destinatario: str,
        url: str,
        caption: str | None = None,
    ) -> SendMessageResult:
        """Send an image with optional caption."""
        pass

    @abstractmethod
    async def enviar_documento(
        self,
        instance: str,
        destinatario: str,
        url: str,
        filename: str,
        caption: str | None = None,
    ) -> SendMessageResult:
        """Send a document."""
        pass

    @abstractmethod
    async def enviar_audio(
        self,
        instance: str,
        destinatario: str,
        url: str,
    ) -> SendMessageResult:
        """Send an audio message."""
        pass

    @abstractmethod
    async def enviar_botoes(
        self,
        instance: str,
        destinatario: str,
        texto: str,
        botoes: list[Button],
        header: str | None = None,
        footer: str | None = None,
    ) -> SendMessageResult:
        """Send an interactive message with buttons."""
        pass

    @abstractmethod
    async def enviar_lista(
        self,
        instance: str,
        destinatario: str,
        texto: str,
        botao_texto: str,
        secoes: list[ListSection],
        header: str | None = None,
        footer: str | None = None,
    ) -> SendMessageResult:
        """Send an interactive list message."""
        pass

    @abstractmethod
    async def marcar_como_lido(
        self,
        instance: str,
        message_id: str,
    ) -> bool:
        """Mark a message as read."""
        pass

    @abstractmethod
    async def enviar_reacao(
        self,
        instance: str,
        destinatario: str,
        message_id: str,
        emoji: str,
    ) -> SendMessageResult:
        """Send a reaction to a message."""
        pass

    @abstractmethod
    async def verificar_numero(
        self,
        instance: str,
        numero: str,
    ) -> bool:
        """Check if a phone number has WhatsApp."""
        pass


class WhatsAppService(WhatsAppServiceBase):
    """
    WhatsApp service that delegates to the configured provider.

    This class provides a unified interface regardless of the
    underlying provider (Evolution API, Meta Cloud API, etc.).
    """

    def __init__(self):
        settings = get_settings()
        # Default to Evolution API provider
        from .providers.evolution import EvolutionProvider

        self._provider = EvolutionProvider(
            api_url=settings.evolution_api_url,
            api_key=settings.evolution_api_key,
        )

    async def enviar_mensagem(
        self,
        instance: str,
        destinatario: str,
        mensagem: str,
    ) -> SendMessageResult:
        return await self._provider.enviar_mensagem(instance, destinatario, mensagem)

    async def enviar_imagem(
        self,
        instance: str,
        destinatario: str,
        url: str,
        caption: str | None = None,
    ) -> SendMessageResult:
        return await self._provider.enviar_imagem(instance, destinatario, url, caption)

    async def enviar_documento(
        self,
        instance: str,
        destinatario: str,
        url: str,
        filename: str,
        caption: str | None = None,
    ) -> SendMessageResult:
        return await self._provider.enviar_documento(
            instance, destinatario, url, filename, caption
        )

    async def enviar_audio(
        self,
        instance: str,
        destinatario: str,
        url: str,
    ) -> SendMessageResult:
        return await self._provider.enviar_audio(instance, destinatario, url)

    async def enviar_botoes(
        self,
        instance: str,
        destinatario: str,
        texto: str,
        botoes: list[Button],
        header: str | None = None,
        footer: str | None = None,
    ) -> SendMessageResult:
        return await self._provider.enviar_botoes(
            instance, destinatario, texto, botoes, header, footer
        )

    async def enviar_lista(
        self,
        instance: str,
        destinatario: str,
        texto: str,
        botao_texto: str,
        secoes: list[ListSection],
        header: str | None = None,
        footer: str | None = None,
    ) -> SendMessageResult:
        return await self._provider.enviar_lista(
            instance, destinatario, texto, botao_texto, secoes, header, footer
        )

    async def marcar_como_lido(
        self,
        instance: str,
        message_id: str,
    ) -> bool:
        return await self._provider.marcar_como_lido(instance, message_id)

    async def enviar_reacao(
        self,
        instance: str,
        destinatario: str,
        message_id: str,
        emoji: str,
    ) -> SendMessageResult:
        return await self._provider.enviar_reacao(
            instance, destinatario, message_id, emoji
        )

    async def verificar_numero(
        self,
        instance: str,
        numero: str,
    ) -> bool:
        return await self._provider.verificar_numero(instance, numero)


@lru_cache
def get_whatsapp_service() -> WhatsAppService:
    """Get cached WhatsApp service instance."""
    return WhatsAppService()
