import { PageHeading } from "@/components/page-heading";
import { FunctionWorkspace } from "./function-workspace";

export default function FunctionsPage() {
  return (
    <>
      <PageHeading
        action={<span><i /> Execution service online</span>}
        eyebrow="Cloud execution"
        title="Search verification functions"
        description="Run focused checks against current search results, inspect live signals, and turn fresh evidence into a repeatable research workflow."
      />
      <FunctionWorkspace />
    </>
  );
}
