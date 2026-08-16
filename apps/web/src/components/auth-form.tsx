"use client";

import { ArrowRight, Eye, EyeOff, Moon, Sun } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { BrandMark } from "@/components/brand-mark";
import { nameFromEmail, readMockUser, saveMockUser } from "@/lib/mock-auth";

type AuthMode = "login" | "register";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const isRegister = mode === "register";

  function toggleTheme() {
    const root = document.documentElement;
    const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = nextTheme;
    root.style.colorScheme = nextTheme;
    localStorage.setItem("myseo-theme", nextTheme);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim().toLowerCase();
    const password = String(form.get("password") ?? "");

    if (password.length < 8) {
      setError("Use at least 8 characters for the mock password.");
      return;
    }

    if (isRegister) {
      const confirmation = String(form.get("passwordConfirmation") ?? "");
      if (password !== confirmation) {
        setError("The passwords do not match.");
        return;
      }
      saveMockUser({
        name: String(form.get("name") ?? "").trim(),
        email,
        company: String(form.get("company") ?? "").trim(),
        role: "",
        createdAt: new Date().toISOString(),
      });
    } else {
      const existingUser = readMockUser();
      saveMockUser(existingUser?.email === email ? existingUser : {
        name: nameFromEmail(email),
        email,
        company: "",
        role: "",
        createdAt: new Date().toISOString(),
      });
    }

    router.push("/dashboard");
  }

  return (
    <main className="auth-layout">
      <section className="auth-brand-panel">
        <Link className="auth-brand" href="/dashboard" aria-label="MySEO home"><BrandMark /><span><strong>MySEO</strong><small>Search intelligence</small></span></Link>
        <div className="auth-brand-copy">
          <p className="eyebrow">From searches to direction</p>
          <h1>See the market before you build.</h1>
          <p>Turn search behavior into clear evidence about demand, momentum, and customer intent.</p>
        </div>
        <div className="auth-signal" aria-hidden="true"><i /><i /><i /><span /></div>
        <p className="auth-brand-note">Demand intelligence for focused product teams.</p>
      </section>

      <section className="auth-stage">
        <button aria-label="Switch color theme" className="auth-theme-toggle" onClick={toggleTheme} type="button"><Sun className="theme-sun" size={17} /><Moon className="theme-moon" size={17} /></button>
        <div className="auth-card">
          <div className="auth-heading">
            <p className="eyebrow">{isRegister ? "Create your workspace" : "Welcome back"}</p>
            <h2>{isRegister ? "Start with MySEO" : "Sign in to MySEO"}</h2>
            <p>{isRegister ? "Create a mock profile and explore the complete research workflow." : "Continue to your demand intelligence workspace."}</p>
          </div>

          <form className="auth-form" onSubmit={submit}>
            {isRegister ? <div className="auth-field-row"><label>Full name<input autoComplete="name" name="name" placeholder="Alex Morgan" required /></label><label>Company <span>Optional</span><input autoComplete="organization" name="company" placeholder="Acme" /></label></div> : null}
            <label>Personal email<input autoComplete="email" name="email" placeholder="you@example.com" required type="email" /></label>
            <label>Password<div className="password-field"><input autoComplete={isRegister ? "new-password" : "current-password"} minLength={8} name="password" placeholder="At least 8 characters" required type={showPassword ? "text" : "password"} /><button aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((current) => !current)} type="button">{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
            {isRegister ? <label>Confirm password<input autoComplete="new-password" minLength={8} name="passwordConfirmation" placeholder="Repeat your password" required type={showPassword ? "text" : "password"} /></label> : <div className="auth-form-meta"><label><input name="remember" type="checkbox" /> Keep me signed in</label><button onClick={() => setError("Password recovery will be connected with real authentication.")} type="button">Forgot password?</button></div>}
            {isRegister ? <label className="auth-consent"><input required type="checkbox" /><span>I agree to the <button onClick={() => window.dispatchEvent(new Event("myseo:terms"))} type="button">Terms</button> and <button onClick={() => window.dispatchEvent(new Event("myseo:privacy"))} type="button">Privacy Policy</button>.</span></label> : null}
            {error ? <p aria-live="polite" className="auth-error">{error}</p> : null}
            <button className="auth-submit" type="submit">{isRegister ? "Create mock account" : "Sign in"}<ArrowRight size={17} /></button>
          </form>

          <p className="auth-switch">{isRegister ? "Already have a profile?" : "New to MySEO?"} <Link href={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create an account"}</Link></p>
        </div>
        <div className="auth-legal"><button onClick={() => window.dispatchEvent(new Event("myseo:terms"))} type="button">Terms</button><button onClick={() => window.dispatchEvent(new Event("myseo:privacy"))} type="button">Privacy</button><button onClick={() => window.dispatchEvent(new Event("myseo:cookies"))} type="button">Cookies</button></div>
      </section>
    </main>
  );
}
