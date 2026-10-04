"use client";

import React from "react";
import { MonthlySummary } from "@/types/api";
import { formatBDT } from "@/lib/formatters";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { TrendingUp } from "lucide-react";

interface BehaviorTrendChartProps {
  data?: MonthlySummary[] | { months?: MonthlySummary[] } | null;
  isLoading?: boolean;
}

export function BehaviorTrendChart({ data, isLoading }: BehaviorTrendChartProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm animate-pulse h-80">
        <div className="h-5 w-48 bg-slate-200 rounded mb-4" />
        <div className="h-60 bg-slate-100 rounded" />
      </div>
    );
  }

  const list: MonthlySummary[] = Array.isArray(data)
    ? data
    : (data as any)?.months || [];

  if (list.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm text-center py-12 flex flex-col items-center justify-center h-80">
        <TrendingUp className="h-8 w-8 text-slate-300 mb-2" />
        <h4 className="text-sm font-semibold text-slate-700">No Historical Trends Available</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-xs">
          As you log transactions across upcoming months, your spending and savings trends will appear here.
        </p>
      </div>
    );
  }

  // Format month labels for Dhaka locale (e.g. "May", "Jun", "Jul")
  const chartData = list.map((item) => {
    const ym = item.year_month || (item as any).month || "2026-10";
    const [year, month] = ym.split("-");
    const dateObj = new Date(Number(year), Number(month) - 1, 1);
    const label = dateObj.toLocaleDateString("en-US", { month: "short" });

    return {
      monthLabel: label,
      necessity: Number(item.necessity_expense || 0),
      discretionary: Number(item.discretionary_expense || 0),
      savings: Math.max(0, Number(item.net_savings || 0)),
    };
  });

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-50 text-navy-900 border border-navy-100">
            <TrendingUp className="h-4 w-4 text-navy-900" />
          </div>
          <h3 className="text-base font-bold text-navy-900">Spending & Savings Allocation Trends</h3>
        </div>
        <span className="text-xs text-slate-500 font-medium">Trailing 6 Months</span>
      </div>

      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis dataKey="monthLabel" tickLine={false} tick={{ fontSize: 12, fill: "#64748B" }} />
            <YAxis
              tickLine={false}
              tick={{ fontSize: 11, fill: "#64748B" }}
              tickFormatter={(val) => `৳${(val / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={(value: any, name: any) => [
                formatBDT(Number(value)),
                name === "necessity"
                  ? "Necessity Expenses"
                  : name === "discretionary"
                  ? "Discretionary Expenses"
                  : "Net Savings",
              ]}
              contentStyle={{
                backgroundColor: "#FFFFFF",
                borderRadius: "12px",
                border: "1px solid #E2E8F0",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                fontSize: "12px",
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ fontSize: "12px", paddingBottom: "10px" }}
              formatter={(val) =>
                val === "necessity"
                  ? "Necessity"
                  : val === "discretionary"
                  ? "Discretionary"
                  : "Savings"
              }
            />
            <Bar dataKey="necessity" stackId="a" fill="#0A1C3C" radius={[0, 0, 0, 0]} />
            <Bar dataKey="discretionary" stackId="a" fill="#94A3B8" radius={[0, 0, 0, 0]} />
            <Bar dataKey="savings" stackId="a" fill="#FFC709" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
