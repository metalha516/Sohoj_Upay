"use client";

import React from "react";
import Link from "next/link";
import {
  Target,
  Calculator,
  PieChart,
  Receipt,
  LayoutDashboard,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

interface UiActionButtonProps {
  action: string;
  payload?: Record<string, any> | null;
}

export function UiActionButton({ action, payload }: UiActionButtonProps) {
  const getActionConfig = (actionName: string) => {
    switch (actionName) {
      case "navigate_to_goals":
        return {
          href: "/goals",
          label: "View Financial Goals",
          icon: Target,
          bg: "bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-emerald-200",
        };
      case "open_simulator":
        return {
          href: "/simulator",
          label: "Open Wealth Simulator",
          icon: Calculator,
          bg: "bg-blue-50 hover:bg-blue-100 text-blue-800 border-blue-200",
        };
      case "view_budget":
        return {
          href: "/dashboard",
          label: "Check Budget & Spending",
          icon: PieChart,
          bg: "bg-purple-50 hover:bg-purple-100 text-purple-800 border-purple-200",
        };
      case "view_transactions":
        return {
          href: "/transactions",
          label: "Inspect Transactions",
          icon: Receipt,
          bg: "bg-amber-50 hover:bg-amber-100 text-amber-800 border-amber-200",
        };
      case "view_dashboard":
        return {
          href: "/dashboard",
          label: "Return to Dashboard",
          icon: LayoutDashboard,
          bg: "bg-slate-50 hover:bg-slate-100 text-slate-800 border-slate-200",
        };
      case "view_anomalies":
        return {
          href: "/behavior",
          label: "Review Spending Anomalies",
          icon: AlertTriangle,
          bg: "bg-rose-50 hover:bg-rose-100 text-rose-800 border-rose-200",
        };
      default:
        return {
          href: "/dashboard",
          label: actionName.replace(/_/g, " "),
          icon: ArrowRight,
          bg: "bg-slate-50 hover:bg-slate-100 text-slate-800 border-slate-200",
        };
    }
  };

  const config = getActionConfig(action);
  const Icon = config.icon;

  return (
    <div className="my-2.5 inline-block">
      <Link
        href={config.href}
        className={`inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-semibold shadow-sm transition-all hover:shadow focus:outline-none focus:ring-2 focus:ring-emerald-500 ${config.bg}`}
      >
        <Icon className="h-4 w-4 shrink-0" />
        <span>{config.label}</span>
        <ArrowRight className="h-3 w-3 shrink-0 opacity-70" />
      </Link>
    </div>
  );
}
