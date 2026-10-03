"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Receipt,
  Target,
  Calculator,
  Settings,
} from "lucide-react";

export function AppBottomNav() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/transactions", label: "Transactions", icon: Receipt },
    { href: "/coach", label: "Coach", icon: Settings },
    { href: "/behavior", label: "Behavior", icon: Target },
    { href: "/simulator", label: "Simulator", icon: Calculator },
  ];

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-200 bg-white/95 backdrop-blur md:hidden"
      aria-label="Mobile Bottom Navigation"
    >
      <div className="flex h-16 items-center justify-around px-2">
        {navLinks.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center gap-1 px-3 py-1 text-xs font-medium transition-colors ${
                isActive
                  ? "text-emerald-700 font-semibold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
