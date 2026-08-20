"use client";

import { ArrowRight, BookOpen, Building2, Check, Code2, LogOut, Mail, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { ProfileSkeleton } from "@/components/loading-skeletons";
import { fetchCurrentUser, logoutUser, updateCurrentUser, type AuthUser } from "@/lib/auth-client";
import type { ExperienceLevel } from "@/lib/experience-level";

export function ProfileWorkspace() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>("guided");

  useEffect(() => {
    let active = true;
    void fetchCurrentUser()
      .then((currentUser) => {
        if (!active) return;
        setUser(currentUser);
        if (currentUser) setExperienceLevel(currentUser.experienceLevel);
      })
      .catch(() => { if (active) setError("Unable to load your profile."); })
      .finally(() => { if (active) setHydrated(true); });
    return () => { active = false; };
  }, []);

  function update(field: keyof Pick<AuthUser, "name" | "email" | "company" | "role">, value: string) {
    setSaved(false);
    setError("");
    setUser((current) => current ? { ...current, [field]: value } : current);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;
    setError("");
    try {
      const updatedUser = await updateCurrentUser({
        name: user.name,
        email: user.email,
        company: user.company,
        role: user.role,
      });
      setUser(updatedUser);
      setSaved(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save changes.");
    }
  }

  async function signOut() {
    await logoutUser();
    router.push("/login");
    router.refresh();
  }

  async function changeExperienceLevel(level: ExperienceLevel) {
    const previousLevel = experienceLevel;
    setExperienceLevel(level);
    setUser((current) => current ? { ...current, experienceLevel: level } : current);
    setError("");
    try {
      const updatedUser = await updateCurrentUser({ experienceLevel: level });
      setUser(updatedUser);
    } catch (submitError) {
      setExperienceLevel(previousLevel);
      setUser((current) => current ? { ...current, experienceLevel: previousLevel } : current);
      setError(submitError instanceof Error ? submitError.message : "Unable to change workspace level.");
    }
  }

  if (!hydrated) return <ProfileSkeleton />;

  if (!user) return (
    <section className="profile-signed-out panel">
      <span><UserRound size={24} /></span>
      <div><p className="eyebrow">Your account</p><h2>Sign in to manage your profile.</h2><p>Keep your personal and workspace information in one place.</p></div>
      <div><Link className="secondary-button" href="/register">Create account</Link><Link className="primary-button" href="/login">Sign in <ArrowRight size={15} /></Link></div>
    </section>
  );

  const joinedAt = new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" }).format(new Date(user.createdAt));
  const profileInitial = user.name.trim().charAt(0).toUpperCase() || "U";

  return (
    <div className="profile-workspace">
      <aside className="profile-summary panel">
        <div className="profile-avatar">{profileInitial}</div>
        <h2>{user.name}</h2>
        <p>{user.email}</p>
        <dl><div><dt>Workspace</dt><dd>{user.company || "Personal"}</dd></div><div><dt>Experience</dt><dd>{experienceLevel === "advanced" ? "Advanced" : "Guided"}</dd></div><div><dt>Member since</dt><dd>{joinedAt}</dd></div></dl>
        <button className="profile-sign-out" onClick={signOut} type="button"><LogOut size={15} /> Sign out</button>
      </aside>

      <form className="profile-form panel" onSubmit={submit}>
        <div className="panel-heading"><div><p className="eyebrow">Account details</p><h2>Personal information</h2></div>{saved ? <span aria-live="polite" className="profile-saved"><Check size={13} /> Saved</span> : null}</div>
        <p className="profile-form-intro">Keep your contact and workspace details up to date.</p>
        <div className="profile-fields">
          <label><span><UserRound size={15} /> Full name</span><input autoComplete="name" onChange={(event) => update("name", event.target.value)} required value={user.name} /></label>
          <label><span><Mail size={15} /> Personal email</span><input autoComplete="email" onChange={(event) => update("email", event.target.value)} required type="email" value={user.email} /></label>
          <label><span><Building2 size={15} /> Company</span><input autoComplete="organization" onChange={(event) => update("company", event.target.value)} placeholder="Add your company" value={user.company} /></label>
          <label><span><UserRound size={15} /> Role</span><input autoComplete="organization-title" onChange={(event) => update("role", event.target.value)} placeholder="e.g. Product manager" value={user.role} /></label>
        </div>
        {error ? <p aria-live="polite" className="auth-error">{error}</p> : null}
        <footer><button className="primary-button" type="submit">Save changes</button></footer>
      </form>

      <section className="profile-experience panel" id="experience">
        <div className="panel-heading"><div><p className="eyebrow">Product experience</p><h2>Choose your workspace level</h2></div></div>
        <p className="profile-form-intro">This changes which tools and explanations are shown. You can switch back at any time.</p>
        <div className="experience-options" role="group" aria-label="Product experience level">
          <button aria-pressed={experienceLevel === "guided"} className={experienceLevel === "guided" ? "active" : ""} onClick={() => changeExperienceLevel("guided")} type="button"><span><BookOpen size={18} /></span><div><strong>Guided workspace</strong><p>Core research workflow with product guidance and contextual explanations.</p></div><i>{experienceLevel === "guided" ? <Check size={15} /> : null}</i></button>
          <button aria-pressed={experienceLevel === "advanced"} className={experienceLevel === "advanced" ? "active" : ""} onClick={() => changeExperienceLevel("advanced")} type="button"><span><Code2 size={18} /></span><div><strong>Advanced workspace</strong><p>Adds cloud functions and prepares the workspace for API-driven workflows.</p></div><i>{experienceLevel === "advanced" ? <Check size={15} /> : null}</i></button>
        </div>
      </section>
    </div>
  );
}
