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
    <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Monthly Inflow
        </span>
        <div className="rounded-xl bg-navy-50 p-2 text-navy-900 border border-navy-100/60">
          <TrendingUp className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-3">
        <div className="tabular-nums text-2xl font-black tracking-tight text-navy-900">
          {formatBDT(amount)}
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-500 font-medium">
          <span className="inline-flex items-center text-navy-700 font-bold">
            <ArrowUpRight className="h-3.5 w-3.5 text-upay-yellow" />
            Active
          </span>
          <span>· {transactionCount} salary/cash-in deposits</span>
        </div>
      </div>
    </div>
  );
}
