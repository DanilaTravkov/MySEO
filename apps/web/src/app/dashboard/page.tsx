import { PageHeading } from "@/components/page-heading";

import { DashboardOverview } from "./dashboard-overview";

export default function DashboardPage() {
  return (
    <>
      <PageHeading
        eyebrow="Market pulse"
        title="See where demand is moving."
        description="A focused view of market coverage, momentum, and the strongest signals emerging from your research."
        variant="hero"
      />
      <DashboardOverview />
    </>
  );
}
