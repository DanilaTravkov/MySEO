from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    id: str
    name: str
    status: str
    description: str


def provider_registry() -> tuple[ProviderDescriptor, ...]:
    return (
        ProviderDescriptor(
            id="mock",
            name="Mock dataset",
            status="available",
            description="Deterministic local dataset with varied demand patterns.",
        ),
        ProviderDescriptor(
            id="csv",
            name="CSV import",
            status="available",
            description="Validated user-supplied historical metrics.",
        ),
        ProviderDescriptor(
            id="google_ads",
            name="Google Ads",
            status="requires_configuration",
            description="Optional provider gated by explicit credential setup.",
        ),
    )
