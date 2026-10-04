"use client";

import React, { useState } from "react";
import { Anomaly } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { formatBDT } from "@/lib/formatters";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  ShieldAlert,
  ArrowUpRight,
  Sliders,
  Check,
} from "lucide-react";

interface AnomalyListTableProps {
  initialAnomalies: Anomaly[];
  isLoading?: boolean;
}

export function AnomalyListTable({ initialAnomalies, isLoading }: AnomalyListTableProps) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>(initialAnomalies);
  const [filter, setFilter] = useState<"all" | "open" | "confirmed" | "dismissed">("all");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Sync state if initialAnomalies changes
  React.useEffect(() => {
    setAnomalies(initialAnomalies);
  }, [initialAnomalies]);

  const handleUpdateStatus = async (id: string, status: "confirmed" | "dismissed") => {
    try {
      setActionLoading(id);
      await apiClient.updateAnomalyStatus(id, { status });
      setAnomalies((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status } : a))
      );
    } catch (e) {
      console.error("Failed to update anomaly status", e);
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = anomalies.filter((a) => {
    if (filter === "all") return true;
    if (filter === "open") return a.status === "open" || a.status === "pending";
    return a.status === filter;
  });

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition hover:shadow-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-rose-600" />
          <div>
            <h3 className="text-base font-bold text-navy-900">Detected Spending Anomalies</h3>
            <p className="text-xs text-slate-500 font-medium">
              Unsupervised statistical and Isolation Forest flags with your feedback history
            </p>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
          {(["all", "open", "confirmed", "dismissed"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1 rounded-lg capitalize transition-all ${
                filter === tab
                  ? "bg-navy-900 text-upay-yellow shadow-sm font-bold"
                  : "text-slate-600 hover:text-navy-900"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3 py-4">
          <div className="h-16 bg-slate-100 rounded-xl animate-pulse" />
          <div className="h-16 bg-slate-100 rounded-xl animate-pulse" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-navy-50 text-navy-900 border border-navy-100 mx-auto mb-3">
            <CheckCircle className="h-6 w-6 text-navy-900" />
          </div>
          <h4 className="text-sm font-bold text-navy-900">No Anomalies Found</h4>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            {filter === "all"
              ? "All your recent cash-outs and card outlays align with your baseline spending distributions."
              : `No anomalies currently marked as "${filter}".`}
          </p>
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {filtered.map((anomaly) => {
            const observed = Number(anomaly.observed_value ?? anomaly.observed ?? 0);
            const baseline = Number(anomaly.baseline_value ?? anomaly.baseline ?? 0);
            const deviation = Number(anomaly.deviation_pct ?? 0);
            const confidencePct = Math.round((Number(anomaly.confidence) || 0.88) * 100);
            const explanationText =
              typeof anomaly.explanation === "object"
                ? anomaly.explanation.reason || JSON.stringify(anomaly.explanation)
                : anomaly.explanation || "Outlier spending detected relative to historical baseline.";

            const isOpen = anomaly.status === "open" || anomaly.status === "pending";

            return (
              <div key={anomaly.id} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {(() => {
                      const rawScope = anomaly.category || anomaly.scope.replace(/_/g, " ");
                      const titleScope = rawScope ? rawScope.charAt(0).toUpperCase() + rawScope.slice(1) : "";
                      return (
                        <span className="font-semibold text-sm text-slate-900">
                          {titleScope} Outlier
                        </span>
                      );
                    })()}
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                        isOpen
                          ? "bg-rose-100 text-rose-800"
                          : anomaly.status === "confirmed"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {isOpen ? "Open Anomaly" : anomaly.status === "confirmed" ? "Confirmed Outlier" : "Dismissed"}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                      {confidencePct}% Confidence
                    </span>
                    {anomaly.model_version && (
                      <span className="text-[11px] font-mono text-slate-400">
                        {anomaly.model_version}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{explanationText}</p>

                  <div className="flex items-center gap-4 text-xs pt-1 text-slate-500">
                    <div>
                      Observed: <strong className="text-slate-900">{formatBDT(observed)}</strong>
                    </div>
                    <div>
                      Baseline: <strong className="text-slate-700">{formatBDT(baseline)}</strong>
                    </div>
                    <div className="flex items-center text-rose-600 font-semibold">
                      <ArrowUpRight className="h-3.5 w-3.5" />
                      <span>+{deviation.toFixed(0)}% deviation</span>
                    </div>
                  </div>
                </div>

                {/* Feedback Action Buttons */}
                <div className="flex items-center gap-2 shrink-0">
                  {isOpen ? (
                    <>
                      <button
                        onClick={() => handleUpdateStatus(anomaly.id, "confirmed")}
                        disabled={actionLoading === anomaly.id}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-navy-800 bg-navy-900 px-3 py-1.5 text-xs font-bold text-upay-yellow hover:bg-navy-800 focus:outline-none focus:ring-2 focus:ring-navy-900 disabled:opacity-50 transition-colors shadow-sm"
                      >
                        <Check className="h-3.5 w-3.5 text-upay-yellow" />
                        <span>Confirm Outlier</span>
                      </button>

                      <button
                        onClick={() => handleUpdateStatus(anomaly.id, "dismissed")}
                        disabled={actionLoading === anomaly.id}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:opacity-50 transition-colors"
                      >
                        <XCircle className="h-3.5 w-3.5 text-slate-500" />
                        <span>Dismiss</span>
                      </button>
                    </>
                  ) : (
                    <span className="text-xs text-slate-400 italic">
                      Feedback recorded ({anomaly.status})
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
