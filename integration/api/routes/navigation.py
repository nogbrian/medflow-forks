"""
Cross-service navigation routes.

Provides deep links between Twenty CRM, Cal.com, and Chatwoot
so users can seamlessly navigate between services.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from core.auth import CurrentUser, DBSession, require_clinic_access
from core.config import get_settings
from core.models import Clinic, User

router = APIRouter(prefix="/navigation")
settings = get_settings()


class ServiceLinks(BaseModel):
    """Links to all integrated services."""
    crm: str
    crm_contacts: str
    crm_pipeline: str
    calendar: str
    calendar_bookings: str
    inbox: str
    inbox_conversations: str
    creative_lab: str


class ContactDeepLinks(BaseModel):
    """Deep links for a specific contact across services."""
    contact_id: str
    crm_contact: str | None = None
    calendar_bookings: str | None = None
    inbox_conversations: str | None = None


# =============================================================================
# GLOBAL NAVIGATION
# =============================================================================


@router.get("/services", response_model=ServiceLinks)
async def get_service_links(
    clinic_id: str | None = Query(None),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Get navigation links to all integrated services.

    Returns URLs for:
    - Twenty CRM (contacts, pipeline)
    - Cal.com (calendar, bookings)
    - Chatwoot (inbox, conversations)
    - Creative Lab (content creation)
    """
    # Base URLs - in production these would be configured per environment
    base_domain = settings.cors_origins[0] if settings.cors_origins else "http://localhost"

    # Check if we have clinic-specific IDs
    clinic_params = ""
    if clinic_id:
        require_clinic_access(current_user, clinic_id)
        result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
        clinic = result.scalar_one_or_none()
        if clinic:
            if clinic.twenty_workspace_id:
                clinic_params = f"?workspace={clinic.twenty_workspace_id}"

    return ServiceLinks(
        crm=f"/crm/{clinic_params}",
        crm_contacts=f"/crm/people{clinic_params}",
        crm_pipeline=f"/crm/opportunities{clinic_params}",
        calendar=f"/agenda/{clinic_params}",
        calendar_bookings=f"/agenda/bookings{clinic_params}",
        inbox=f"/inbox/{clinic_params}",
        inbox_conversations=f"/inbox/conversations{clinic_params}",
        creative_lab=f"/api/creative-lab{clinic_params}",
    )


