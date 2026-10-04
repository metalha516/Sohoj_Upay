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
      <div className="flex min-h-[280px] items-center justify-center rounded-2xl overflow-hidden border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
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
    <div className="rounded-2xl overflow-hidden border border-slate-200/80 bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
      <div className="flex items-center justify-between pb-3">
        <div>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Savings Rate Trend</h3>
          <p className="text-xs text-slate-500 font-medium">Trailing months vs 20% benchmark</p>
        </div>
        <span className="rounded-full bg-upay-yellow/20 px-2.5 py-0.5 text-xs font-bold text-navy-950 border border-upay-yellow/40">
          Target: 20%
        </span>
      </div>

      <div className="min-h-[280px] w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="rateGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#FFC709" stopOpacity={0.45} />
                <stop offset="95%" stopColor="#FFC709" stopOpacity={0.02} />
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
                    <div className="rounded-xl border border-navy-100 bg-white p-2.5 shadow-lg text-xs">
                      <p className="font-bold text-navy-900">{p.fullMonth}</p>
                      <p className="font-black text-navy-950 mt-1 tabular-nums">
                        Rate: <span className="text-amber-600">{formatPercent(p.rate / 100)}</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine
              y={20}
              stroke="#0A1C3C"
              strokeDasharray="3 3"
              label={{
                value: "20% Goal",
                fill: "#0A1C3C",
                fontSize: 10,
                position: "right",
              }}
            />
            <Area
              type="monotone"
              dataKey="rate"
              stroke="#FFC709"
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
