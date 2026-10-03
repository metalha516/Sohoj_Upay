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
      <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
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
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Income vs Outflow</h3>
          <p className="text-xs text-slate-500">Trailing monthly totals</p>
        </div>
      </div>

      <div className="h-56 w-full pt-2">
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
                    <div className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-lg text-xs">
                      <p className="font-semibold text-slate-700">{p.fullMonth}</p>
                      <p className="font-medium text-emerald-600 mt-1">
                        Inflow: {formatBDT(p.income)}
                      </p>
                      <p className="font-medium text-rose-600">
                        Outflow: {formatBDT(p.expense)}
                      </p>
                      <p className="font-bold text-slate-800 mt-1 border-t pt-1">
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
            <Bar dataKey="income" name="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="expense" name="Expense" fill="#f43f5e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
