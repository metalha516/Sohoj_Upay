"use client";

import React, { useState, useEffect, useTransition } from "react";
import { apiClient } from "@/lib/api-client";
import { GrowthSimulationResponse, DoublingSimulationResponse } from "@/types/api";
import { formatBDT, formatPercent } from "@/lib/formatters";
import {
  Calculator,
  TrendingUp,
  AlertCircle,
  HelpCircle,
  Sparkles,
  ShieldAlert,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export function SimulatorView() {
  const [principal, setPrincipal] = useState<number>(10000);
  const [monthlyContribution, setMonthlyContribution] = useState<number>(5000);
  const [annualRate, setAnnualRate] = useState<number>(8.0);
  const [years, setYears] = useState<number>(5);

  const [growthResult, setGrowthResult] = useState<GrowthSimulationResponse | null>(null);
  const [doublingResult, setDoublingResult] = useState<DoublingSimulationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Debounced API call to /simulate/growth and /simulate/doubling
  useEffect(() => {
    let isCurrent = true;
    const timer = setTimeout(async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [growthRes, doublingRes] = await Promise.all([
          apiClient.simulateGrowth({
            principal,
            monthly_contribution: monthlyContribution,
            annual_rate_percent: annualRate,
            years,
            compounding_per_year: 12,
            rate_type: "assumed",
          }),
          apiClient.simulateDoubling({
            annual_rate_percent: annualRate,
            rate_type: "assumed",
          }),
        ]);

        if (isCurrent) {
          setGrowthResult(growthRes);
          setDoublingResult(doublingRes);
        }
      } catch (err: any) {
        if (isCurrent) {
          setError(err.message || "Failed to calculate simulation");
        }
      } finally {
        if (isCurrent) setIsLoading(false);
      }
    }, 250); // 250ms debounce

    return () => {
      isCurrent = false;
      clearTimeout(timer);
    };
  }, [principal, monthlyContribution, annualRate, years]);

  const chartData = growthResult?.series?.map((pt) => ({
    year: `Yr ${pt.year}`,
    balance: pt.balance,
    contributed: pt.total_contributed,
    growth: pt.total_growth,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Top Banner with Assumed Rate Badge */}
      <div className="relative overflow-hidden flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl bg-gradient-to-br from-navy-900 via-[#0A1C3C] to-navy-950 p-6 text-white shadow-lg border border-navy-800">
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-upay-yellow/10 blur-3xl" />

        <div className="relative z-10">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-navy-800/80 border border-navy-700/80 text-upay-yellow shadow-inner">
              <Calculator className="h-5 w-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              Deterministic Wealth Simulator
            </h1>
          </div>
          <p className="mt-2 text-xs text-slate-300 max-w-xl font-medium">
            Pure compound interest calculations executed strictly by our backend Financial
            Engine with high-precision Decimal arithmetic.
          </p>
        </div>

        {/* ALWAYS VISIBLE: Assumed-rate badge */}
        <div className="relative z-10 flex items-center gap-2 self-start sm:self-auto rounded-xl bg-navy-800/90 border border-upay-yellow/40 px-3.5 py-2 text-upay-yellow shadow-inner">
          <ShieldAlert className="h-4 w-4 flex-shrink-0 text-upay-yellow" />
          <div className="text-left">
            <span className="block text-xs font-black uppercase tracking-wider text-upay-yellow">
              Assumed-Rate Badge
            </span>
            <span className="text-[11px] text-slate-300 font-medium">
              Projections not guaranteed
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid: Controls on left, Results & Charts on right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <div className="lg:col-span-5 space-y-5 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-bold uppercase tracking-wider text-navy-900 pb-2 border-b border-slate-100">
            Simulation Parameters
          </h2>

          {/* Initial Principal Slider */}
          <div>
            <div className="flex justify-between items-center text-xs mb-2">
              <label htmlFor="principal-slider" className="font-bold text-navy-900">
                Initial Deposit
              </label>
              <span className="font-black text-navy-900 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/60">
                {formatBDT(principal)}
              </span>
            </div>
            <input
              id="principal-slider"
              type="range"
              min="0"
              max="200000"
              step="5000"
              value={principal}
              onChange={(e) => setPrincipal(Number(e.target.value))}
              className="w-full accent-[#FFC709] cursor-pointer h-2 bg-slate-200 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
              <span>৳0</span>
              <span>৳1,00,000</span>
              <span>৳2,00,000</span>
            </div>
          </div>

          {/* Monthly Saving Slider: ৳2,000 to ৳10,000 required range */}
          <div>
            <div className="flex justify-between items-center text-xs mb-2">
              <label htmlFor="monthly-saving-slider" className="font-bold text-navy-900">
                Monthly Saving
              </label>
              <span className="font-black text-navy-950 bg-upay-yellow/20 px-2.5 py-1 rounded-lg border border-upay-yellow/50">
                {formatBDT(monthlyContribution)} / mo
              </span>
            </div>
            <input
              id="monthly-saving-slider"
              type="range"
              min="2000"
              max="10000"
              step="500"
              value={monthlyContribution}
              onChange={(e) => setMonthlyContribution(Number(e.target.value))}
              className="w-full accent-[#FFC709] cursor-pointer h-2 bg-slate-200 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
              <span>৳2,000 (Min)</span>
              <span>৳6,000</span>
              <span>৳10,000 (Max)</span>
            </div>
          </div>

          {/* Assumed Annual Return Rate Slider: 2% to 12% required range */}
          <div>
            <div className="flex justify-between items-center text-xs mb-2">
              <div className="flex items-center gap-1.5">
                <label htmlFor="rate-slider" className="font-bold text-navy-900">
                  Assumed Annual Rate
                </label>
                <span className="text-[10px] font-bold text-amber-900 bg-amber-100 px-1.5 py-0.5 rounded border border-amber-200">
                  Assumed
                </span>
              </div>
              <span className="font-black text-navy-900 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/60">
                {annualRate.toFixed(1)}% p.a.
              </span>
            </div>
            <input
              id="rate-slider"
              type="range"
              min="2.0"
              max="12.0"
              step="0.5"
              value={annualRate}
              onChange={(e) => setAnnualRate(Number(e.target.value))}
              className="w-full accent-[#FFC709] cursor-pointer h-2 bg-slate-200 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
              <span>2.0% (Savings)</span>
              <span>7.0% (DPS/FDR)</span>
              <span>12.0% (Equity)</span>
            </div>
          </div>

          {/* Horizon Years Slider: 1 to 15 years required range */}
          <div>
            <div className="flex justify-between items-center text-xs mb-2">
              <label htmlFor="years-slider" className="font-bold text-navy-900">
                Horizon
              </label>
              <span className="font-black text-navy-900 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/60">
                {years} {years === 1 ? "Year" : "Years"}
              </span>
            </div>
            <input
              id="years-slider"
              type="range"
              min="1"
              max="15"
              step="1"
              value={years}
              onChange={(e) => setYears(Number(e.target.value))}
              className="w-full accent-[#FFC709] cursor-pointer h-2 bg-slate-200 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
              <span>1 Year</span>
              <span>7 Years</span>
              <span>15 Years</span>
            </div>
          </div>

          {/* Doubling Time Rule of 72 Badge */}
          {doublingResult && (
            <div className="rounded-xl border border-navy-100 bg-navy-50/60 p-3.5 text-xs">
              <div className="flex items-center justify-between text-navy-900">
                <span className="font-semibold text-slate-700">Rule of 72 Doubling Time:</span>
                <span className="font-black text-navy-950">
                  ~{doublingResult.years_rule_of_72.toFixed(1)} years
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-500 font-medium">
                Exact log compounding: {doublingResult.years_exact.toFixed(2)} years at{" "}
                {annualRate}%
              </p>
            </div>
          )}
        </div>

        {/* Results & Visuals Column */}
        <div className="lg:col-span-7 space-y-5">
          {/* 3 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div className="rounded-2xl border border-navy-800 bg-gradient-to-br from-navy-900 to-navy-950 p-4 shadow-md text-white transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Projected Future Value
              </span>
              <div className="mt-1 text-2xl font-black text-upay-yellow drop-shadow-sm">
                {growthResult ? formatBDT(growthResult.future_value) : "—"}
              </div>
              <span className="text-[10px] text-slate-400 font-medium">After {years} years</span>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Total Contributed
              </span>
              <div className="mt-1 text-xl font-black text-navy-900">
                {growthResult ? formatBDT(growthResult.total_contributed) : "—"}
              </div>
              <span className="text-[10px] text-slate-400 font-medium">Your deposits</span>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Compound Growth
              </span>
              <div className="mt-1 text-xl font-black text-navy-900">
                {growthResult ? formatBDT(growthResult.total_growth) : "—"}
              </div>
              <span className="text-[10px] text-amber-600 font-bold">Interest earned</span>
            </div>
          </div>

          {/* Growth Area Chart */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-navy-900">
                  Wealth Accumulation Curve
                </h3>
                <p className="text-xs text-slate-500 font-medium">
                  Principal contributions vs compound interest
                </p>
              </div>
              <span className="text-xs font-bold text-navy-900 bg-navy-50 border border-navy-100 px-2.5 py-1 rounded-full">
                {isLoading ? "Calculating..." : "Backend Verified"}
              </span>
            </div>

            <div className="h-64 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={chartData}
                  margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="balanceGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FFC709" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#FFC709" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="contribGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0A1C3C" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#0A1C3C" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="year" stroke="#94a3b8" fontSize={11} tickLine={false} />
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
                          <div className="rounded-xl border border-navy-100 bg-white p-3 shadow-lg text-xs space-y-1">
                            <p className="font-black text-navy-950">{p.year}</p>
                            <p className="text-navy-900 font-bold">
                              Total Balance: <span className="text-amber-600">{formatBDT(p.balance)}</span>
                            </p>
                            <p className="text-slate-600 font-medium">
                              Contributed: {formatBDT(p.contributed)}
                            </p>
                            <p className="text-slate-700 font-semibold">
                              Interest: {formatBDT(p.growth)}
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
                    wrapperStyle={{ fontSize: 11, paddingBottom: 10 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="balance"
                    name="Total Value"
                    stroke="#FFC709"
                    strokeWidth={2.5}
                    fill="url(#balanceGrad)"
                  />
                  <Area
                    type="monotone"
                    dataKey="contributed"
                    name="Contributed"
                    stroke="#0A1C3C"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    fill="url(#contribGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Statutory Disclaimer */}
            <p className="mt-4 text-[11px] text-slate-400 border-t border-slate-100 pt-3">
              {growthResult?.disclaimer ||
                "Projection based on an assumed rate; not guaranteed. Past performance or assumed returns do not represent future contractual certainty."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
