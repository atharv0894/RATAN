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
  loginPersonal: (e: string, p: string) => Promise<User>;
  loginEnterprise: (e: string, p: string) => Promise<User>;
  loginSuperAdmin: (e: string, p: string) => Promise<User>;
  registerPersonal: (data: any) => Promise<void>;
  registerEnterprise: (data: any) => Promise<void>;
  logout: () => void;
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
      const { data } = await authApi.get_me();
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

  const loginPersonal = async (email: string, pass: string) => {
    const res = await authApi.login_personal(email, pass);
    setTokens(res.data.data.access_token, res.data.data.refresh_token);
    const userRes = await authApi.get_me();
    setUser(userRes.data.data);
    return userRes.data.data;
  };

  const loginEnterprise = async (email: string, pass: string) => {
    const res = await authApi.login_enterprise(email, pass);
    setTokens(res.data.data.access_token, res.data.data.refresh_token);
    const userRes = await authApi.get_me();
    setUser(userRes.data.data);
    return userRes.data.data;
  };

  const loginSuperAdmin = async (email: string, pass: string) => {
    const res = await authApi.login_super_admin(email, pass);
    setTokens(res.data.data.access_token, res.data.data.refresh_token);
    const userRes = await authApi.get_me();
    setUser(userRes.data.data);
    return userRes.data.data;
  };

  const registerPersonal = async (data: any) => {
    await authApi.register_personal(data);
  };

  const registerEnterprise = async (data: any) => {
    await authApi.register_enterprise(data);
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
    <AuthContext.Provider value={{ 
      user, isLoading, isAuthenticated: !!user, 
      loginPersonal, loginEnterprise, loginSuperAdmin, 
      registerPersonal, registerEnterprise, logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
