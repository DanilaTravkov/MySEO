export type ProviderStatus = "available" | "planned" | "requires_configuration";

export interface SearchProviderSummary {
  id: string;
  name: string;
  status: ProviderStatus;
  description: string;
}
