"use client";

import { Check, ChevronLeft, ChevronRight, Cookie, ExternalLink, ShieldCheck, X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from "react";

import { updateCurrentUser } from "../lib/auth-client";
import { cacheExperienceLevel } from "../lib/experience-level";

const CONSENT_KEY = "myseo-cookie-consent";
const TOUR_KEY = "myseo-product-tour";

type LegalDocument = "terms" | "privacy" | "cookies";
type ConsentChoice = "all" | "necessary";
type TourRect = { left: number; top: number; width: number; height: number };
type TourSide = "top" | "right" | "bottom" | "left";
type TourStep = {
  path: string;
  selector: string;
  eyebrow: string;
  title: string;
  body: string;
  details: ReadonlyArray<{ label: string; text: string }>;
  coachWidth?: number;
  preferredSide: TourSide;
  primaryAction?: "switch-to-advanced";
};

const tourSteps: readonly TourStep[] = [
  { path: "/dashboard", selector: "[data-tour='dashboard-metrics']", eyebrow: "Overview", title: "See the big picture", body: "These cards summarize the latest discovery run.", preferredSide: "bottom", details: [
    { label: "Keywords", text: "How many search phrases were collected." },
    { label: "Volume", text: "The combined monthly search activity in this dataset." },
    { label: "Start here", text: "Use these numbers for orientation, then open Discover for the individual searches." },
  ] },
  { path: "/dashboard", selector: "[data-tour='data-sources']", eyebrow: "Data sources", title: "Know where the numbers come from", body: "Every result starts with one of these data sources.", preferredSide: "top", details: [
    { label: "Demo", text: "Safe sample data for learning the product." },
    { label: "CSV", text: "Search data uploaded from your own file." },
    { label: "Google Ads", text: "Live keyword data after an account is connected. Ready means the source can be used now." },
  ] },
  { path: "/discover", selector: "[data-tour='discovery-form']", eyebrow: "Step 1 · Start a search", title: "Enter a few starting words", body: "A seed is a short phrase that describes the market you want to explore.", preferredSide: "bottom", details: [
    { label: "Seeds", text: "Enter phrases in one line, separated by commas—for example “invoice software, team scheduling”." },
    { label: "Market", text: "Geo and language decide whose searches are included." },
    { label: "Run", text: "Choose a data source and press Run Discovery to build the dataset." },
  ] },
  { path: "/discover", selector: "[data-tour='discovery-results']", eyebrow: "Step 2 · Review results", title: "Find useful searches", body: "Each row is one phrase people search for.", preferredSide: "bottom", details: [
    { label: "Volume", text: "Estimated searches in an average month. Higher means more demand." },
    { label: "Growth", text: "How interest changed over time. Positive means it is rising." },
    { label: "Competition", text: "How strongly advertisers compete for that search. Use filters to narrow the list." },
  ] },
  { path: "/discover", selector: "[data-tour='keyword-clusters']", eyebrow: "Step 3 · See groups", title: "Understand shared intent", body: "A cluster collects searches that appear to describe the same user problem.", preferredSide: "top", details: [
    { label: "Group", text: "The title is a short summary of the shared problem." },
    { label: "Metrics", text: "Compare demand, growth, competition, and bid values between groups." },
    { label: "Validate", text: "Open the example searches and check that they really belong to one product need." },
  ] },
  { path: "/opportunities", selector: "[data-tour='opportunity-board']", eyebrow: "Step 4 · Choose an idea", title: "Compare possible opportunities", body: "An opportunity combines several demand and feasibility signals into one candidate.", preferredSide: "bottom", details: [
    { label: "Overall score", text: "A higher number means the idea looks stronger across all included signals." },
    { label: "Smaller scores", text: "They explain the result: demand, growth, commercial value, competition, intent, and buildability." },
    { label: "Next step", text: "Treat the score as a shortlist, then validate the customer problem before building." },
  ] },
  { path: "/opportunities", selector: "[data-tour='advanced-workspace']", eyebrow: "Workspace level", title: "Unlock advanced research tools", body: "The guided workspace keeps the daily workflow focused. Switch to advanced when you want deeper diagnostics and repeatable market tracking.", preferredSide: "right", primaryAction: "switch-to-advanced", details: [
    { label: "Distribution Lab", text: "Inspect the statistical shape behind demand, growth, competition, and bid metrics." },
    { label: "Monitoring", text: "Repeat the same market discovery on a schedule and compare snapshots over time." },
    { label: "Reversible", text: "This changes the workspace navigation, not your data. You can switch back from your profile." },
  ] },
  { path: "/distributions", selector: "[data-tour='distribution-metric']", eyebrow: "Distribution Lab · Choose", title: "Choose one metric to inspect", body: "Distribution Lab shows how one number varies across all keywords in the latest run.", preferredSide: "bottom", details: [
    { label: "Example", text: "Choose Average monthly searches to compare keyword demand." },
    { label: "Both graphs", text: "The histogram and Q–Q plot update together for the selected metric." },
    { label: "Why", text: "The shape helps you spot typical values, uneven data, and unusually large or small observations." },
  ] },
  { path: "/distributions", selector: "[data-tour='histogram']", eyebrow: "Distribution Lab · Empirical shape", title: "Read the histogram axes", body: "Empirical simply means the values actually observed in your dataset.", coachWidth: 560, preferredSide: "right", details: [
    { label: "Horizontal axis", text: "Values of the selected metric, from lower on the left to higher on the right. For search volume, these are monthly searches." },
    { label: "Vertical axis", text: "The number of keywords inside each value range. It is a keyword count, not search volume." },
    { label: "Bars", text: "Each bar is one range. A taller bar means more keywords have values in that range." },
    { label: "Reference line", text: "A bell-shaped comparison fitted to the same data. A large mismatch means the values are uneven or skewed." },
  ] },
  { path: "/distributions", selector: "[data-tour='qq-plot']", eyebrow: "Distribution Lab · Q–Q plot", title: "Understand what each axis means", body: "This chart checks whether the selected metric has a balanced bell-shaped pattern.", coachWidth: 640, preferredSide: "left", details: [
    { label: "Horizontal axis", text: "Expected positions in a perfect bell-shaped pattern. Negative values are the low end, 0 is the middle, and positive values are the high end. These are positions, not your metric." },
    { label: "Vertical axis", text: "The real observed values of the selected metric. For search volume, this is the actual monthly-search value." },
    { label: "Dots", text: "Each dot pairs an expected position with one real value from your data." },
    { label: "Reference line", text: "Dots near the line fit the simple pattern. A curve, wide gaps, or distant dots point to skew or unusual values." },
  ] },
  { path: "/distributions", selector: "[data-tour='diagnostics']", eyebrow: "Distribution Lab · Summary", title: "Turn the graphs into a conclusion", body: "These numbers summarize the same selected metric.", preferredSide: "top", details: [
    { label: "Mean and median", text: "Mean is the average; median is the middle. A large gap often means a few extreme values are pulling the average." },
    { label: "Spread", text: "Std and MAD describe how far values sit from the center. Larger values mean more variation." },
    { label: "Shape and sample", text: "Skewness and kurtosis describe shape; sample size is the number of keywords checked. Read the message below for the plain-language takeaway." },
  ] },
  { path: "/monitoring", selector: "[data-tour='monitoring']", eyebrow: "Monitoring · Continuous intelligence", title: "Watch the same market over time", body: "A monitor saves one market definition and builds a comparable history of discovery runs, so meaningful changes become visible.", preferredSide: "bottom", details: [
    { label: "Define once", text: "Choose the seed queries, market, language, provider, and refresh frequency." },
    { label: "Run repeatedly", text: "Scheduled workers collect fresh search observations without changing the monitor definition." },
    { label: "Read signals", text: "Compare snapshots to spot changes in demand, competition, and search intent." },
  ] },
];

function getCoachStyle(target: TourRect, side: TourSide, preferredWidth = 680, measuredHeight = 420): CSSProperties | undefined {
  if (typeof window === "undefined") return undefined;
  const margin = 16;
  const gap = 14;
  const safeTop = window.innerWidth > 800 ? 80 : 16;
  const sidebarWidth = window.innerWidth > 800 ? 236 : 0;
  const availableWidth = window.innerWidth - sidebarWidth - margin * 2;
  const width = Math.min(preferredWidth, availableWidth);
  const clamp = (value: number, minimum: number, maximum: number) => Math.min(Math.max(value, minimum), Math.max(minimum, maximum));
  const centeredLeft = clamp(target.left + target.width / 2 - width / 2, sidebarWidth + margin, window.innerWidth - width - margin);
  const centeredTop = clamp(target.top + target.height / 2 - measuredHeight / 2, safeTop, window.innerHeight - measuredHeight - margin);
  const positions: Record<TourSide, { left: number; top: number }> = {
    top: { left: centeredLeft, top: target.top - measuredHeight - gap },
    right: { left: target.left + target.width + gap, top: centeredTop },
    bottom: { left: centeredLeft, top: target.top + target.height + gap },
    left: { left: target.left - width - gap, top: centeredTop },
  };
  const position = positions[side];
  return {
    left: clamp(position.left, sidebarWidth + margin, window.innerWidth - width - margin),
    top: clamp(position.top, safeTop, window.innerHeight - measuredHeight - margin),
    width,
    right: "auto",
    bottom: "auto",
  };
}

export function lockTourScroll() {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  root.classList.add("tour-scroll-lock");
  root.style.scrollBehavior = "auto";
}

export function restoreTourScroll() {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  root.classList.remove("tour-scroll-lock");
  root.style.scrollBehavior = "";
}

const legalContent: Record<LegalDocument, { title: string; updated: string; sections: Array<{ title: string; body: string }> }> = {
  terms: {
    title: "Terms and Conditions", updated: "Effective 15 August 2026", sections: [
      { title: "1. Agreement", body: "By accessing MySEO, you agree to these Terms. If you use the service for an organization, you confirm that you are authorized to accept them on its behalf." },
      { title: "2. The service", body: "MySEO provides search-demand research, statistical diagnostics, and opportunity-ranking tools. Features may change as the product evolves. We may suspend access where necessary to protect the service, its users, or comply with law." },
      { title: "3. Your account and data", body: "You are responsible for your account activity, the accuracy and legality of submitted data, and keeping credentials secure. Do not upload personal data or confidential information unless you have the right and a valid reason to process it." },
      { title: "4. Acceptable use", body: "You may not misuse the service, interfere with its operation, reverse engineer protected portions, bypass access controls, introduce malicious code, or use outputs to violate applicable law or third-party rights." },
      { title: "5. Third-party data", body: "Some results may derive from providers such as Google Ads or user-supplied CSV files. Your use remains subject to the relevant provider terms. You may not use MySEO to obtain indirect or unauthorized access to a provider API." },
      { title: "6. Analytical outputs", body: "Scores, forecasts, clusters, and recommendations are decision-support signals, not guarantees of traffic, revenue, product-market fit, or investment performance. You remain responsible for validation and business decisions." },
      { title: "7. Intellectual property", body: "We retain rights in the service, interface, and analytics methods. You retain rights in data you submit. You grant us only the limited rights needed to operate, secure, and improve the service." },
      { title: "8. Availability and liability", body: "The service is provided on an as-available basis. To the extent permitted by law, we are not liable for indirect or consequential losses, loss of profit, or decisions made solely from analytical outputs." },
      { title: "9. Changes and contact", body: "Material changes will be reflected by an updated effective date and, where appropriate, an in-product notice. Questions may be sent through the official support contact published by the service operator." },
    ],
  },
  privacy: {
    title: "Privacy Notice", updated: "Effective 15 August 2026", sections: [
      { title: "What we process", body: "We may process account details, product interactions, search seeds, uploaded research datasets, provider identifiers, and technical security logs. Provider credentials are not returned to the browser and should never be placed in uploaded files." },
      { title: "Why we process it", body: "We process data to provide analytics, secure and maintain the service, respond to support requests, comply with legal duties, and—with consent where required—understand product usage." },
      { title: "Sharing and providers", body: "Data is shared only with infrastructure and data providers needed to deliver the service, under appropriate contractual controls, or where law requires it. We do not sell personal information." },
      { title: "Retention and security", body: "We retain data only as long as needed for the stated purposes, contractual obligations, and legal requirements. We apply access controls, encryption in transit, and operational safeguards appropriate to the risk." },
      { title: "Your choices", body: "Depending on your location, you may request access, correction, deletion, restriction, portability, or object to certain processing. You can also change optional cookie preferences at any time." },
      { title: "Contact", body: "Privacy requests may be submitted through the official privacy or support contact published by the service operator. The final deployed notice must identify the legal operator and applicable jurisdiction before public launch." },
    ],
  },
  cookies: {
    title: "Cookie Policy", updated: "Effective 15 August 2026", sections: [
      { title: "How cookies are used", body: "MySEO uses browser storage required to remember privacy choices, onboarding progress, and essential session state. These items keep the experience consistent and cannot be disabled through this panel." },
      { title: "Optional measurement", body: "With your permission, optional analytics may be used to understand feature adoption and improve usability. The current application does not activate optional analytics until a compatible analytics provider is configured and consent has been granted." },
      { title: "Your control", body: "Choose Accept all to allow optional measurement, or Necessary only to keep it disabled. You can revisit this choice from Cookie settings in the navigation footer." },
    ],
  },
};

function LegalModal({ kind, onClose }: { kind: LegalDocument; onClose: () => void }) {
  const content = legalContent[kind];
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", closeOnEscape);
    return () => { document.body.style.overflow = ""; window.removeEventListener("keydown", closeOnEscape); };
  }, [onClose]);
  return <div className="experience-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section aria-labelledby="legal-title" aria-modal="true" className="legal-modal" role="dialog">
      <header className="legal-header"><div><p className="eyebrow">MySEO legal</p><h2 id="legal-title">{content.title}</h2><span>{content.updated}</span></div><button aria-label={`Close ${content.title}`} className="icon-button" onClick={onClose} ref={closeRef} type="button"><X size={19} /></button></header>
      <div className="legal-scroll"><div className="legal-summary"><ShieldCheck size={20} /><p>Clear terms for responsible, evidence-led research.</p></div>{content.sections.map((section) => <section className="legal-section" key={section.title}><h3>{section.title}</h3><p>{section.body}</p></section>)}</div>
      <footer className="legal-footer"><span>Version 1.0</span><button className="primary-button" onClick={onClose} type="button">Done</button></footer>
    </section>
  </div>;
}

