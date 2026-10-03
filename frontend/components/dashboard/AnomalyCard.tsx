"use client";

import React, { useState } from "react";
import { Anomaly } from "@/types/api";
import { formatBDT, formatPercent } from "@/lib/formatters";
import { AlertTriangle, Check, X, ShieldAlert } from "lucide-react";

interface AnomalyCardProps {
  anomalies: Anomaly[];
  onFeedback?: (id: string, status: "dismissed" | "confirmed") => Promise<void>;
}

export function AnomalyCard({ anomalies, onFeedback }: AnomalyCardProps) {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const pendingAnomalies = anomalies.filter((a) => a.status === "pending");

  if (pendingAnomalies.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-2 text-slate-800">
          <ShieldAlert className="h-4 w-4 text-emerald-600" />
          <h3 className="text-sm font-bold">Spending Anomaly Monitor</h3>
        </div>
        <div className="mt-3 rounded-xl bg-emerald-50/50 border border-emerald-100 p-4 text-xs text-emerald-800">
          <p className="font-semibold">No anomalous spending detected</p>
          <p className="mt-0.5 text-emerald-700/80">
            Your recent transactions align with your historical baseline and peer group patterns.
          </p>
        </div>
      </div>
    );
  }

  const handleAction = async (id: string, status: "dismissed" | "confirmed") => {
    if (!onFeedback) return;
    setLoadingId(id);
    try {
      await onFeedback(id, status);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-2 text-amber-600">
          <AlertTriangle className="h-4 w-4" />
          <h3 className="text-sm font-bold text-slate-900">
            Unusual Activity Detected ({pendingAnomalies.length})
          </h3>
        </div>
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
          Review Needed
        </span>
      </div>

      <div className="space-y-3 pt-1">
        {pendingAnomalies.slice(0, 2).map((item) => (
          <div
            key={item.id}
            className="rounded-xl border border-amber-200 bg-amber-50/40 p-3.5 text-xs"
          >
            <div className="flex justify-between items-start gap-2">
              <span className="font-bold text-slate-900 capitalize">
                {item.scope.replace(/_/g, " ")} spike
              </span>
              <span className="font-extrabold text-rose-600">
                +{formatPercent(item.deviation_pct)} above baseline
              </span>
            </div>

            <p className="mt-1 text-slate-600 leading-relaxed">
              {typeof item.explanation === "object"
                ? (item.explanation as any).reason || JSON.stringify(item.explanation)
                : item.explanation}
            </p>

            <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 border-t border-amber-200/50 pt-2">
              <span>Observed: {formatBDT(item.observed)}</span>
              <span>Baseline: {formatBDT(item.baseline)}</span>
            </div>

            <div className="mt-3 flex gap-2">
              <button
                disabled={loadingId === item.id}
                onClick={() => handleAction(item.id, "confirmed")}
                className="flex-1 inline-flex items-center justify-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                Legitimate Expense
              </button>
              <button
                disabled={loadingId === item.id}
                onClick={() => handleAction(item.id, "dismissed")}
                className="inline-flex items-center justify-center gap-1 rounded-lg bg-white border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                <X className="h-3.5 w-3.5 text-slate-500" />
                Dismiss
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
