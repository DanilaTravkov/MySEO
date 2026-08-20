import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { authApiRequest, sessionCookieName, sessionCookieOptions } from "@/lib/server-auth";

export async function POST() {
  const sessionToken = (await cookies()).get(sessionCookieName)?.value;
  if (sessionToken) await authApiRequest("logout", { method: "POST" }, sessionToken);
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(sessionCookieName, "", { ...sessionCookieOptions(), maxAge: 0 });
  return response;
}
