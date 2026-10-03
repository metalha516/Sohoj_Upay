"use client";

import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { CategoryBreakdown } from "@/types/api";
import { formatBDT, formatPercent } from "@/lib/formatters";

interface ExpenseCategoryChartProps {
  categories: CategoryBreakdown[];
}

const PALETTE = [
  "#0f766e", // teal-700
  "#0284c7", // sky-600
  "#e11d48", // rose-600
  "#d97706", // amber-600
  "#7c3aed", // violet-600
  "#059669", // emerald-600
  "#475569", // slate-600
  "#ea580c", // orange-600
];

export function ExpenseCategoryChart({ categories }: ExpenseCategoryChartProps) {
  if (!categories || categories.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
        No category spending recorded for this month.
      </div>
    );
  }

  // Top 6 categories + others
  const topCategories = categories.slice(0, 6);
  const otherAmount = categories
    .slice(6)
    .reduce((sum, item) => sum + item.total_amount, 0);

  const chartData = [
    ...topCategories.map((c) => ({
      name: c.category.replace(/_/g, " "),
      amount: c.total_amount,
      percentage: c.percentage,
    })),
    ...(otherAmount > 0
      ? [
          {
            name: "Other",
            amount: otherAmount,
            percentage: otherAmount / categories.reduce((s, c) => s + c.total_amount, 0),
          },
        ]
      : []),
  ];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between pb-2">
        <h3 className="text-sm font-bold text-slate-900">Spending by Category</h3>
        <span className="text-xs text-slate-500">Monthly breakdown</span>
      </div>

      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={72}
              paddingAngle={2}
              dataKey="amount"
            >
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-lg text-xs">
                      <p className="font-bold text-slate-800 capitalize">{p.name}</p>
                      <p className="text-slate-600 mt-0.5">{formatBDT(p.amount)}</p>
                      <p className="text-emerald-600 font-semibold">{formatPercent(p.percentage)}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Category Pills */}
      <div className="mt-3 flex flex-wrap gap-2 pt-2 border-t border-slate-100">
        {chartData.slice(0, 5).map((item, idx) => (
          <div key={item.name} className="flex items-center gap-1.5 text-xs text-slate-600">
            <span
              className="h-2.5 w-2.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: PALETTE[idx % PALETTE.length] }}
              aria-hidden="true"
            />
            <span className="capitalize truncate max-w-[100px]">{item.name}</span>
            <span className="font-semibold text-slate-900">{formatPercent(item.percentage, 0)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
