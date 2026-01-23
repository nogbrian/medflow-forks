from fastapi import APIRouter

from app.api.endpoints import scrape, ads, ai

api_router = APIRouter()
api_router.include_router(scrape.router, tags=["scrape"])
api_router.include_router(ads.router, prefix="/ads", tags=["ads"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
