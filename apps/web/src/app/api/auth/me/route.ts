import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { authApiRequest, authError, sessionCookieName, sessionCookieOptions } from "@/lib/server-auth";

async function token() {
  return (await cookies()).get(sessionCookieName)?.value;
}

function unauthorized() {
  const response = NextResponse.json({ detail: "Not authenticated." }, { status: 401 });
  response.cookies.set(sessionCookieName, "", { ...sessionCookieOptions(), maxAge: 0 });
  return response;
}

export async function GET() {
  const sessionToken = await token();
  if (!sessionToken) return unauthorized();
  const response = await authApiRequest("me", { method: "GET" }, sessionToken);
  if (response.status === 401) return unauthorized();
  if (!response.ok) return NextResponse.json({ detail: await authError(response) }, { status: response.status });
  return NextResponse.json({ user: await response.json() });
}

export async function PATCH(request: Request) {
  const sessionToken = await token();
  if (!sessionToken) return unauthorized();
  const response = await authApiRequest(
    "me",
    { method: "PATCH", body: await request.text() },
    sessionToken,
  );
  if (response.status === 401) return unauthorized();
  if (!response.ok) return NextResponse.json({ detail: await authError(response) }, { status: response.status });
  return NextResponse.json({ user: await response.json() });
}
