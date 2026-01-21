"""Evolution API WhatsApp Provider implementation."""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.logging import get_logger

from ..service import WhatsAppServiceBase
from ..types import Button, ListSection, SendMessageResult

logger = get_logger(__name__)


class EvolutionProvider(WhatsAppServiceBase):
    """Evolution API implementation for WhatsApp messaging."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json",
        }

    def _format_phone(self, phone: str) -> str:
        """Format phone number to WhatsApp format."""
        # Remove any non-numeric characters
        phone = "".join(filter(str.isdigit, phone))
        # Ensure it starts with country code
        if not phone.startswith("55"):
            phone = f"55{phone}"
        return phone

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        instance: str,
        json_data: dict | None = None,
    ) -> dict:
        """Make an HTTP request to Evolution API."""
        url = f"{self.api_url}/{endpoint}/{instance}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()

    async def enviar_mensagem(
        self,
        instance: str,
        destinatario: str,
        mensagem: str,
    ) -> SendMessageResult:
        try:
            phone = self._format_phone(destinatario)
            data = {
                "number": phone,
                "text": mensagem,
            }

            result = await self._request("POST", "message/sendText", instance, data)

            logger.info(
                "Message sent",
                instance=instance,
                destinatario=phone,
                message_id=result.get("key", {}).get("id"),
            )

            return SendMessageResult(
                success=True,
                message_id=result.get("key", {}).get("id"),
            )

        except Exception as e:
            logger.error(
                "Failed to send message",
                instance=instance,
                destinatario=destinatario,
                error=str(e),
            )
            return SendMessageResult(success=False, error=str(e))

    async def enviar_imagem(
        self,
        instance: str,
        destinatario: str,
        url: str,
        caption: str | None = None,
    ) -> SendMessageResult:
        try:
            phone = self._format_phone(destinatario)
            data = {
                "number": phone,
                "media": url,
                "mediatype": "image",
            }
            if caption:
                data["caption"] = caption

            result = await self._request("POST", "message/sendMedia", instance, data)

            return SendMessageResult(
                success=True,
                message_id=result.get("key", {}).get("id"),
            )

        except Exception as e:
            logger.error("Failed to send image", error=str(e))
            return SendMessageResult(success=False, error=str(e))

    async def enviar_documento(
        self,
        instance: str,
        destinatario: str,
        url: str,
        filename: str,
        caption: str | None = None,
    ) -> SendMessageResult:
        try:
            phone = self._format_phone(destinatario)
            data = {
                "number": phone,
                "media": url,
                "mediatype": "document",
                "fileName": filename,
            }
            if caption:
                data["caption"] = caption

            result = await self._request("POST", "message/sendMedia", instance, data)

            return SendMessageResult(
                success=True,
                message_id=result.get("key", {}).get("id"),
            )

        except Exception as e:
            logger.error("Failed to send document", error=str(e))
            return SendMessageResult(success=False, error=str(e))

    async def enviar_audio(
        self,
        instance: str,
        destinatario: str,
        url: str,
    ) -> SendMessageResult:
        try:
            phone = self._format_phone(destinatario)
            data = {
                "number": phone,
                "audio": url,
            }

            result = await self._request("POST", "message/sendWhatsAppAudio", instance, data)

            return SendMessageResult(
                success=True,
                message_id=result.get("key", {}).get("id"),
            )

        except Exception as e:
            logger.error("Failed to send audio", error=str(e))
            return SendMessageResult(success=False, error=str(e))

    async def enviar_botoes(
        self,
        instance: str,
        destinatario: str,
        texto: str,
        botoes: list[Button],
        header: str | None = None,
        footer: str | None = None,
    ) -> SendMessageResult:
        try:
            phone = self._format_phone(destinatario)
            data = {
                "number": phone,
                "title": header or "",
                "description": texto,
                "footer": footer or "",
                "buttons": [
                    {"type": "reply", "buttonId": b.id, "buttonText": {"displayText": b.title}}
                    for b in botoes
                ],
            }

            result = await self._request("POST", "message/sendButtons", instance, data)

            return SendMessageResult(
                success=True,
                message_id=result.get("key", {}).get("id"),
            )

        except Exception as e:
            logger.error("Failed to send buttons", error=str(e))
            return SendMessageResult(success=False, error=str(e))

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
        try:
            phone = self._format_phone(destinatario)
            data = {
                "number": phone,
                "title": header or "",
                "description": texto,
                "buttonText": botao_texto,
                "footerText": footer or "",
                "sections": [
                    {
                        "title": section.title,
                        "rows": [
                            {
                                "rowId": row.id,
                                "title": row.title,
                                "description": row.description or "",
                            }
                            for row in section.rows
                        ],
                    }
                    for section in secoes
                ],
            }

            result = await self._request("POST", "message/sendList", instance, data)

            return SendMessageResult(
                success=True,
                message_id=result.get("key", {}).get("id"),
            )

        except Exception as e:
            logger.error("Failed to send list", error=str(e))
            return SendMessageResult(success=False, error=str(e))

    async def marcar_como_lido(
        self,
        instance: str,
        message_id: str,
    ) -> bool:
        try:
            data = {"read_messages": [{"id": message_id}]}
            await self._request("POST", "chat/markMessageAsRead", instance, data)
            return True

        except Exception as e:
            logger.error("Failed to mark as read", error=str(e))
            return False

    async def enviar_reacao(
        self,
        instance: str,
        destinatario: str,
        message_id: str,
        emoji: str,
    ) -> SendMessageResult:
        try:
            phone = self._format_phone(destinatario)
            data = {
                "key": {"id": message_id, "remoteJid": f"{phone}@s.whatsapp.net"},
                "reaction": emoji,
            }

            result = await self._request("POST", "message/sendReaction", instance, data)

            return SendMessageResult(
                success=True,
                message_id=result.get("key", {}).get("id"),
            )

        except Exception as e:
            logger.error("Failed to send reaction", error=str(e))
            return SendMessageResult(success=False, error=str(e))

    async def verificar_numero(
        self,
        instance: str,
        numero: str,
    ) -> bool:
        try:
            phone = self._format_phone(numero)
            data = {"numbers": [phone]}

            result = await self._request("POST", "chat/whatsappNumbers", instance, data)

            # Check if the number exists in WhatsApp
            numbers = result.get("data", [])
            return any(n.get("exists", False) for n in numbers if n.get("jid", "").startswith(phone))

        except Exception as e:
            logger.error("Failed to verify number", error=str(e))
            return False
