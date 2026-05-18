const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ─────────────────────────────────────────────
   Token Storage
   access_token: short-lived (30min), stored in JS-accessible cookie for
   Authorization header injection.
   refresh_token: long-lived (7d), stored in HttpOnly cookie set by the
   backend — JS cannot read or write it.
   ───────────────────────────────────────────── */
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name: string, value: string, days: number) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function deleteCookie(name: string) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

export function getAccessToken(): string | null {
  return getCookie("access_token");
}

export function setTokens(accessToken: string) {
  setCookie("access_token", accessToken, 1);
}

export async function clearTokens() {
  deleteCookie("access_token");
  // Ask the backend to clear the HttpOnly refresh_token cookie
  try {
    await fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Ignore — the access token is already cleared
  }
}

/* ─────────────────────────────────────────────
   Authenticated Fetch Wrapper
   ───────────────────────────────────────────── */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  // If 401 and we have an access token (meaning we were logged in), try refreshing
  if (res.status === 401 && getAccessToken()) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${getAccessToken()}`;
      const retryRes = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      });
      if (!retryRes.ok) {
        const err = await retryRes.json().catch(() => ({}));
        throw new ApiError(retryRes.status, err.detail || "Request failed");
      }
      return retryRes.json();
    } else {
      clearTokens();
      throw new ApiError(401, "Session expired");
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail || "Request failed");
  }

  return res.json();
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/* ─────────────────────────────────────────────
   Token Refresh
   ───────────────────────────────────────────── */
async function refreshTokens(): Promise<boolean> {
  try {
    // No body needed — the backend reads the HttpOnly refresh_token cookie automatically
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    if (!res.ok) return false;

    const data = await res.json();
    setTokens(data.access_token);
    return true;
  } catch {
    return false;
  }
}

/* ─────────────────────────────────────────────
   Auth API
   ───────────────────────────────────────────── */
export interface AuthUser {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authApi = {
  async register(email: string, username: string, password: string): Promise<AuthUser> {
    const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, username, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(res.status, err.detail || "Registration failed");
    }

    return res.json();
  },

  async login(email: string, password: string): Promise<AuthUser> {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(res.status, err.detail || "Invalid credentials");
    }

    const data: TokenResponse = await res.json();
    setTokens(data.access_token);

    // Fetch user profile
    return this.me();
  },

  async me(): Promise<AuthUser> {
    return apiFetch<AuthUser>("/api/v1/auth/me");
  },

  async logout(): Promise<void> {
    await clearTokens();
  },
};
