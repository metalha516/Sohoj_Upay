"use client";

import React from "react";
import { SpendingForecast } from "@/types/api";
import { formatBDT, formatPercent } from "@/lib/formatters";
import { Sparkles, Info, HelpCircle } from "lucide-react";

interface ForecastCardProps {
  forecast?: SpendingForecast | null;
  isLoading?: boolean;
}

export function ForecastCard({ forecast, isLoading = false }: ForecastCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm animate-pulse">
        <div className="h-4 w-32 bg-slate-200 rounded mb-4" />
        <div className="h-8 w-44 bg-slate-200 rounded mb-2" />
        <div className="h-3 w-56 bg-slate-100 rounded" />
      </div>
    );
  }

  if (!forecast) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-2 text-slate-700">
          <Sparkles className="h-4 w-4 text-upay-yellow" />
          <h3 className="text-sm font-bold">Expense Forecast</h3>
        </div>
        <div className="mt-3 rounded-xl bg-slate-50 p-4 border border-dashed border-slate-200 text-xs text-slate-500">
          <p className="font-medium text-slate-700">Forecast Pending</p>
          <p className="mt-1">
            Need at least 2 months of historical MFS activity to build an expense forecast.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <div className="rounded-xl bg-navy-900 p-1.5 text-upay-yellow shadow-sm">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          </div>
          <h3 className="text-sm font-bold text-navy-900">Next Month Expense Forecast</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 font-mono">
          {forecast.model_version}
        </span>
      </div>

      <div className="mt-2">
        <div className="text-2xl font-black tracking-tight text-navy-900">
          {formatBDT(forecast.predicted_expense)}
        </div>
        
        {/* Interval range */}
        <div className="mt-2.5 rounded-xl bg-navy-50/80 border border-navy-100/90 p-2.5 text-xs">
          <div className="flex justify-between items-center text-navy-900 font-medium">
            <span className="text-slate-600 font-semibold">80% Confidence Interval:</span>
            <span className="font-bold text-navy-950">
              {formatBDT(forecast.interval_p10)} – {formatBDT(forecast.interval_p90)}
            </span>
          </div>
        </div>

        {/* Confidence metric */}
        <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1">
            Confidence score:{" "}
            <strong className="text-slate-800">
              {formatPercent(forecast.confidence)}
            </strong>
          </span>
          <span className="text-[10px] text-slate-400">LightGBM Model C</span>
        </div>

        {/* Disclaimer */}
        <p className="mt-2 text-[10px] text-slate-400 leading-tight">
          {forecast.disclaimer ||
            "Projection based on an assumed machine learning estimate; not guaranteed."}
        </p>
      </div>
    </div>
  );
}
