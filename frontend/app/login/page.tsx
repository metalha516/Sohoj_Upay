"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Lock, Mail, AlertCircle, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login({ email, password });
    } catch (err: any) {
      setError(err.problem?.detail || err.message || "Invalid credentials or account locked");
    } finally {
      setIsLoading(false);
    }
  };

  // One-click demo login — auto-submits without touching the form
  const handleQuickLogin = async (demoEmail: string) => {
    setError(null);
    setIsLoading(true);
    setEmail(demoEmail);
    setPassword("SecurePassword123!");

    try {
      await login({ email: demoEmail, password: "SecurePassword123!" });
    } catch (err: any) {
      setError(err.problem?.detail || err.message || "Login failed. Please try manually.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-50 via-slate-100 to-upay-yellow/10">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center">
          <Link
            href="/"
            className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-upay-500 text-navy-900 font-black text-2xl shadow-md border border-navy-800 hover:scale-105 transition-transform"
          >
            S
          </Link>
          <h1 className="mt-4 text-2xl font-black tracking-tight text-navy-900">
            Welcome to Sohoj
          </h1>
          <p className="mt-1 text-xs text-slate-500 font-medium">
            Sign in to access your financial dashboard and insights
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm">
          {error && (
            <div className="mb-5 flex items-center gap-2 rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="login-email"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="login-email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="user@example.test"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-navy-900 focus:outline-none focus:ring-2 focus:ring-navy-900/20 font-medium"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="login-password"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="login-password"
                  type="password"
                  required
                  autoComplete="current-password"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-navy-900 focus:outline-none focus:ring-2 focus:ring-navy-900/20 font-medium"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 inline-flex items-center justify-center gap-2 rounded-xl bg-navy-900 px-4 py-2.5 text-xs font-bold text-upay-yellow shadow-sm hover:bg-navy-800 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:ring-offset-2 disabled:opacity-50 transition border border-navy-800"
            >
              {isLoading ? "Signing in..." : "Sign In to Account"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          {/* One-Click Demo Login */}
          <div className="mt-6 border-t border-slate-100 pt-4">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
              ⚡ One-Click Demo Login:
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                id="demo-sumaiya"
                type="button"
                disabled={isLoading}
                onClick={() => handleQuickLogin("sumaiya.talukder.26dafe@example.com")}
                className="rounded-lg bg-navy-50/80 border border-navy-100 px-3 py-2 text-[11px] font-bold text-navy-900 hover:bg-navy-900 hover:text-upay-yellow hover:border-navy-900 transition-all duration-300 hover:-translate-y-0.5 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Signing in..." : "Sumaiya (Driver)"}
              </button>
              <button
                id="demo-roksana"
                type="button"
                disabled={isLoading}
                onClick={() => handleQuickLogin("roksana.khan.71141c@example.test")}
                className="rounded-lg bg-navy-50/80 border border-navy-100 px-3 py-2 text-[11px] font-bold text-navy-900 hover:bg-navy-900 hover:text-upay-yellow hover:border-navy-900 transition-all duration-300 hover:-translate-y-0.5 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Signing in..." : "Roksana (Student)"}
              </button>
            </div>
            <p className="mt-1.5 text-[10px] text-slate-400">Click once to instantly sign in as a demo user</p>
          </div>
        </div>

        <p className="text-center text-xs text-slate-500 font-medium">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-bold text-navy-900 hover:underline"
          >
            Create an account
          </Link>
        </p>
      </div>
    </main>
  );
}
