"""Integration tests for webhook endpoints using FastAPI TestClient."""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a test FastAPI app with webhook routes."""
    from fastapi import FastAPI

    # Mock settings before importing routes
    with patch("core.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.evolution_api_key = "test-api-key"
        settings.evolution_api_url = "http://localhost:8080"
        settings.webhook_secret = "test-secret"
        settings.chatwoot_api_url = "http://localhost:3000"
        settings.chatwoot_api_key = "test-key"
        settings.chatwoot_account_id = "1"
        settings.chatwoot_inbox_id = "1"
        settings.chatwoot_human_team_id = "1"
        settings.twenty_api_url = "http://localhost:3001"
        settings.twenty_api_key = "test-key"
        settings.calcom_api_url = "http://localhost:3002"
        settings.calcom_api_key = "test-key"
        settings.anthropic_api_key = "test-key"
        settings.llm_provider = "anthropic"
        settings.model_smart = "claude-sonnet-4-5-20250514"
        settings.model_fast = "claude-haiku-4-20250514"
        settings.meta_access_token = None
        mock_settings.return_value = settings

        app = FastAPI()

        from webhooks.evolution import router as evolution_router
        app.include_router(evolution_router)

        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestEvolutionWebhook:
    """Test Evolution API webhook endpoint."""

    def test_accepts_valid_webhook(self, client):
        """Webhook accepts valid payload with correct API key."""
        payload = {
            "event": "messages.upsert",
            "instance": "clinic-1",
            "data": {
                "key": {
                    "remoteJid": "5511999990000@s.whatsapp.net",
                    "fromMe": False,
                    "id": "msg-123",
                },
                "message": {
                    "conversation": "Olá, gostaria de agendar uma consulta",
                },
                "pushName": "Maria Silva",
                "messageTimestamp": 1706000000,
            },
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200
        assert response.json()["received"] is True
        assert response.json()["event"] == "messages.upsert"

    def test_rejects_invalid_api_key(self, client):
        """Webhook rejects requests with wrong API key."""
        payload = {"event": "messages.upsert", "data": {}}

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "wrong-key"},
        )

        assert response.status_code == 401

    def test_rejects_missing_auth(self, client):
        """Webhook rejects requests with no auth header."""
        payload = {"event": "messages.upsert", "data": {}}

        response = client.post("/webhooks/evolution", json=payload)

        assert response.status_code == 401

    def test_handles_connection_update(self, client):
        """Webhook handles connection status updates."""
        payload = {
            "event": "connection.update",
            "instance": "clinic-1",
            "data": {"state": "open"},
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200
        assert response.json()["event"] == "connection.update"

    def test_handles_message_status(self, client):
        """Webhook handles message status updates."""
        payload = {
            "event": "messages.update",
            "instance": "clinic-1",
            "data": {"status": "DELIVERY_ACK"},
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200

    def test_skips_outgoing_messages(self, client):
        """Webhook ignores outgoing (fromMe) messages."""
        payload = {
            "event": "messages.upsert",
            "instance": "clinic-1",
            "data": {
                "key": {
                    "remoteJid": "5511999990000@s.whatsapp.net",
                    "fromMe": True,
                    "id": "msg-out-1",
                },
                "message": {"conversation": "Hello from bot"},
            },
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200

    def test_skips_group_messages(self, client):
        """Webhook skips group chat messages."""
        payload = {
            "event": "messages.upsert",
            "instance": "clinic-1",
            "data": {
                "key": {
                    "remoteJid": "123456789@g.us",  # Group JID
                    "fromMe": False,
                    "id": "msg-group-1",
                },
                "message": {"conversation": "Group message"},
                "pushName": "Someone",
            },
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200

    def test_handles_image_message(self, client):
        """Webhook handles image messages."""
        payload = {
            "event": "messages.upsert",
            "instance": "clinic-1",
            "data": {
                "key": {
                    "remoteJid": "5511999990000@s.whatsapp.net",
                    "fromMe": False,
                    "id": "msg-img-1",
                },
                "message": {
                    "imageMessage": {
                        "caption": "Check this photo",
                        "url": "https://example.com/image.jpg",
                    },
                },
                "pushName": "Patient",
            },
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200

    def test_handles_audio_message(self, client):
        """Webhook handles audio messages."""
        payload = {
            "event": "messages.upsert",
            "instance": "clinic-1",
            "data": {
                "key": {
                    "remoteJid": "5511999990000@s.whatsapp.net",
                    "fromMe": False,
                    "id": "msg-audio-1",
                },
                "message": {
                    "audioMessage": {"seconds": 30},
                },
                "pushName": "Patient",
            },
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200

    def test_handles_unknown_event(self, client):
        """Webhook handles unknown event types gracefully."""
        payload = {
            "event": "unknown.event",
            "instance": "clinic-1",
            "data": {},
        }

        response = client.post(
            "/webhooks/evolution",
            json=payload,
            headers={"x-api-key": "test-api-key"},
        )

        assert response.status_code == 200
