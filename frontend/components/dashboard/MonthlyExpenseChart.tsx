"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { MonthlySummary } from "@/types/api";
import { formatBDT } from "@/lib/formatters";

interface MonthlyExpenseChartProps {
  data: MonthlySummary[];
}

export function MonthlyExpenseChart({ data }: MonthlyExpenseChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex min-h-[280px] items-center justify-center rounded-2xl overflow-hidden border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
        No monthly spending history available.
      </div>
    );
  }

  const chartData = data.map((d) => ({
    month: d.year_month.slice(5),
    fullMonth: d.year_month,
    income: d.total_income,
    expense: d.total_expense,
  }));

  return (
    <div className="rounded-2xl overflow-hidden border border-slate-200/80 bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
      <div className="flex items-center justify-between pb-3">
        <div>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Income vs Outflow</h3>
          <p className="text-xs text-slate-500 font-medium">Trailing monthly totals</p>
        </div>
      </div>

      <div className="min-h-[280px] w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              tickFormatter={(val) => `৳${Math.round(val / 1000)}k`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-navy-100 bg-white p-2.5 shadow-lg text-xs">
                      <p className="font-bold text-navy-900">{p.fullMonth}</p>
                      <p className="font-semibold text-navy-700 mt-1 tabular-nums">
                        Inflow: {formatBDT(p.income)}
                      </p>
                      <p className="font-semibold text-rose-600 tabular-nums">
                        Outflow: {formatBDT(p.expense)}
                      </p>
                      <p className="font-black text-navy-950 mt-1 border-t border-slate-100 pt-1 tabular-nums">
                        Net: {formatBDT(p.income - p.expense)}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ fontSize: 11, paddingBottom: 8 }}
            />
            <Bar dataKey="income" name="Income" fill="#0A1C3C" radius={[4, 4, 0, 0]} />
            <Bar dataKey="expense" name="Expense" fill="#f43f5e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
