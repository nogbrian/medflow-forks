"""Integration tests for API proxy routes (leads, bookings, conversations, dashboard)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from api.routes.leads import router as leads_router
from api.routes.bookings import router as bookings_router
from api.routes.conversations import router as conversations_router
from api.routes.dashboard import router as dashboard_router


@pytest.fixture
def mock_crm_client():
    """Mock Twenty CRM client."""
    with patch("tools.crm._client") as mock_client:
        mock_client._request = AsyncMock()
        yield mock_client


@pytest.fixture
def mock_calcom_service():
    """Mock Cal.com service."""
    service = MagicMock()
    service.verificar_disponibilidade = AsyncMock(return_value=[])
    service.listar_agendamentos = AsyncMock(return_value=[])
    service.criar_agendamento = AsyncMock(return_value=None)
    service.cancelar_agendamento = AsyncMock(return_value=True)
    service.reagendar = AsyncMock(return_value=None)
    service.buscar_event_types = AsyncMock(return_value=[])

    # Patch both the import location and the route module location
    with patch("tools.calendar.get_calcom_service", return_value=service):
        with patch("api.routes.bookings.get_calcom_service", return_value=service):
            with patch("api.routes.dashboard.get_calcom_service", return_value=service):
                yield service


@pytest.fixture
def mock_chatwoot_service():
    """Mock Chatwoot service."""
    service = MagicMock()
    service._request = AsyncMock(return_value={"payload": [], "meta": {}})
    service.enviar_mensagem = AsyncMock(return_value={"id": 1})
    service.transferir_para_humano = AsyncMock(return_value=True)
    service.atualizar_status = AsyncMock(return_value=True)
    service.adicionar_labels = AsyncMock(return_value=True)

    with patch("tools.chatwoot.get_chatwoot_service", return_value=service):
        with patch("api.routes.conversations.get_chatwoot_service", return_value=service):
            with patch("api.routes.dashboard.get_chatwoot_service", return_value=service):
                yield service


@pytest.fixture
def app():
    """Create a test app with just the proxy routes (auth overridden)."""
    from fastapi import FastAPI

    from api.deps import require_auth

    test_app = FastAPI()
    test_app.include_router(leads_router, prefix="/api")
    test_app.include_router(bookings_router, prefix="/api")
    test_app.include_router(conversations_router, prefix="/api")
    test_app.include_router(dashboard_router, prefix="/api")

    # Override auth dependency for testing
    test_app.dependency_overrides[require_auth] = lambda: {"sub": "test-user"}

    return test_app


@pytest.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestLeadsRoutes:
    """Test leads API routes."""

    @pytest.mark.asyncio
    async def test_list_leads(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {
            "data": {"people": [
                {"id": "1", "name": {"firstName": "Maria", "lastName": "Silva"}},
                {"id": "2", "name": {"firstName": "João", "lastName": "Santos"}},
            ]}
        }

        response = await client.get("/api/leads")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_leads_with_filters(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {"data": {"people": []}}

        response = await client.get("/api/leads?etapa=hot&limite=10&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["limite"] == 10
        assert data["offset"] == 5

    @pytest.mark.asyncio
    async def test_search_lead_found(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {
            "data": {"people": [
                {"id": "1", "name": {"firstName": "Maria"}, "phones": {"primaryPhoneNumber": "5511999990000"}},
            ]}
        }

        response = await client.get("/api/leads/search?telefone=5511999990000")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == "1"

    @pytest.mark.asyncio
    async def test_search_lead_not_found(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {"data": {"people": []}}

        response = await client.get("/api/leads/search?telefone=0000000000")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_lead(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {
            "data": {"id": "new-1", "name": {"firstName": "Test"}}
        }

        response = await client.post(
            "/api/leads",
            json={"nome": "Test User", "telefone": "5511999990000", "email": "test@test.com"},
        )
        assert response.status_code == 201
        assert response.json()["data"]["id"] == "new-1"

    @pytest.mark.asyncio
    async def test_update_lead(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {
            "data": {"id": "1", "stage": "hot"}
        }

        response = await client.patch(
            "/api/leads/1",
            json={"etapa_pipeline": "hot"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_lead_empty_body(self, client, mock_crm_client):
        response = await client.patch("/api/leads/1", json={})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_move_pipeline(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {}

        response = await client.post(
            "/api/leads/1/pipeline",
            json={"etapa": "qualified"},
        )
        assert response.status_code == 200
        assert response.json()["etapa"] == "qualified"


class TestBookingsRoutes:
    """Test bookings API routes."""

    @pytest.mark.asyncio
    async def test_list_bookings(self, client, mock_calcom_service):
        mock_calcom_service.listar_agendamentos.return_value = [
            {"id": 1, "uid": "abc", "titulo": "Consulta", "inicio": "2026-01-22T09:00:00"},
        ]

        response = await client.get("/api/bookings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["uid"] == "abc"

    @pytest.mark.asyncio
    async def test_get_availability(self, client, mock_calcom_service):
        mock_calcom_service.verificar_disponibilidade.return_value = [
            {"data": "2026-01-22", "inicio": "09:00", "disponivel": True},
        ]

        response = await client.get("/api/bookings/availability?data=2026-01-22")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_create_booking(self, client, mock_calcom_service):
        mock_calcom_service.criar_agendamento.return_value = {
            "id": 99, "uid": "new-uid", "titulo": "Consulta"
        }

        response = await client.post(
            "/api/bookings",
            json={
                "lead_id": "lead-1",
                "horario": "2026-01-23T10:00:00",
                "nome": "Maria Silva",
                "email": "maria@test.com",
                "telefone": "5511999990000",
            },
        )
        assert response.status_code == 201
        assert response.json()["data"]["uid"] == "new-uid"

    @pytest.mark.asyncio
    async def test_create_booking_failure(self, client, mock_calcom_service):
        mock_calcom_service.criar_agendamento.return_value = None

        response = await client.post(
            "/api/bookings",
            json={
                "lead_id": "lead-1",
                "horario": "2026-01-23T10:00:00",
                "nome": "Maria Silva",
                "email": "maria@test.com",
                "telefone": "5511999990000",
            },
        )
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_cancel_booking(self, client, mock_calcom_service):
        mock_calcom_service.cancelar_agendamento.return_value = True

        response = await client.request(
            "DELETE",
            "/api/bookings/99",
            json={"motivo": "Paciente cancelou"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_reschedule_booking(self, client, mock_calcom_service):
        mock_calcom_service.reagendar.return_value = {
            "id": 99, "inicio": "2026-01-24T11:00:00"
        }

        response = await client.patch(
            "/api/bookings/99/reschedule",
            json={"new_start": "2026-01-24T11:00:00", "motivo": "Conflito"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_event_types(self, client, mock_calcom_service):
        mock_calcom_service.buscar_event_types.return_value = [
            {"id": 1, "titulo": "Consulta Geral", "duracao_minutos": 30},
        ]

        response = await client.get("/api/bookings/event-types")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1


class TestConversationsRoutes:
    """Test conversations API routes."""

    @pytest.mark.asyncio
    async def test_list_conversations(self, client, mock_chatwoot_service):
        mock_chatwoot_service._request.return_value = {
            "payload": [{"id": 1, "status": "open"}],
            "meta": {"all_count": 1},
        }

        response = await client.get("/api/conversations")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_conversation(self, client, mock_chatwoot_service):
        mock_chatwoot_service._request.return_value = {
            "id": 1, "status": "open", "messages_count": 5,
        }

        response = await client.get("/api/conversations/1")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == 1

    @pytest.mark.asyncio
    async def test_send_message(self, client, mock_chatwoot_service):
        mock_chatwoot_service.enviar_mensagem.return_value = {"id": 42, "content": "Hello"}

        response = await client.post(
            "/api/conversations/1/messages",
            json={"content": "Hello"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["id"] == 42

    @pytest.mark.asyncio
    async def test_transfer_to_human(self, client, mock_chatwoot_service):
        response = await client.post(
            "/api/conversations/1/transfer",
            json={"motivo": "Paciente insistiu"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "transferred"

    @pytest.mark.asyncio
    async def test_update_status(self, client, mock_chatwoot_service):
        response = await client.post(
            "/api/conversations/1/status",
            json={"status": "resolved"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_add_labels(self, client, mock_chatwoot_service):
        response = await client.post(
            "/api/conversations/1/labels",
            json={"labels": ["vip", "urgent"]},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_conversation_stats(self, client, mock_chatwoot_service):
        mock_chatwoot_service._request.return_value = {
            "data": {"meta": {"all_count": 5}},
        }

        response = await client.get("/api/conversations/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "open" in stats
        assert "pending" in stats


class TestDashboardRoutes:
    """Test dashboard aggregation routes."""

    @pytest.mark.asyncio
    async def test_dashboard_metrics(
        self, client, mock_crm_client, mock_calcom_service, mock_chatwoot_service
    ):
        mock_crm_client._request.return_value = {
            "data": {"people": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}
        }
        mock_calcom_service.listar_agendamentos.return_value = [
            {"id": 1}, {"id": 2},
        ]
        mock_chatwoot_service._request.return_value = {
            "data": {"meta": {"all_count": 10}},
        }

        response = await client.get("/api/dashboard/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["leads_total"] == 3
        assert data["bookings_upcoming"] == 2
        assert "conversion_rate" in data
        assert "period" in data

    @pytest.mark.asyncio
    async def test_recent_leads(self, client, mock_crm_client):
        mock_crm_client._request.return_value = {
            "data": {"people": [
                {"id": "1", "name": {"firstName": "Ana"}},
            ]}
        }

        response = await client.get("/api/dashboard/recent-leads")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_upcoming_bookings(self, client, mock_calcom_service):
        mock_calcom_service.listar_agendamentos.return_value = [
            {"id": 1, "titulo": "Consulta", "inicio": "2026-01-22T09:00:00"},
        ]

        response = await client.get("/api/dashboard/upcoming-bookings")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_metrics_handles_failures(
        self, client, mock_crm_client, mock_calcom_service, mock_chatwoot_service
    ):
        """Dashboard metrics still returns data even if some services fail."""
        mock_crm_client._request.side_effect = Exception("CRM down")
        mock_calcom_service.listar_agendamentos.side_effect = Exception("Cal.com down")
        mock_chatwoot_service._request.side_effect = Exception("Chatwoot down")

        response = await client.get("/api/dashboard/metrics")
        assert response.status_code == 200
        data = response.json()
        # Should return zeros, not error
        assert data["leads_total"] == 0
        assert data["bookings_upcoming"] == 0
        assert data["conversations_active"] == 0
