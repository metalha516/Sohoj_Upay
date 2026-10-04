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

  const handleQuickFill = (testEmail: string) => {
    setEmail(testEmail);
    setPassword("SecurePassword123!");
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-slate-50">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center">
          <Link
            href="/"
            className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-white font-black text-lg shadow-sm hover:bg-emerald-500 transition"
          >
            SU
          </Link>
          <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-slate-900">
            Welcome to Shohoj Upay
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Sign in to access your financial dashboard and insights
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
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
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
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
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-50 transition"
            >
              {isLoading ? "Signing in..." : "Sign In to Account"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          {/* Seed Quick-Fill Helpers */}
          <div className="mt-6 border-t border-slate-100 pt-4">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Quick Test Seed Personas:
            </p>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => handleQuickFill("sumaiya.talukder.26dafe@example.com")}
                className="rounded-lg bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition"
              >
                Sumaiya (Driver)
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill("roksana.khan.71141c@example.test")}
                className="rounded-lg bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition"
              >
                Roksana (Student)
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill("kamrul.akter.8d6ed3@example.test")}
                className="rounded-lg bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition"
              >
                Kamrul (Remittance)
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-500">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-bold text-emerald-600 hover:text-emerald-500"
          >
            Create an account
          </Link>
        </p>
      </div>
    </main>
  );
}
