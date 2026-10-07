"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { User, LoginRequest, RegisterRequest, UserUpdateRequest } from "@/types/api";
import { apiClient } from "@/lib/api-client";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (req: LoginRequest) => Promise<void>;
  register: (req: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (req: UserUpdateRequest) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function initAuth() {
      try {
        const token = apiClient.getToken();
        if (token) {
          const currentUser = await apiClient.getCurrentUser();
          setUser(currentUser);
        }
      } catch (err) {
        console.warn("User session check failed:", err);
        apiClient.setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    initAuth();
  }, []);

  const sanitizeRedirectPath = (path: string | null | undefined): string => {
    if (!path) return "/dashboard";
    // Must be a relative path starting with a single '/'
    if (!path.startsWith("/") || path.startsWith("//") || path.includes("://")) {
      return "/dashboard";
    }
    // Prevent redirect loops
    if (path === "/login" || path === "/register") {
      return "/dashboard";
    }
    return path;
  };

  const login = async (req: LoginRequest) => {
    await apiClient.login(req);
    const currentUser = await apiClient.getCurrentUser();
    setUser(currentUser);
    const searchParams = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
    const redirectPath = sanitizeRedirectPath(searchParams?.get("redirect"));
    router.push(redirectPath);
  };

  const register = async (req: RegisterRequest) => {
    const newUser = await apiClient.register(req);
    setUser(newUser);
    const searchParams = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
    const redirectPath = sanitizeRedirectPath(searchParams?.get("redirect"));
    router.push(redirectPath);
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch {
      // Even if network fails, clear local state
    } finally {
      apiClient.setToken(null);
      setUser(null);
      router.push("/login");
    }
  };

  const updateUser = async (req: UserUpdateRequest) => {
    const updated = await apiClient.updateProfile(req);
    setUser(updated);
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
