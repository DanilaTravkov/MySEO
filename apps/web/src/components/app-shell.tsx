"use client";

import { ArrowUpRight, Code2, HelpCircle, Moon, Plus, Sun, UserRound, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { BrandMark } from "@/components/brand-mark";
import { authEvent, fetchCurrentUser, type AuthUser } from "@/lib/auth-client";
import { experienceLevelEvent, readExperienceLevel, type ExperienceLevel } from "@/lib/experience-level";
import { navigationItems } from "@/lib/navigation";

const guidePromptKey = "myseo-guide-prompt-dismissed";
const productTourKey = "myseo-product-tour";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [showGuidePrompt, setShowGuidePrompt] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>("guided");
  const [experienceHydrated, setExperienceHydrated] = useState(false);
  const isAuthRoute = pathname === "/login" || pathname === "/register";
  const currentRoute = navigationItems.find(({ href }) =>
    pathname === href || (pathname.startsWith("/keywords/") && href === "/discover")
  );
  const profileInitial = authUser?.name.trim().charAt(0).toUpperCase() || "U";
  const coreNavigationItems = navigationItems.filter((item) => !item.level && item.href !== "/settings");
  const advancedNavigationItems = navigationItems.filter((item) => item.level === "advanced");
  const settingsItem = navigationItems.find((item) => item.href === "/settings");
  const SettingsIcon = settingsItem?.icon;

  useEffect(() => {
    if (readExperienceLevel() === "advanced" || localStorage.getItem(guidePromptKey) || localStorage.getItem(productTourKey)) return;
    const promptTimer = window.setTimeout(() => setShowGuidePrompt(true), 450);
    return () => window.clearTimeout(promptTimer);
  }, []);

  useEffect(() => {
    const syncExperienceLevel = () => {
      setExperienceLevel(readExperienceLevel());
      setExperienceHydrated(true);
    };
    const syncTimer = window.setTimeout(syncExperienceLevel, 0);
    window.addEventListener(experienceLevelEvent, syncExperienceLevel);
    window.addEventListener("storage", syncExperienceLevel);
    return () => {
      window.clearTimeout(syncTimer);
      window.removeEventListener(experienceLevelEvent, syncExperienceLevel);
      window.removeEventListener("storage", syncExperienceLevel);
    };
  }, []);

  useEffect(() => {
    let active = true;
    const syncUser = () => void fetchCurrentUser()
      .then((user) => { if (active) setAuthUser(user); })
      .catch(() => { if (active) setAuthUser(null); });
    const syncTimer = window.setTimeout(syncUser, 0);
    window.addEventListener(authEvent, syncUser);
    window.addEventListener("storage", syncUser);
    return () => {
      active = false;
      window.clearTimeout(syncTimer);
      window.removeEventListener(authEvent, syncUser);
      window.removeEventListener("storage", syncUser);
    };
  }, []);

  function dismissGuidePrompt() {
    localStorage.setItem(guidePromptKey, "true");
    setShowGuidePrompt(false);
  }

  function openGuide() {
    dismissGuidePrompt();
    window.dispatchEvent(new Event("myseo:tour"));
  }

  function toggleTheme() {
    const root = document.documentElement;
    const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = nextTheme;
    root.style.colorScheme = nextTheme;
    localStorage.setItem("myseo-theme", nextTheme);
  }

  if (isAuthRoute) return <>{children}</>;

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <div className="ambient-canvas" aria-hidden="true" />
      <aside className="sidebar">
        <Link className="brand" href="/dashboard" aria-label="MySEO home">
          <BrandMark className="brand-mark" />
          <span><strong>MySEO</strong><small>Search intelligence</small></span>
        </Link>

        <nav className="primary-nav" aria-label="Primary navigation">
          {coreNavigationItems.map(({ href, icon: Icon, label }) => (
            <Link className={currentRoute?.href === href ? "active" : ""} href={href} key={href}>
              <Icon size={18} />
              <span>{label}</span>
              <ArrowUpRight className="nav-arrow" size={14} />
            </Link>
          ))}
          <div className="experience-nav-slot" data-tour="advanced-workspace">
            {!experienceHydrated ? <span className="experience-nav-placeholder" /> : experienceLevel === "advanced" ? (
              <div className="advanced-nav-group">
                <p>Advanced workspace</p>
                {advancedNavigationItems.map(({ href, icon: Icon, label }) => (
                  <Link className={currentRoute?.href === href ? "active" : ""} href={href} key={href}>
                    <Icon size={18} />
                    <span>{label}</span>
                    <ArrowUpRight className="nav-arrow" size={14} />
                  </Link>
                ))}
              </div>
            ) : (
              <Link className="advanced-workspace-entry" href="/profile#experience">
                <Code2 size={18} />
                <span><strong>Advanced workspace</strong><small>Distribution lab and monitoring</small></span>
                <ArrowUpRight className="nav-arrow" size={14} />
              </Link>
            )}
          </div>
          {settingsItem && SettingsIcon ? <Link className={currentRoute?.href === settingsItem.href ? "active" : ""} href={settingsItem.href}><SettingsIcon size={18} /><span>{settingsItem.label}</span><ArrowUpRight className="nav-arrow" size={14} /></Link> : null}
        </nav>

        <div className="sidebar-legal" aria-label="Legal links">
          <button onClick={() => window.dispatchEvent(new Event("myseo:terms"))} type="button">Terms</button>
          <button onClick={() => window.dispatchEvent(new Event("myseo:privacy"))} type="button">Privacy</button>
          <button onClick={() => window.dispatchEvent(new Event("myseo:cookies"))} type="button">Cookies</button>
        </div>
        <p className="sidebar-foot">Evidence over intuition.</p>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="route-marker"><span>MySEO</span><strong>{pathname === "/profile" ? "Profile" : currentRoute?.label ?? "Keyword insight"}</strong></div>
          <div className="topbar-actions">
            <button aria-label="Switch color theme" className="theme-toggle" onClick={toggleTheme} title="Switch color theme" type="button"><Sun className="theme-sun" size={16} /><Moon className="theme-moon" size={16} /></button>
            <div className="topbar-guide-wrap">
              <button aria-describedby={showGuidePrompt ? "guide-prompt" : undefined} className="topbar-guide" onClick={openGuide} type="button"><HelpCircle size={15} /> How does everything work?</button>
              {showGuidePrompt ? <aside className="guide-prompt" id="guide-prompt" role="status"><span className="guide-prompt-icon"><HelpCircle size={16} /></span><div><strong>Start with the product guide</strong><p>It is worth taking the short tour before your first discovery. You will learn what each metric means and where to begin.</p></div><button aria-label="Dismiss guide recommendation" onClick={dismissGuidePrompt} type="button"><X size={15} /></button></aside> : null}
            </div>
            <Link className="topbar-action" href="/discover"><Plus size={15} /> New discovery</Link>
            {authUser ? <Link aria-label={`Open ${authUser.name}'s profile`} className="profile-control" href="/profile" title={authUser.name}>{profileInitial}</Link> : <Link className="topbar-sign-in" href="/login"><UserRound size={15} /> Sign in</Link>}
          </div>
        </header>
        <main className="main-content" id="main-content">{children}</main>
      </div>
    </div>
  );
}
