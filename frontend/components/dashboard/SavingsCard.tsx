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
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Net Monthly Savings
        </span>
        <div
          className={`rounded-lg p-2 ${
            isHealthy
              ? "bg-emerald-50 text-emerald-600"
              : "bg-amber-50 text-amber-600"
          }`}
        >
          <PiggyBank className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-3">
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {formatBDT(savingsAmount)}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-bold ${
              isHealthy
                ? "bg-emerald-100 text-emerald-800"
                : "bg-amber-100 text-amber-800"
            }`}
          >
            {formatPercent(savingsRate)} rate
          </span>
        </div>

        <div className="mt-2.5 flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-100">
          <ShieldCheck className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          <span>
            Emergency fund:{" "}
            <strong className="text-slate-900">
              {Number(emergencyFundMonths || 0).toFixed(1)} mo
            </strong>{" "}
            runway
          </span>
        </div>
      </div>
    </div>
  );
}
