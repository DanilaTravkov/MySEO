import { NextResponse } from "next/server";

import { authApiRequest, authError, sessionCookieName, sessionCookieOptions } from "@/lib/server-auth";

type AuthPayload = { access_token: string; expires_at: string; user: unknown };

export async function POST(request: Request) {
  const body = await request.text();
  const remember = Boolean((JSON.parse(body) as { remember?: boolean }).remember);
  const response = await authApiRequest("login", { method: "POST", body });
  if (!response.ok) return NextResponse.json({ detail: await authError(response) }, { status: response.status });

  const payload = await response.json() as AuthPayload;
  const result = NextResponse.json({ user: payload.user });
  result.cookies.set(
    sessionCookieName,
    payload.access_token,
    sessionCookieOptions(remember ? payload.expires_at : undefined),
  );
  return result;
}
