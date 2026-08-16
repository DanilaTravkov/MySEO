from fastapi import APIRouter
from pydantic import BaseModel

from app.providers.registry import provider_registry

router = APIRouter(tags=["providers"])


class ProviderResponse(BaseModel):
    id: str
    name: str
    status: str
    description: str


@router.get("/providers", response_model=list[ProviderResponse])
def list_providers() -> list[ProviderResponse]:
    return [
        ProviderResponse.model_validate(provider, from_attributes=True)
        for provider in provider_registry()
    ]
