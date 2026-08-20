import { NextResponse } from "next/server";

import { authApiRequest, authError, sessionCookieName, sessionCookieOptions } from "@/lib/server-auth";

type AuthPayload = { access_token: string; expires_at: string; user: unknown };

export async function POST(request: Request) {
  const body = await request.text();
  const response = await authApiRequest("register", { method: "POST", body });
  if (!response.ok) return NextResponse.json({ detail: await authError(response) }, { status: response.status });

  const payload = await response.json() as AuthPayload;
  const result = NextResponse.json({ user: payload.user }, { status: 201 });
  result.cookies.set(sessionCookieName, payload.access_token, sessionCookieOptions(payload.expires_at));
  return result;
}
