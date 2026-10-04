"use client";

import React from "react";
import Link from "next/link";
import { Goal } from "@/types/api";
import { formatBDT, formatPercent, formatDate } from "@/lib/formatters";
import { Target, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

interface FinancialGoalCardProps {
  goals: Goal[];
}

export function FinancialGoalCard({ goals }: FinancialGoalCardProps) {
  if (!goals || goals.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
        <div className="flex items-center justify-between">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Financial Goals</h3>
          <Link
            href="/goals"
            className="text-xs font-bold text-navy-900 hover:text-navy-700 hover:underline"
          >
            Create Goal
          </Link>
        </div>
        <div className="mt-4 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-navy-50 text-navy-900 mb-2 border border-navy-100">
            <Target className="h-6 w-6 text-navy-900" />
          </div>
          <p className="text-xs font-bold text-navy-900">No active goals yet</p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-xs font-medium">
            Set a savings target for an emergency buffer, gadget, or DPS deposit.
          </p>
          <Link
            href="/goals"
            className="mt-3 inline-flex items-center gap-1 rounded-xl bg-navy-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-navy-800 shadow-sm transition"
          >
            Create Goal
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <div className="rounded-xl bg-navy-900 p-1.5 text-upay-yellow shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
            <Target className="h-4 w-4" />
          </div>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Active Goals</h3>
        </div>
        <Link
          href="/goals"
          className="inline-flex items-center gap-1 text-xs font-bold text-navy-900 hover:text-navy-700"
        >
          View all ({goals.length})
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="space-y-3.5 pt-1">
        {goals.slice(0, 3).map((goal) => {
          const isComplete = goal.progress_pct >= 1;
          return (
            <div
              key={goal.id}
              className="rounded-xl border border-slate-200/70 bg-slate-50/70 p-3.5 transition hover:bg-slate-50"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-xs font-bold text-navy-900 line-clamp-1">
                    {goal.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5 font-medium">
                    Target: {formatDate(goal.target_date)}
                  </p>
                </div>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                    isComplete
                      ? "bg-navy-900 text-upay-yellow"
                      : goal.is_feasible
                      ? "bg-upay-yellow/20 text-navy-950 border border-upay-yellow/40"
                      : "bg-amber-100 text-amber-900"
                  }`}
                >
                  {isComplete ? (
                    <>
                      <CheckCircle2 className="h-3 w-3 text-upay-yellow" />
                      <span>Complete</span>
                    </>
                  ) : goal.is_feasible ? (
                    <span>On track · {formatPercent(goal.progress_pct, 0)}</span>
                  ) : (
                    <>
                      <AlertCircle className="h-3 w-3" />
                      <span>Lagging · {formatPercent(goal.progress_pct, 0)}</span>
                    </>
                  )}
                </span>
              </div>

              {/* Progress bar */}
              <div className="mt-2.5">
                <div className="flex justify-between text-[11px] text-slate-600 mb-1 font-semibold">
                  <span className="tabular-nums">{formatBDT(goal.current_amount)}</span>
                  <span className="text-slate-400 tabular-nums">of {formatBDT(goal.target_amount)}</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full bg-gradient-to-r from-navy-900 to-upay-yellow rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(100, goal.progress_pct * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
