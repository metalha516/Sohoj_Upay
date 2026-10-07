"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiClient } from "@/lib/api-client";

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      const token = apiClient.getToken();
      if (!token || !user) {
        const dest = `/login?redirect=${encodeURIComponent(pathname)}`;
        router.replace(dest);
        const timer = setTimeout(() => {
          if (typeof window !== "undefined" && window.location.pathname !== "/login") {
            window.location.href = dest;
          }
        }, 300);
        return () => clearTimeout(timer);
      }
    }
  }, [isLoading, user, pathname, router]);

  if (isLoading || !user || !apiClient.getToken()) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-700">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-upay-500 text-navy-950 font-black text-2xl shadow-lg upay-glow animate-pulse mb-4">
          S
        </div>
        <p className="text-sm font-semibold text-slate-600">Verifying session...</p>
      </div>
    );
  }

  return <>{children}</>;
}
