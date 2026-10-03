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
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900">Financial Goals</h3>
          <Link
            href="/goals"
            className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
          >
            Create Goal
          </Link>
        </div>
        <div className="mt-4 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
          <Target className="h-8 w-8 text-slate-400 mb-2" />
          <p className="text-xs font-medium text-slate-600">No active goals yet</p>
          <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
            Set a savings target for an emergency buffer, gadget, or DPS deposit.
          </p>
          <Link
            href="/goals"
            className="mt-3 inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            Create Goal
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-emerald-600" />
          <h3 className="text-sm font-bold text-slate-900">Active Goals</h3>
        </div>
        <Link
          href="/goals"
          className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700"
        >
          View all ({goals.length})
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="space-y-4 pt-1">
        {goals.slice(0, 3).map((goal) => {
          const isComplete = goal.progress_pct >= 1;
          return (
            <div
              key={goal.id}
              className="rounded-xl border border-slate-100 bg-slate-50/60 p-3.5 transition hover:bg-slate-50"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-xs font-bold text-slate-900 line-clamp-1">
                    {goal.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Target: {formatDate(goal.target_date)}
                  </p>
                </div>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                    isComplete
                      ? "bg-emerald-100 text-emerald-800"
                      : goal.is_feasible
                      ? "bg-blue-100 text-blue-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle2 className="h-3 w-3" />
                  ) : goal.is_feasible ? (
                    "On track"
                  ) : (
                    <AlertCircle className="h-3 w-3" />
                  )}
                  {formatPercent(goal.progress_pct, 0)}
                </span>
              </div>

              {/* Progress bar */}
              <div className="mt-2.5">
                <div className="flex justify-between text-[11px] text-slate-600 mb-1 font-medium">
                  <span>{formatBDT(goal.current_amount)}</span>
                  <span className="text-slate-400">of {formatBDT(goal.target_amount)}</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full bg-emerald-600 rounded-full transition-all duration-300"
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
