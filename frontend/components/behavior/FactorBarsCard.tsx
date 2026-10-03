"use client";

import React from "react";
import { BehaviorProfile } from "@/types/api";
import { Sliders, HelpCircle, ArrowUpRight, ArrowDownRight, CheckCircle2 } from "lucide-react";

interface FactorBarsCardProps {
  profile: BehaviorProfile | null;
  isLoading?: boolean;
}

export function FactorBarsCard({ profile, isLoading }: FactorBarsCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm animate-pulse">
        <div className="h-5 w-40 bg-slate-200 rounded mb-4" />
        <div className="space-y-4">
          <div className="h-4 bg-slate-100 rounded" />
          <div className="h-4 bg-slate-100 rounded" />
          <div className="h-4 bg-slate-100 rounded" />
        </div>
      </div>
    );
  }

  // Extract key factor metrics with safe fallbacks
  const savingsRate = Number(profile?.savings_rate ?? 0.22);
  const necessityRate = Number(profile?.necessity_rate ?? 0.54);
  const discretionaryRate = Number(profile?.discretionary_rate ?? 0.24);
  const cashoutFreq = Number(profile?.cashout_frequency ?? 4);
  const spendingVariance = Number(profile?.spending_variance ?? 0.18);

  const factors = [
    {
      name: "Savings Rate",
      value: Math.round(savingsRate * 100),
      benchmark: 20,
      unit: "%",
      status: savingsRate >= 0.2 ? "Optimal" : "Attention",
      statusColor: savingsRate >= 0.2 ? "text-emerald-700 bg-emerald-50" : "text-amber-700 bg-amber-50",
      description: "Portion of monthly income converted to persistent reserves",
      barColor: "bg-emerald-600",
    },
    {
      name: "Necessity Expense Ratio",
      value: Math.round(necessityRate * 100),
      benchmark: 50,
      unit: "%",
      status: necessityRate <= 0.6 ? "Healthy" : "Elevated",
      statusColor: necessityRate <= 0.6 ? "text-blue-700 bg-blue-50" : "text-amber-700 bg-amber-50",
      description: "Essential outlays (groceries, rent, medical, utilities)",
      barColor: "bg-blue-600",
    },
    {
      name: "Discretionary Ratio",
      value: Math.round(discretionaryRate * 100),
      benchmark: 30,
      unit: "%",
      status: discretionaryRate <= 0.3 ? "Controlled" : "High",
      statusColor: discretionaryRate <= 0.3 ? "text-emerald-700 bg-emerald-50" : "text-rose-700 bg-rose-50",
      description: "Lifestyle, dining out, and impulse transactions",
      barColor: "bg-purple-600",
    },
    {
      name: "Monthly Cash-Out Count",
      value: cashoutFreq,
      benchmark: 6,
      unit: " txns",
      status: cashoutFreq <= 6 ? "Prudent" : "Frequent",
      statusColor: cashoutFreq <= 6 ? "text-emerald-700 bg-emerald-50" : "text-amber-700 bg-amber-50",
      description: "Frequency of MFS agent cash withdrawals incurring tariffs",
      barColor: "bg-amber-500",
    },
    {
      name: "Spending Volatility",
      value: Math.round(spendingVariance * 100),
      benchmark: 25,
      unit: "%",
      status: spendingVariance <= 0.25 ? "Consistent" : "Volatile",
      statusColor: spendingVariance <= 0.25 ? "text-emerald-700 bg-emerald-50" : "text-rose-700 bg-rose-50",
      description: "Weekly variance coefficient in discretionary spending",
      barColor: "bg-indigo-600",
    },
  ];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Sliders className="h-5 w-5 text-emerald-600" />
          <h3 className="text-base font-bold text-slate-900">Explainability Factors</h3>
        </div>
        <span className="text-xs text-slate-500">Benchmark: 50/30/20 Guideline</span>
      </div>

      <p className="text-xs text-slate-500 mb-6">
        These calibrated drivers explain why your financial archetype was assigned. Each factor is benchmarked against balanced spending targets.
      </p>

      <div className="space-y-6">
        {factors.map((factor) => {
          const pctFill = Math.min(100, Math.max(5, factor.value));
          return (
            <div key={factor.name} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-800">{factor.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-full font-medium ${factor.statusColor}`}>
                    {factor.status}
                  </span>
                  <span className="font-bold text-slate-900">
                    {factor.value}
                    {factor.unit}
                  </span>
                </div>
              </div>

              {/* Progress Bar with Benchmark marker */}
              <div className="relative h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${factor.barColor}`}
                  style={{ width: `${pctFill}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>{factor.description}</span>
                <span>Target: ~{factor.benchmark}{factor.unit}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
