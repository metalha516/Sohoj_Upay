"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { LoginRequest, RegisterRequest, User, UserUpdateRequest } from "@/types/api";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (req: LoginRequest) => Promise<void>;
  register: (req: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (req: UserUpdateRequest) => Promise<User>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    try {
      const u = await apiClient.getMe();
      setUser(u);
    } catch {
      setUser(null);
    }
  }, []);

  // Restore session on mount via refresh cookie
  useEffect(() => {
    let isMounted = true;
    async function initAuth() {
      try {
        const token = await apiClient.refreshToken();
        if (token && isMounted) {
          const u = await apiClient.getMe();
          if (isMounted) setUser(u);
        }
      } catch {
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    initAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (req: LoginRequest) => {
    setIsLoading(true);
    try {
      await apiClient.login(req);
      const u = await apiClient.getMe();
      setUser(u);
      router.push("/dashboard");
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (req: RegisterRequest) => {
    setIsLoading(true);
    try {
      await apiClient.register(req);
      // Auto-login after registration
      await apiClient.login({ email: req.email, password: req.password });
      const u = await apiClient.getMe();
      setUser(u);
      router.push("/dashboard");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await apiClient.logout();
      setUser(null);
      router.push("/login");
    } finally {
      setIsLoading(false);
    }
  };

  const updateUser = async (req: UserUpdateRequest) => {
    const updated = await apiClient.updateMe(req);
    setUser(updated);
    return updated;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        updateUser,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
