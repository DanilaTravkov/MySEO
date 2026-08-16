import { Check, FileSpreadsheet, KeyRound, Sparkles } from "lucide-react";

import { PageHeading } from "@/components/page-heading";

export default function SettingsPage() {
  return (
    <>
      <PageHeading eyebrow="Preferences" title="Settings" description="Manage the data sources that power your research experience." />
      <section className="settings-list panel">
        <div className="settings-row"><span className="settings-icon"><FileSpreadsheet size={18} /></span><div><strong>CSV imports</strong><p>Bring historical keyword data into your research workspace.</p></div><span className="state-pill"><Check size={13} /> Available</span></div>
        <div className="settings-row"><span className="settings-icon"><Sparkles size={18} /></span><div><strong>Demo dataset</strong><p>Explore the full analysis workflow with representative sample data.</p></div><span className="state-pill"><Check size={13} /> Available</span></div>
        <div className="settings-row"><span className="settings-icon"><KeyRound size={18} /></span><div><strong>Google Ads</strong><p>Connect your account to research live Keyword Planner demand.</p></div><span className="state-pill neutral">Not connected</span></div>
      </section>
    </>
  );
}
