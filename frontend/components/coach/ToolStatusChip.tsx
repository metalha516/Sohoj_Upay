"use client";

import React from "react";
import {
  Wrench,
  Search,
  Calculator,
  ShieldAlert,
  Wallet,
  TrendingUp,
  CheckCircle2,
  Clock,
} from "lucide-react";

interface ToolStatusChipProps {
  tool: string;
  status: "running" | "completed";
  callIndex?: number;
}

const TOOL_DESCRIPTIONS: Record<string, { label: string; icon: any }> = {
  get_current_balance: { label: "Checking current balance", icon: Wallet },
  get_user_profile: { label: "Reviewing profile & income", icon: Wrench },
  get_transactions: { label: "Scanning transaction records", icon: Wrench },
  get_monthly_summary: { label: "Analyzing monthly spending", icon: TrendingUp },
  get_behavior_profile: { label: "Consulting behavior model", icon: TrendingUp },
  get_spending_forecast: { label: "Querying expense forecast", icon: TrendingUp },
  get_anomalies: { label: "Checking unusual expenses", icon: ShieldAlert },
  get_financial_goals: { label: "Inspecting financial goals", icon: Calculator },
  calculate_future_value: { label: "Calculating future growth", icon: Calculator },
  calculate_doubling_time: { label: "Computing doubling time", icon: Calculator },
  calculate_goal_plan: { label: "Calculating savings requirement", icon: Calculator },
  calculate_savings_rate: { label: "Evaluating savings rate", icon: Calculator },
  run_financial_scenario: { label: "Running scenario projection", icon: Calculator },
  check_affordability: { label: "Verifying affordability impact", icon: Calculator },
  search_knowledge: { label: "Searching financial knowledge base", icon: Search },
};

export function ToolStatusChip({ tool, status, callIndex }: ToolStatusChipProps) {
  const config = TOOL_DESCRIPTIONS[tool] || {
    label: tool.replace(/_/g, " "),
    icon: Wrench,
  };
  const Icon = config.icon;
  const isRunning = status === "running";

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium transition-all ${
        isRunning
          ? "bg-amber-50 text-amber-800 border border-amber-200 animate-pulse"
          : "bg-slate-100 text-slate-700 border border-slate-200"
      }`}
      title={`Tool: ${tool}`}
    >
      <Icon className="h-3 w-3 shrink-0" />
      <span>{config.label}</span>
      {isRunning ? (
        <Clock className="h-3 w-3 shrink-0 text-amber-600 animate-spin" />
      ) : (
        <CheckCircle2 className="h-3 w-3 shrink-0 text-navy-900" />
      )}
    </div>
  );
}
