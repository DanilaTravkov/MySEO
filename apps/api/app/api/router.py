from fastapi import APIRouter

from app.api.routes import analytics, clustering, discovery, health, insights, providers

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(providers.router, prefix="/api")
api_router.include_router(discovery.router, prefix="/api")
api_router.include_router(analytics.router, prefix="/api")
api_router.include_router(clustering.router, prefix="/api")
api_router.include_router(insights.router, prefix="/api")
