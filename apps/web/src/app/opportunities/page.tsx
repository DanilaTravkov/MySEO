import { PageHeading } from "@/components/page-heading";

import { OpportunityBoard } from "./opportunity-board";

export default function OpportunitiesPage() {
  return (
    <>
      <PageHeading eyebrow="Decision space" title="Ideas worth building." description="Prioritized market opportunities, supported by transparent demand and commercial signals." />
      <div data-tour="opportunity-board"><OpportunityBoard /></div>
    </>
  );
}
