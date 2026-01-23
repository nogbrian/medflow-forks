const TOKEN_KEY = "medflow_token";
const USER_KEY = "medflow_user";
const COOKIE_NAME = "medflow_token";

/** Cookie domain for cross-subdomain auth (studio, playground, etc.) */
function getCookieDomain(): string {
  if (typeof window === "undefined") return "";
  const host = window.location.hostname;
  // In production, set domain to root so all subdomains share the cookie
  const parts = host.split(".");
  if (parts.length >= 3 && !host.includes("localhost")) {
    return `.${parts.slice(-3).join(".")}`;
  }
  return host;
}

function setAuthCookie(token: string): void {
  const domain = getCookieDomain();
  const secure = window.location.protocol === "https:";
  const maxAge = 60 * 60 * 24 * 7; // 7 days
  document.cookie = `${COOKIE_NAME}=${token}; path=/; domain=${domain}; max-age=${maxAge}; SameSite=Lax${secure ? "; Secure" : ""}`;
}

function clearAuthCookie(): void {
  const domain = getCookieDomain();
  document.cookie = `${COOKIE_NAME}=; path=/; domain=${domain}; max-age=0; SameSite=Lax`;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: "superuser" | "agency_staff" | "clinic_owner" | "clinic_staff";
  agency_id: string | null;
  clinic_id: string | null;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function storeAuth(token: string, user: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  setAuthCookie(token);
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  clearAuthCookie();
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Credenciais inválidas");
  }

  return res.json();
}

export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(url, { ...options, headers });
}
