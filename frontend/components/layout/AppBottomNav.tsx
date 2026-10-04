"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Receipt,
  Target,
  Calculator,
  Sparkles,
} from "lucide-react";

export function AppBottomNav() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/transactions", label: "Transactions", icon: Receipt },
    { href: "/coach", label: "AI Coach", icon: Sparkles },
    { href: "/behavior", label: "Behavior", icon: Target },
    { href: "/simulator", label: "Simulator", icon: Calculator },
  ];

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-navy-800/80 bg-navy-950/95 backdrop-blur-md md:hidden"
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
              className={`flex flex-col items-center justify-center gap-1 px-3 py-1.5 rounded-xl text-xs font-medium transition-all duration-300 ${
                isActive
                  ? "text-upay-500 font-bold bg-navy-800/90 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className={`h-5 w-5 ${isActive ? "text-upay-500" : "text-slate-400"}`} aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
