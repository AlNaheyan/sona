import { NextRequest, NextResponse } from "next/server";

const protectedRoutes = ["/dashboard", "/onboarding", "/recommendations", "/settings", "/profile"];
const authRoutes = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const accessToken = request.cookies.get("access_token")?.value;
  const isLoggedIn = !!accessToken;

  // Redirect logged-in users away from auth pages
  if (isLoggedIn && authRoutes.some((r) => pathname.startsWith(r))) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Redirect unauthenticated users away from protected pages
  if (!isLoggedIn && protectedRoutes.some((r) => pathname.startsWith(r))) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/onboarding/:path*",
    "/recommendations/:path*",
    "/settings/:path*",
    "/profile/:path*",
    "/login",
    "/register",
  ],
};
