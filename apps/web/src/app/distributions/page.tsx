import { PageHeading } from "@/components/page-heading";
import { DistributionLab } from "./distribution-lab";

export default function DistributionsPage() {
  return (
    <>
      <PageHeading
        eyebrow="Signal quality"
        title="Know the shape behind the score."
        description="Explore how demand is distributed, where outliers sit, and when robust statistics deserve more trust."
      />
      <DistributionLab />
    </>
  );
}