@router.get("/contact/{contact_id}/links", response_model=ContactDeepLinks)
async def get_contact_deep_links(
    contact_id: str,
    clinic_id: str | None = Query(None),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Get deep links for a specific contact across all services.

    Allows jumping directly to:
    - Contact profile in Twenty CRM
    - Bookings for this contact in Cal.com
    - Conversations with this contact in Chatwoot
    """
    if clinic_id:
        require_clinic_access(current_user, clinic_id)

    # Build links based on where the contact exists
    # In a real implementation, we'd look up the contact's IDs in each service
    return ContactDeepLinks(
        contact_id=contact_id,
        crm_contact=f"/crm/person/{contact_id}",
        calendar_bookings=f"/agenda/bookings?attendee={contact_id}",
        inbox_conversations=f"/inbox/contacts/{contact_id}/conversations",
    )


# =============================================================================
# SIDEBAR MENU STRUCTURE
# =============================================================================


@router.get("/menu")
async def get_navigation_menu(
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Get the sidebar navigation menu structure.

    Returns a hierarchical menu for the unified dashboard.
    """
    # Build menu based on user permissions
    menu_items = []

    # Dashboard (everyone)
    menu_items.append({
        "id": "dashboard",
        "label": "Dashboard",
        "icon": "LayoutDashboard",
        "href": "/",
    })

    # CRM Section
    menu_items.append({
        "id": "crm",
        "label": "CRM",
        "icon": "Users",
        "children": [
            {"id": "contacts", "label": "Contatos", "href": "/crm/people", "icon": "User"},
            {"id": "companies", "label": "Empresas", "href": "/crm/companies", "icon": "Building"},
            {"id": "pipeline", "label": "Pipeline", "href": "/crm/opportunities", "icon": "Kanban"},
        ],
    })

    # Calendar Section
    menu_items.append({
        "id": "agenda",
        "label": "Agenda",
        "icon": "Calendar",
        "children": [
            {"id": "bookings", "label": "Agendamentos", "href": "/agenda/bookings", "icon": "CalendarDays"},
            {"id": "availability", "label": "Disponibilidade", "href": "/agenda/availability", "icon": "Clock"},
            {"id": "event_types", "label": "Tipos de Evento", "href": "/agenda/event-types", "icon": "ListChecks"},
        ],
    })

    # Inbox Section
    menu_items.append({
        "id": "inbox",
        "label": "Inbox",
        "icon": "MessageSquare",
        "children": [
            {"id": "conversations", "label": "Conversas", "href": "/inbox/conversations", "icon": "MessagesSquare"},
            {"id": "contacts", "label": "Contatos", "href": "/inbox/contacts", "icon": "ContactRound"},
        ],
    })

    # Creative Lab
    menu_items.append({
        "id": "creative",
        "label": "Creative Lab",
        "icon": "Palette",
        "children": [
            {"id": "chat", "label": "Assistente", "href": "/creative/chat", "icon": "Bot"},
            {"id": "copy", "label": "Copywriter", "href": "/creative/copy", "icon": "PenLine"},
            {"id": "image", "label": "Designer", "href": "/creative/image", "icon": "Image"},
        ],
    })

    # Agents (for agency users)
    if current_user and (current_user.is_superuser or current_user.is_agency_user):
        menu_items.append({
            "id": "agents",
            "label": "Agentes IA",
            "icon": "Bot",
            "children": [
                {"id": "workflows", "label": "Workflows", "href": "/agents/workflows", "icon": "Workflow"},
                {"id": "plans", "label": "Planos", "href": "/agents/plans", "icon": "ClipboardList"},
            ],
        })

    # Settings (admin)
    if current_user and current_user.is_superuser:
        menu_items.append({
            "id": "settings",
            "label": "Configurações",
            "icon": "Settings",
            "children": [
                {"id": "clinics", "label": "Clínicas", "href": "/settings/clinics", "icon": "Hospital"},
                {"id": "users", "label": "Usuários", "href": "/settings/users", "icon": "Users"},
                {"id": "integrations", "label": "Integrações", "href": "/settings/integrations", "icon": "Plug"},
            ],
        })

    return {
        "menu": menu_items,
        "user": {
            "name": current_user.name if current_user else "Guest",
            "role": current_user.role.value if current_user else "guest",
            "avatar": current_user.avatar_url if current_user else None,
        },
    }


# =============================================================================
# QUICK ACTIONS
# =============================================================================


@router.get("/quick-actions")
async def get_quick_actions(
    clinic_id: str | None = Query(None),
    current_user: CurrentUser = None,
):
    """
    Get quick action buttons for the dashboard.

    These are common actions users frequently need.
    """
    actions = [
        {
            "id": "new_contact",
            "label": "Novo Contato",
            "icon": "UserPlus",
            "href": "/crm/people/new",
            "color": "blue",
        },
        {
            "id": "new_appointment",
            "label": "Agendar Consulta",
            "icon": "CalendarPlus",
            "href": "/agenda/bookings/new",
            "color": "green",
        },
        {
            "id": "new_conversation",
            "label": "Nova Conversa",
            "icon": "MessageSquarePlus",
            "href": "/inbox/conversations/new",
            "color": "purple",
        },
        {
            "id": "create_content",
            "label": "Criar Conteúdo",
            "icon": "Sparkles",
            "href": "/creative/chat",
            "color": "orange",
        },
    ]

    return {"actions": actions}


# =============================================================================
# BREADCRUMBS
# =============================================================================


@router.get("/breadcrumbs")
async def get_breadcrumbs(
    path: str = Query(..., description="Current path"),
    current_user: CurrentUser = None,
):
    """
    Get breadcrumb navigation for a given path.

    Helps users understand their location in the app.
    """
    # Parse path and build breadcrumbs
    parts = [p for p in path.split("/") if p]

    breadcrumbs = [{"label": "Início", "href": "/"}]

    # Map path segments to labels
    labels = {
        "crm": "CRM",
        "people": "Contatos",
        "companies": "Empresas",
        "opportunities": "Pipeline",
        "agenda": "Agenda",
        "bookings": "Agendamentos",
        "availability": "Disponibilidade",
        "inbox": "Inbox",
        "conversations": "Conversas",
        "creative": "Creative Lab",
        "chat": "Assistente",
        "agents": "Agentes",
        "settings": "Configurações",
    }

    current_path = ""
    for part in parts:
        current_path += f"/{part}"
        label = labels.get(part, part.replace("-", " ").title())
        breadcrumbs.append({
            "label": label,
            "href": current_path,
        })

    return {"breadcrumbs": breadcrumbs}
