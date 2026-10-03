"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { MonthlySummary } from "@/types/api";
import { formatPercent } from "@/lib/formatters";

interface SavingsRateChartProps {
  data: MonthlySummary[];
}

export function SavingsRateChart({ data }: SavingsRateChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
        No savings rate history available yet.
      </div>
    );
  }

  const chartData = data.map((item) => ({
    month: item.year_month.slice(5), // "2026-05" -> "05"
    fullMonth: item.year_month,
    rate: Number((Number(item.savings_rate || 0) * 100).toFixed(1)),
  }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Savings Rate Trend</h3>
          <p className="text-xs text-slate-500">Trailing months vs 20% benchmark</p>
        </div>
        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">
          Target: 20%
        </span>
      </div>

      <div className="h-52 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="rateGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              tickFormatter={(val) => `${val}%`}
              domain={[0, "auto"]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0].payload;
                  return (
                    <div className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-lg text-xs">
                      <p className="font-semibold text-slate-700">{p.fullMonth}</p>
                      <p className="font-bold text-emerald-600 mt-1">
                        Rate: {formatPercent(p.rate / 100)}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine
              y={20}
              stroke="#059669"
              strokeDasharray="3 3"
              label={{
                value: "20% Goal",
                fill: "#059669",
                fontSize: 10,
                position: "right",
              }}
            />
            <Area
              type="monotone"
              dataKey="rate"
              stroke="#10b981"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#rateGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
