import "server-only";

export const sessionCookieName = "myseo_session";

export function authApiUrl(path: string) {
  const baseUrl = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  return `${baseUrl.replace(/\/$/, "")}/api/auth/${path}`;
}

export async function authApiRequest(
  path: string,
  init: RequestInit,
  token?: string,
) {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(authApiUrl(path), { ...init, headers, cache: "no-store" });
}

export async function authError(response: Response) {
  try {
    const payload = await response.json() as { detail?: string | Array<{ msg?: string }> };
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) return payload.detail[0]?.msg ?? "The request could not be completed.";
  } catch {
    // The API may be temporarily unavailable and return a non-JSON gateway response.
  }
  return response.status >= 500
    ? "Authentication is temporarily unavailable. Please try again."
    : "The request could not be completed.";
}

export function sessionCookieOptions(expires?: string) {
  return {
    httpOnly: true,
    secure: process.env.AUTH_COOKIE_SECURE === "true",
    sameSite: "lax" as const,
    path: "/",
    ...(expires ? { expires: new Date(expires) } : {}),
  };
}