export function ProductExperience() {
  const pathname = usePathname();
  const router = useRouter();
  const [consent, setConsent] = useState<ConsentChoice | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [legal, setLegal] = useState<LegalDocument | null>(null);
  const [tourIndex, setTourIndex] = useState<number | null>(null);
  const [tourTarget, setTourTarget] = useState<{ index: number; rect: TourRect | null; side: TourSide } | null>(null);
  const [tourTransitioning, setTourTransitioning] = useState(false);
  const returnToDashboardTopRef = useRef(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setConsent(localStorage.getItem(CONSENT_KEY) as ConsentChoice | null);
      setHydrated(true);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);
  useEffect(() => {
    const handlers = {
      tour: () => { setTourTarget(null); setTourTransitioning(true); setTourIndex(0); }, terms: () => setLegal("terms" as const), privacy: () => setLegal("privacy" as const), cookies: () => setShowPreferences(true),
    };
    window.addEventListener("myseo:tour", handlers.tour); window.addEventListener("myseo:terms", handlers.terms); window.addEventListener("myseo:privacy", handlers.privacy); window.addEventListener("myseo:cookies", handlers.cookies);
    return () => { window.removeEventListener("myseo:tour", handlers.tour); window.removeEventListener("myseo:terms", handlers.terms); window.removeEventListener("myseo:privacy", handlers.privacy); window.removeEventListener("myseo:cookies", handlers.cookies); };
  }, []);

  const step = tourIndex === null ? null : tourSteps[tourIndex];
  const tourActive = step !== null;
  const displayedIndex = tourTarget?.index ?? tourIndex;
  const displayedStep = displayedIndex === null ? null : tourSteps[displayedIndex];
  const displayedTargetRect = tourTarget?.rect ?? null;

  useEffect(() => {
    if (tourIndex === null) return;
    const nextStep = tourSteps[tourIndex + 1];
    if (nextStep && nextStep.path !== pathname) router.prefetch(nextStep.path);
  }, [pathname, router, tourIndex]);

  useLayoutEffect(() => {
    if (!returnToDashboardTopRef.current || pathname !== "/dashboard") return;
    returnToDashboardTopRef.current = false;
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [pathname]);

  useLayoutEffect(() => {
    if (!tourActive) return;

    lockTourScroll();

    const stopScroll = (event: Event) => event.preventDefault();
    const stopScrollKeys = (event: KeyboardEvent) => {
      const activeElement = document.activeElement;
      const isInteractive = activeElement instanceof HTMLButtonElement || activeElement instanceof HTMLInputElement || activeElement instanceof HTMLTextAreaElement || activeElement instanceof HTMLSelectElement;
      if (["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End"].includes(event.key) || (event.key === " " && !isInteractive)) event.preventDefault();
    };
    window.addEventListener("wheel", stopScroll, { passive: false });
    window.addEventListener("touchmove", stopScroll, { passive: false });
    window.addEventListener("keydown", stopScrollKeys);
    return () => {
      restoreTourScroll();
      window.removeEventListener("wheel", stopScroll);
      window.removeEventListener("touchmove", stopScroll);
      window.removeEventListener("keydown", stopScrollKeys);
    };
  }, [tourActive]);

  useLayoutEffect(() => {
    if (!step) return;
    if (pathname !== step.path) { router.push(step.path, { scroll: false }); return; }
    let cancelled = false;
    let scrollFrame = 0;
    let targetResizeObserver: ResizeObserver | null = null;
    const preferredCoachWidth = step.coachWidth ?? 680;
    const measuredCoachHeight = preferredCoachWidth > 420
      ? step.details.length > 3 ? 510 : 410
      : 460;
    const sidebarWidth = window.innerWidth > 800 ? 236 : 0;
    const measuredCoachWidth = Math.min(preferredCoachWidth, window.innerWidth - sidebarWidth - 32);
    const horizontalSide = step.preferredSide === "left" || step.preferredSide === "right";
    let side: TourSide = horizontalSide && window.innerWidth < 1000
      ? step.preferredSide === "left" ? "top" : "bottom"
      : step.preferredSide;
    const gap = 14;
    const margin = 16;
    const safeTop = window.innerWidth > 800 ? 80 : margin;

    const calculateRect = (element: Element): TourRect => {
      const rect = element.getBoundingClientRect();
      let left = Math.max(margin, rect.left);
      let top = Math.max(safeTop, rect.top);
      let right = Math.min(window.innerWidth - margin, rect.right);
      let bottom = Math.min(window.innerHeight - margin, rect.bottom);
      if (side === "top") top = Math.max(top, measuredCoachHeight + gap + safeTop);
      if (side === "bottom") bottom = Math.min(bottom, window.innerHeight - measuredCoachHeight - gap - margin);
      if (side === "left") left = Math.max(left, sidebarWidth + measuredCoachWidth + gap + margin);
      if (side === "right") right = Math.min(right, window.innerWidth - measuredCoachWidth - gap - margin);
      return { left, top, width: Math.max(0, right - left), height: Math.max(0, bottom - top) };
    };

    const measure = (element: Element) => {
      if (cancelled) return;
      const rect = calculateRect(element);
      setTourTarget({ index: tourIndex!, side, rect });
    };

    const reveal = (element: Element) => {
      if (cancelled) return;
      measure(element);
      setTourTransitioning(false);
    };

    const locate = () => {
      const element = document.querySelector(step.selector);
      if (!element) return false;
      if (!targetResizeObserver) {
        targetResizeObserver = new ResizeObserver(() => measure(element));
        targetResizeObserver.observe(element);
      }

      const initialRect = element.getBoundingClientRect();
      if (step.preferredSide === "right") {
        const rightSpace = window.innerWidth - initialRect.right - gap - margin;
        const leftSpace = initialRect.left - sidebarWidth - gap - margin;
        side = rightSpace >= measuredCoachWidth ? "right" : leftSpace >= measuredCoachWidth ? "left" : "bottom";
      } else if (step.preferredSide === "left") {
        const leftSpace = initialRect.left - sidebarWidth - gap - margin;
        const rightSpace = window.innerWidth - initialRect.right - gap - margin;
        side = leftSpace >= measuredCoachWidth ? "left" : rightSpace >= measuredCoachWidth ? "right" : "top";
      }
      const desiredViewportTop = side === "top"
        ? measuredCoachHeight + gap + safeTop
        : side === "bottom"
          ? safeTop
          : safeTop + Math.max(0, (window.innerHeight - safeTop - margin - Math.min(initialRect.height, window.innerHeight - safeTop - margin)) / 2);
      const targetTop = window.scrollY + initialRect.top - desiredViewportTop;
      const destination = Math.max(0, targetTop);
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const shouldAnimate = !reduceMotion && Math.abs(window.scrollY - destination) > 1;
      window.cancelAnimationFrame(scrollFrame);
      window.scrollTo({ top: destination, behavior: shouldAnimate ? "smooth" : "auto" });

      if (!shouldAnimate) {
        scrollFrame = window.requestAnimationFrame(() => reveal(element));
        return true;
      }

      const startedAt = performance.now();
      let lastScrollY = window.scrollY;
      let stableFrames = 0;
      const waitForScrollEnd = () => {
        if (cancelled) return;
        const currentScrollY = window.scrollY;
        stableFrames = Math.abs(currentScrollY - lastScrollY) < 0.5 ? stableFrames + 1 : 0;
        lastScrollY = currentScrollY;
        const elapsed = performance.now() - startedAt;
        if (elapsed < 1000 && (elapsed < 120 || stableFrames < 4)) {
          scrollFrame = window.requestAnimationFrame(waitForScrollEnd);
          return;
        }
        reveal(element);
      };
      scrollFrame = window.requestAnimationFrame(waitForScrollEnd);
      return true;
    };

    locate();
    const observer = new MutationObserver(() => {
      if (locate()) observer.disconnect();
    });
    if (!document.querySelector(step.selector)) observer.observe(document.body, { childList: true, subtree: true });
    const updateOnResize = () => {
      const element = document.querySelector(step.selector);
      if (element) measure(element);
    };
    window.addEventListener("resize", updateOnResize);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(scrollFrame);
      targetResizeObserver?.disconnect();
      observer.disconnect();
      window.removeEventListener("resize", updateOnResize);
    };
  }, [pathname, router, step, tourIndex]);

  function saveConsent(choice: ConsentChoice) {
    localStorage.setItem(CONSENT_KEY, choice); setConsent(choice); setShowPreferences(false);
    window.dispatchEvent(new CustomEvent("myseo:consent", { detail: choice }));
  }
  function closeTour(completed = false) {
    if (completed) localStorage.setItem(TOUR_KEY, "completed");
    restoreTourScroll();
    setTourIndex(null);
    setTourTarget(null);
    setTourTransitioning(false);
  }
  function showTourStep(index: number) {
    setTourTransitioning(true);
    setTourIndex(index);
  }
  function advanceTour() {
    if (displayedIndex === null || !displayedStep) return;
    if (displayedStep.primaryAction === "switch-to-advanced") {
      cacheExperienceLevel("advanced");
      void updateCurrentUser({ experienceLevel: "advanced" }).catch(() => undefined);
    }
    if (displayedIndex === tourSteps.length - 1) finishTour();
    else showTourStep(displayedIndex + 1);
  }
  function finishTour() {
    returnToDashboardTopRef.current = true;
    closeTour(true);
    if (pathname === "/dashboard") {
      returnToDashboardTopRef.current = false;
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      return;
    }
    router.push("/dashboard", { scroll: false });
  }
  const tourLayerClass = !tourTransitioning && displayedTargetRect ? "tour-layer" : "tour-layer pending";
  const preferredCoachWidth = displayedStep?.coachWidth ?? 680;
  const stableCoachHeight = displayedStep && preferredCoachWidth > 420
    ? displayedStep.details.length > 3 ? 510 : 410
    : 460;
  const coachStyle = displayedTargetRect && tourTarget
    ? getCoachStyle(displayedTargetRect, tourTarget.side, preferredCoachWidth, stableCoachHeight)
    : undefined;

  return <>
    {hydrated && consent === null && <aside aria-label="Cookie consent" className="cookie-banner"><div className="cookie-icon"><Cookie size={21} /></div><div className="cookie-copy"><strong>Your research. Your choice.</strong><p>We use essential storage to keep MySEO working. Optional analytics only run with your permission.</p><button onClick={() => setLegal("cookies")} type="button">Read Cookie Policy <ExternalLink size={12} /></button></div><div className="cookie-actions"><button className="primary-button" onClick={() => saveConsent("all")} type="button">Accept all</button><button className="secondary-button" onClick={() => saveConsent("necessary")} type="button">Necessary only</button></div></aside>}
    {showPreferences && <div className="experience-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setShowPreferences(false)}><section aria-labelledby="cookie-preference-title" aria-modal="true" className="preference-modal" role="dialog"><div className="preference-title"><span className="cookie-icon"><Cookie size={20} /></span><div><p className="eyebrow">Privacy controls</p><h2 id="cookie-preference-title">Cookie preferences</h2></div><button aria-label="Close cookie preferences" className="icon-button" onClick={() => setShowPreferences(false)} type="button"><X size={18} /></button></div><div className="preference-row"><div><strong>Essential</strong><p>Consent, onboarding, security, and session continuity.</p></div><span className="always-on"><Check size={12} /> Always on</span></div><div className="preference-row"><div><strong>Optional analytics</strong><p>Helps us understand product usage. No advertising cookies.</p></div><span className={consent === "all" ? "consent-state enabled" : "consent-state"}>{consent === "all" ? "Allowed" : "Off"}</span></div><div className="preference-actions"><button className="secondary-button" onClick={() => saveConsent("necessary")} type="button">Use necessary only</button><button className="primary-button" onClick={() => saveConsent("all")} type="button">Allow analytics</button></div></section></div>}
    {legal && <LegalModal kind={legal} onClose={() => setLegal(null)} />}
    {displayedStep && displayedIndex !== null && <div aria-busy={tourTransitioning} className={tourLayerClass} aria-live="polite">{!tourTransitioning && displayedTargetRect && <><div className="tour-spotlight" style={{ left: displayedTargetRect.left, top: displayedTargetRect.top, width: displayedTargetRect.width, height: displayedTargetRect.height }} /><section aria-label={`Product tour step ${displayedIndex + 1} of ${tourSteps.length}`} className={`tour-coach${preferredCoachWidth > 420 ? " wide" : ""}${displayedStep.details.length > 3 ? " four-details" : ""}`} style={coachStyle}><div className="tour-coach-content"><div className="tour-progress"><span>{String(displayedIndex + 1).padStart(2, "0")} / {tourSteps.length}</span><i><b style={{ width: `${((displayedIndex + 1) / tourSteps.length) * 100}%` }} /></i><button aria-label="Close tour" onClick={() => closeTour()} type="button"><X size={16} /></button></div><p className="eyebrow">{displayedStep.eyebrow}</p><h2>{displayedStep.title}</h2><p>{displayedStep.body}</p><dl className="tour-details">{displayedStep.details.map((detail) => <div key={detail.label}><dt>{detail.label}</dt><dd>{detail.text}</dd></div>)}</dl><footer><button className="tour-skip" onClick={() => closeTour()} type="button">Exit guide</button><div>{displayedIndex > 0 && <button aria-label="Previous step" className="icon-button" onClick={() => showTourStep(displayedIndex - 1)} type="button"><ChevronLeft size={18} /></button>}<button className="primary-button" onClick={advanceTour} type="button">{displayedStep.primaryAction === "switch-to-advanced" ? "See advanced features" : displayedIndex === tourSteps.length - 1 ? "Finish" : "Next"}<ChevronRight size={15} /></button></div></footer></div></section></>}</div>}
  </>;
}
