"use client";

import React from "react";
import { formatBDT } from "@/lib/formatters";
import { TrendingUp, ArrowUpRight } from "lucide-react";

interface IncomeCardProps {
  amount: number;
  transactionCount?: number;
}

export function IncomeCard({ amount, transactionCount = 0 }: IncomeCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Monthly Inflow
        </span>
        <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
          <TrendingUp className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-slate-900">
          {formatBDT(amount)}
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
          <span className="inline-flex items-center text-emerald-600 font-medium">
            <ArrowUpRight className="h-3.5 w-3.5" />
            Active
          </span>
          <span>· {transactionCount} salary/cash-in deposits</span>
        </div>
      </div>
    </div>
  );
}
