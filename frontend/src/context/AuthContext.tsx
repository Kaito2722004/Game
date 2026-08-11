import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi } from "@/api/authApi";
import { getStoredToken, setStoredToken } from "@/api/client";
import type { LoginRequest, RegisterRequest, User, UserRole } from "@/types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  /** True while the stored token is being checked on first load. */
  initialising: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<User>;
  register: (payload: RegisterRequest) => Promise<User>;
  logout: () => void;
  /** Role check used to enable or hide write actions. */
  hasRole: (...roles: UserRole[]) => boolean;
  canManage: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * JWT session state.
 *
 * Deliberately non-blocking: if the backend is unreachable the app still
 * renders, signed out, so the UI can be developed and demonstrated without a
 * running API. Only write actions require a session.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [initialising, setInitialising] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      if (!getStoredToken()) {
        setInitialising(false);
        return;
      }
      try {
        const currentUser = await authApi.me();
        if (!cancelled) setUser(currentUser);
      } catch {
        // An expired or invalid token should not trap the user signed-out-ish.
        if (!cancelled) {
          setStoredToken(null);
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setInitialising(false);
      }
    }

    void restoreSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (payload: LoginRequest) => {
    const response = await authApi.login(payload);
    setStoredToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  }, []);

  const register = useCallback(async (payload: RegisterRequest) => {
    const response = await authApi.register(payload);
    setStoredToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  }, []);

  const logout = useCallback(() => {
    setStoredToken(null);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(() => {
    const hasRole = (...roles: UserRole[]) => (user ? roles.includes(user.role) : false);
    return {
      user,
      token,
      initialising,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      hasRole,
      canManage: hasRole("ADMIN", "TEACHER"),
    };
  }, [user, token, initialising, login, register, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside an AuthProvider");
  return context;
}
