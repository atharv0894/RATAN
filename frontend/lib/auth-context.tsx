"use client";
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { authApi, setTokens, clearTokens, getAccessToken, getRefreshToken } from "@/lib/api";
import { User as BaseUser } from "@/types";

interface User extends BaseUser {
  account_type: "PERSONAL" | "ORGANIZATION" | "SUPER_ADMIN";
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setTimeout(() => setIsLoading(false), 0);
      return;
    }
    try {
      const { data } = await authApi.me();
      setUser(data.data);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const { data } = await authApi.login(email, password);
    const { access_token, refresh_token } = data.data;
    setTokens(access_token, refresh_token);
    const meRes = await authApi.me();
    setUser(meRes.data.data);
    return meRes.data.data;
  };

  const logout = async () => {
    const refresh = getRefreshToken();
    if (refresh) {
      try { await authApi.logout(refresh); } catch { /* ignore */ }
    }
    clearTokens();
    setUser(null);
    window.location.href = "/auth/login";
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
