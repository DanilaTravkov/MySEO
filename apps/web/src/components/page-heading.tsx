import type { ReactNode } from "react";

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
  variant = "workspace",
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
  variant?: "hero" | "workspace";
}) {
  return (
    <header className={`page-heading page-heading-${variant}`}>
      <div className="page-heading-copy">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action ? <div className="page-heading-aside">{action}</div> : null}
    </header>
  );
}
