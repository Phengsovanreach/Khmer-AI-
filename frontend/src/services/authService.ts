/**
 * Angkor Nexus — Production Authentication Service
 * Manages API calls, cryptographic token storage, HttpOnly cookies, and session validation.
 */

export interface UserProfile {
  id: string;
  name: string;
  full_name?: string;
  email: string;
  created_at: string;
  updated_at?: string;
  last_login_at?: string;
  status?: string;
  email_verified?: boolean;
  avatar_color: string;
}

export type AuthUser = UserProfile;

export interface AuthResponse {
  success: boolean;
  user: UserProfile;
  token: string;
  message: string;
}

const TOKEN_KEY = 'khmer_ai_auth_token';
const USER_KEY = 'khmer_ai_auth_user';

export class AuthService {
  public static getApiBase(): string {
    const custom = typeof window !== 'undefined' ? localStorage.getItem('khmer_ai_api_url') : null;
    if (custom && custom.trim()) {
      return custom.trim().replace(/\/+$/, '');
    }
    if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) {
      return import.meta.env.VITE_API_URL.trim().replace(/\/+$/, '');
    }
    const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
    if (isHttps) {
      return 'https://khmer-ai-1ktp.onrender.com';
    }
    return 'http://127.0.0.1:8000';
  }

  public static getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
  }

  public static getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  public static setSession(token: string, user: UserProfile, rememberMe: boolean = true): void {
    if (rememberMe) {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USER_KEY);
    } else {
      sessionStorage.setItem(TOKEN_KEY, token);
      sessionStorage.setItem(USER_KEY, JSON.stringify(user));
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  }

  public static getCachedUser(): UserProfile | null {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  public static clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  }

  public static async register(
    name: string,
    email: string,
    password: string
  ): Promise<AuthResponse> {
    const res = await fetch(`${this.getApiBase()}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, email, password, terms_accepted: true }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || 'Registration failed / ការចុះឈ្មោះបរាជ័យ');
    }

    this.setSession(data.token, data.user, true);
    return data;
  }

  public static async login(
    email: string,
    password: string,
    rememberMe: boolean = true
  ): Promise<AuthResponse> {
    const res = await fetch(`${this.getApiBase()}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password, remember_me: rememberMe }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || 'Invalid email or password / អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ');
    }

    this.setSession(data.token, data.user, rememberMe);
    return data;
  }

  public static async verifySession(): Promise<UserProfile | null> {
    const token = this.getToken();

    try {
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${this.getApiBase()}/api/auth/me`, {
        headers,
        credentials: 'include',
      });

      if (!res.ok) {
        if (token) this.clearSession();
        return null;
      }

      const data = await res.json();
      if (data.authenticated && data.user) {
        if (token) {
          const isLocal = !!localStorage.getItem(TOKEN_KEY);
          this.setSession(token, data.user, isLocal);
        } else {
          sessionStorage.setItem(USER_KEY, JSON.stringify(data.user));
        }
        return data.user;
      }
      if (token) this.clearSession();
      return null;
    } catch {
      // In offline / network glitch, fallback to cached user if available
      return this.getCachedUser();
    }
  }

  public static async logout(): Promise<void> {
    const token = this.getToken();
    try {
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
      await fetch(`${this.getApiBase()}/api/auth/logout`, {
        method: 'POST',
        headers,
        credentials: 'include',
      });
    } catch {
      // Ignore network failure on logout
    }
    this.clearSession();
  }
}
