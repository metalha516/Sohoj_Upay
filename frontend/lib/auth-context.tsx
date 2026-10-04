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

  const login = async (req: LoginRequest) => {
    await apiClient.login(req);
    const currentUser = await apiClient.getCurrentUser();
    setUser(currentUser);
    router.push("/dashboard");
  };

  const register = async (req: RegisterRequest) => {
    const newUser = await apiClient.register(req);
    setUser(newUser);
    router.push("/dashboard");
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch {
      // Even if network fails, clear local state
    } finally {
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
