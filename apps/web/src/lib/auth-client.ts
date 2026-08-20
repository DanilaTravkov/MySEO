import { cacheExperienceLevel, type ExperienceLevel } from "@/lib/experience-level";

export const authEvent = "myseo:auth";
const authSyncKey = "myseo-auth-sync";

function notifyAuthChange() {
  localStorage.setItem(authSyncKey, String(Date.now()));
  window.dispatchEvent(new Event(authEvent));
}

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  company: string;
  role: string;
  createdAt: string;
  experienceLevel: ExperienceLevel;
};

type ApiUser = {
  id: string;
  full_name: string;
  email: string;
  company: string;
  role: string;
  created_at: string;
  experience_level: ExperienceLevel;
};

function normalizeUser(user: ApiUser): AuthUser {
  return {
    id: user.id,
    name: user.full_name,
    email: user.email,
    company: user.company,
    role: user.role,
    createdAt: user.created_at,
    experienceLevel: user.experience_level === "advanced" ? "advanced" : "guided",
  };
}

async function responseError(response: Response) {
  try {
    const payload = await response.json() as { detail?: string };
    return payload.detail ?? "The request could not be completed.";
  } catch {
    return "Authentication is temporarily unavailable. Please try again.";
  }
}

async function userResponse(response: Response): Promise<AuthUser> {
  if (!response.ok) throw new Error(await responseError(response));
  const payload = await response.json() as { user: ApiUser };
  const user = normalizeUser(payload.user);
  cacheExperienceLevel(user.experienceLevel);
  return user;
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  localStorage.removeItem("myseo-mock-user");
  const response = await fetch("/api/auth/me", { cache: "no-store" });
  if (response.status === 401) return null;
  return userResponse(response);
}

export async function registerUser(input: {
  name: string;
  email: string;
  password: string;
  company: string;
}) {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      full_name: input.name,
      email: input.email,
      password: input.password,
      company: input.company,
    }),
  });
  const user = await userResponse(response);
  notifyAuthChange();
  return user;
}

export async function loginUser(input: { email: string; password: string; remember: boolean }) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const user = await userResponse(response);
  notifyAuthChange();
  return user;
}

export async function updateCurrentUser(input: Partial<{
  name: string;
  email: string;
  company: string;
  role: string;
  experienceLevel: ExperienceLevel;
}>) {
  const response = await fetch("/api/auth/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...(input.name !== undefined ? { full_name: input.name } : {}),
      ...(input.email !== undefined ? { email: input.email } : {}),
      ...(input.company !== undefined ? { company: input.company } : {}),
      ...(input.role !== undefined ? { role: input.role } : {}),
      ...(input.experienceLevel !== undefined ? { experience_level: input.experienceLevel } : {}),
    }),
  });
  const user = await userResponse(response);
  notifyAuthChange();
  return user;
}

export async function logoutUser() {
  await fetch("/api/auth/logout", { method: "POST" });
  cacheExperienceLevel("guided");
  notifyAuthChange();
}
