import { KeywordDetail } from "./keyword-detail";

export default async function KeywordPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <KeywordDetail keywordId={id} />;
}
