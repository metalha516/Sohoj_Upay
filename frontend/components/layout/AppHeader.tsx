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
    <header className="sticky top-0 z-40 border-b border-navy-800/80 bg-navy-900/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand / Logo */}
        <div className="flex items-center gap-8">
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5 text-xl font-bold tracking-tight text-white focus:outline-none focus:ring-2 focus:ring-upay-500 rounded-lg"
            aria-label="Sohoj Home"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-upay-500 text-navy-950 font-black shadow-md shadow-upay-500/20">
              S
            </div>
            <span className="flex items-center gap-2 font-black tracking-tight text-white">
              Sohoj
              <span className="rounded-md bg-upay-500/15 px-2 py-0.5 text-xs font-bold text-upay-400 border border-upay-500/30">
                Upay
              </span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1.5" aria-label="Main Navigation">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold transition-all ${
                    isActive
                      ? "bg-navy-800 text-upay-400 border border-navy-700/80 shadow-sm"
                      : "text-slate-300 hover:bg-navy-800/60 hover:text-white"
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className={`h-4 w-4 ${isActive ? "text-upay-500" : "text-slate-400"}`} aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Section / User menu */}
        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-slate-200 bg-navy-800/80 px-3 py-1.5 rounded-full border border-navy-700/60">
              <span className="h-2 w-2 rounded-full bg-upay-500 ring-2 ring-upay-500/30 animate-pulse" />
              <span className="truncate max-w-[140px]">{user.full_name || user.email}</span>
            </div>
          )}

          <Link
            href="/settings"
            className={`p-2 rounded-xl text-slate-300 hover:bg-navy-800/80 hover:text-white transition-colors ${
              pathname === "/settings" ? "bg-navy-800 text-upay-400 border border-navy-700" : ""
            }`}
            aria-label="Account Settings"
          >
            <Settings className="h-5 w-5" aria-hidden="true" />
          </Link>

          <Link
            href="/profile"
            className={`p-2 rounded-xl text-slate-300 hover:bg-navy-800/80 hover:text-white transition-colors ${
              pathname === "/profile" ? "bg-navy-800 text-upay-400 border border-navy-700" : ""
            }`}
            aria-label="User Profile"
          >
            <User className="h-5 w-5" aria-hidden="true" />
          </Link>

          <button
            onClick={() => logout()}
            className="p-2 rounded-xl text-slate-400 hover:bg-rose-950/40 hover:text-rose-400 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500"
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
