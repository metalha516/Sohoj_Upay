"use client";

import React from "react";
import { formatBDT, formatPercent } from "@/lib/formatters";
import { ShieldCheck, PiggyBank } from "lucide-react";

interface SavingsCardProps {
  savingsAmount: number;
  savingsRate: number;
  emergencyFundMonths?: number;
}

export function SavingsCard({
  savingsAmount,
  savingsRate,
  emergencyFundMonths = 0,
}: SavingsCardProps) {
  const isHealthy = savingsRate >= 0.2; // 20% savings rule

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Net Monthly Savings
        </span>
        <div className="rounded-xl p-2 bg-navy-50 text-navy-900 border border-navy-100/60">
          <PiggyBank className="h-4 w-4 text-navy-900" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-3">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="text-2xl font-black tracking-tight text-navy-900">
            {formatBDT(savingsAmount)}
          </span>
          <span className="rounded-full bg-upay-yellow/20 px-2.5 py-0.5 text-xs font-black text-navy-900 border border-upay-yellow/50">
            {formatPercent(savingsRate)} rate
          </span>
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-xs text-navy-900 bg-navy-50/70 px-3 py-2 rounded-xl border border-navy-100/70">
          <ShieldCheck className="h-4 w-4 text-navy-800" aria-hidden="true" />
          <span>
            Emergency fund:{" "}
            <strong className="text-navy-950 font-bold">
              {Number(emergencyFundMonths || 0).toFixed(1)} mo
            </strong>{" "}
            runway
          </span>
        </div>
      </div>
    </div>
  );
}
