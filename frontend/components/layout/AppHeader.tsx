"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  LayoutDashboard,
  Receipt,
  Target,
  Calculator,
  User,
  Settings,
  LogOut,
  Sparkles,
} from "lucide-react";

export function AppHeader() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/transactions", label: "Transactions", icon: Receipt },
    { href: "/goals", label: "Goals", icon: Target },
    { href: "/simulator", label: "Simulator", icon: Calculator },
    { href: "/behavior", label: "Behavior", icon: Sparkles },
    { href: "/coach", label: "AI Coach", icon: Sparkles },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand / Logo */}
        <div className="flex items-center gap-8">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-xl font-bold tracking-tight text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded"
            aria-label="Sohoj Home"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm font-black">
              S
            </div>
            <span className="flex items-center gap-1.5">
              Sohoj
              <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-xs font-semibold text-emerald-800">
                Coach
              </span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1" aria-label="Main Navigation">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-emerald-50 text-emerald-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Section / User menu */}
        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-slate-600 bg-slate-100 px-2.5 py-1.5 rounded-full">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>{user.full_name || user.email}</span>
            </div>
          )}

          <Link
            href="/settings"
            className={`p-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors ${
              pathname === "/settings" ? "bg-slate-100 text-slate-900" : ""
            }`}
            aria-label="Account Settings"
          >
            <Settings className="h-5 w-5" aria-hidden="true" />
          </Link>

          <Link
            href="/profile"
            className={`p-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors ${
              pathname === "/profile" ? "bg-slate-100 text-slate-900" : ""
            }`}
            aria-label="User Profile"
          >
            <User className="h-5 w-5" aria-hidden="true" />
          </Link>

          <button
            onClick={() => logout()}
            className="p-2 rounded-lg text-slate-500 hover:bg-rose-50 hover:text-rose-600 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500"
            aria-label="Log Out"
            title="Log Out"
          >
            <LogOut className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </header>
  );
}
