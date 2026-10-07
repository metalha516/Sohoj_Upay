import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Bypass middleware for _next static assets, images, and static files
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const isDev = process.env.NODE_ENV === "development";

  // Build Content Security Policy (allow Next.js runtime hydration scripts)
  const scriptSrc = `'self' 'unsafe-inline' 'unsafe-eval'`;

  let backendOrigin = "";
  if (process.env.BACKEND_URL) {
    try {
      backendOrigin = new URL(process.env.BACKEND_URL).origin;
    } catch {
      // Invalid URL in env, fallback
    }
  }
  const devOrigins = isDev ? "http://localhost:8000 http://127.0.0.1:8000 ws: http:" : "";
  const connectSrc = `'self' ${devOrigins} ${backendOrigin}`.trim().replace(/\s+/g, " ");

  const cspHeader = `
    default-src 'self';
    script-src ${scriptSrc};
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' blob: data:;
    font-src 'self' https://fonts.gstatic.com;
    connect-src ${connectSrc};
    frame-ancestors 'none';
    form-action 'self';
    base-uri 'self';
  `
    .replace(/\s{2,}/g, " ")
    .trim();

  // Clone headers and attach nonce + CSP
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", cspHeader);

<<<<<<< HEAD
  const refreshToken = request.cookies.get("refresh_token")?.value;
=======
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("sohoj_access_token")?.value;

  // Validate that access token is present and not an old dummy string
  const hasValidAuth =
    !!token &&
    token !== "active_session" &&
    token !== "null" &&
    token !== "undefined" &&
    token.length > 20;
>>>>>>> 403f1465fb12a87eb6b261ec98469af2e03dd5ba

  // Protected application routes
  const protectedPaths = [
    "/dashboard",
    "/transactions",
    "/goals",
    "/simulator",
    "/profile",
    "/settings",
    "/coach",
    "/behavior",
  ];
  const isProtectedPath = protectedPaths.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );

  // Auth routes
  const isAuthPath = pathname === "/login" || pathname === "/register";

  // Redirection logic
  if (isProtectedPath && !hasValidAuth) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    const response = NextResponse.redirect(loginUrl);
    response.headers.set("Content-Security-Policy", cspHeader);
    // Clear any stale tokens
    response.cookies.delete("sohoj_access_token");
    response.cookies.delete("refresh_token");
    return response;
  }

<<<<<<< HEAD
  if (isAuthPath && refreshToken && !request.nextUrl.searchParams.has("redirect") && !request.nextUrl.searchParams.has("error")) {
=======
  if (isAuthPath && hasValidAuth) {
>>>>>>> 403f1465fb12a87eb6b261ec98469af2e03dd5ba
    const dashboardUrl = new URL("/dashboard", request.url);
    const response = NextResponse.redirect(dashboardUrl);
    response.headers.set("Content-Security-Policy", cspHeader);
    return response;
  }

  // Create response with security headers
  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  response.headers.set("Content-Security-Policy", cspHeader);
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "no-referrer");
  response.headers.set(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=()"
  );

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
