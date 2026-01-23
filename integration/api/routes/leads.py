"""API routes for leads - proxies to Twenty CRM."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import require_auth
from core.logging import get_logger
from tools.crm import (
    buscar_lead,
    criar_lead,
    atualizar_lead,
    listar_leads,
    mover_pipeline,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/leads", tags=["Leads"], dependencies=[Depends(require_auth)])


class LeadCreate(BaseModel):
    nome: str
    telefone: str
    email: str | None = None
    origem: str | None = None
    cliente_id: str | None = None


class LeadUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None
    telefone: str | None = None
    etapa_pipeline: str | None = None
    custom_fields: dict[str, Any] | None = None


class PipelineMove(BaseModel):
    etapa: str


@router.get("")
async def list_leads(
    etapa: str | None = Query(None, description="Pipeline stage filter"),
    origem: str | None = Query(None, description="Origin filter"),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """List leads with optional filters."""
    filtros: dict[str, Any] = {}
    if etapa:
        filtros["stage"] = etapa
    if origem:
        filtros["origem"] = origem

    leads = await listar_leads(
        filtros=filtros if filtros else None,
        limite=limite,
        offset=offset,
    )

    return {
        "data": leads,
        "total": len(leads),
        "limite": limite,
        "offset": offset,
    }


@router.get("/search")
async def search_lead(
    telefone: str = Query(..., description="Phone number to search"),
) -> dict:
    """Search for a lead by phone number."""
    lead = await buscar_lead(telefone)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"data": lead}


@router.get("/{lead_id}")
async def get_lead(lead_id: str) -> dict:
    """Get a specific lead by ID."""
    # Twenty CRM uses the people endpoint with ID
    from tools.crm import _client

    try:
        result = await _client._request("GET", f"people/{lead_id}")
        data = result.get("data")
        if not data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"data": data}
    except Exception as e:
        logger.error("Failed to get lead", lead_id=lead_id, error=str(e))
        raise HTTPException(status_code=404, detail="Lead not found")


@router.post("", status_code=201)
async def create_lead(body: LeadCreate) -> dict:
    """Create a new lead in the CRM."""
    lead = await criar_lead(body.model_dump(exclude_none=True))
    if not lead:
        raise HTTPException(status_code=500, detail="Failed to create lead")
    return {"data": lead}


@router.patch("/{lead_id}")
async def update_lead(lead_id: str, body: LeadUpdate) -> dict:
    """Update an existing lead."""
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    lead = await atualizar_lead(lead_id, update_data)
    if not lead:
        raise HTTPException(status_code=500, detail="Failed to update lead")
    return {"data": lead}


@router.post("/{lead_id}/pipeline")
async def move_lead_pipeline(lead_id: str, body: PipelineMove) -> dict:
    """Move a lead to a different pipeline stage."""
    success = await mover_pipeline(lead_id, body.etapa)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to move pipeline stage")
    return {"status": "ok", "lead_id": lead_id, "etapa": body.etapa}
