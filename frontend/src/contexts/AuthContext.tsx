import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, setAccessToken, unwrap } from '@/services/api';
import type { ApiEnvelope, LoginResponse, User } from '@/types';
import type { LoginInput, RegisterInput } from '@/utils/validators';

const USER_KEY = 'turf_user';

export interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (input: LoginInput) => Promise<User>;
  register: (input: RegisterInput) => Promise<User>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [user, setUser] = useState<User | null>(readStoredUser);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    async function bootstrap(): Promise<void> {
      try {
        const response = await api.post<ApiEnvelope<{ access_token: string }>>('/auth/refresh');
        setAccessToken(unwrap(response.data).access_token);
      } catch {
        if (active) {
          setUser(null);
          localStorage.removeItem(USER_KEY);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    void bootstrap();
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (input: LoginInput): Promise<User> => {
    const response = await api.post<ApiEnvelope<LoginResponse>>('/auth/login', input);
    const data = unwrap(response.data);
    setAccessToken(data.access_token);
    setUser(data.user);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    return data.user;
  }, []);

  const register = useCallback(async (input: RegisterInput): Promise<User> => {
    const response = await api.post<ApiEnvelope<User>>('/auth/register', input);
    return unwrap(response.data);
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } finally {
      setAccessToken(null);
      setUser(null);
      localStorage.removeItem(USER_KEY);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
