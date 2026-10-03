"use client";

import React from "react";
import { formatBDT, formatPercent } from "@/lib/formatters";
import { TrendingDown, PieChart } from "lucide-react";

interface ExpenseCardProps {
  amount: number;
  necessityRatio?: number;
}

export function ExpenseCard({ amount, necessityRatio = 0 }: ExpenseCardProps) {
  const discretionaryRatio = Math.max(0, 1 - necessityRatio);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Monthly Outflow
        </span>
        <div className="rounded-lg bg-rose-50 p-2 text-rose-600">
          <TrendingDown className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-slate-900">
          {formatBDT(amount)}
        </div>
        <div className="mt-2">
          {/* Necessity vs Discretionary mini bar */}
          <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="bg-slate-700 transition-all duration-300"
              style={{ width: `${Math.min(100, necessityRatio * 100)}%` }}
              title={`Necessity: ${formatPercent(necessityRatio)}`}
            />
            <div
              className="bg-amber-400 transition-all duration-300"
              style={{ width: `${Math.min(100, discretionaryRatio * 100)}%` }}
              title={`Discretionary: ${formatPercent(discretionaryRatio)}`}
            />
          </div>
          <div className="mt-1.5 flex justify-between text-[11px] text-slate-500">
            <span>Necessity: {formatPercent(necessityRatio, 0)}</span>
            <span>Discretionary: {formatPercent(discretionaryRatio, 0)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
