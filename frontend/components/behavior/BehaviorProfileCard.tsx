"use client";

import React from "react";
import { BehaviorProfile } from "@/types/api";
import { Sparkles, ShieldCheck, Calendar, Activity, AlertCircle } from "lucide-react";

interface BehaviorProfileCardProps {
  profile: BehaviorProfile | null;
  isLoading?: boolean;
}

const ARCHETYPE_METADATA: Record<string, { label: string; badgeColor: string; description: string }> = {
  disciplined_saver: {
    label: "Disciplined Saver",
    badgeColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
    description: "Consistent surplus accumulator with strong emergency fund protection and prudent discretionary outlays.",
  },
  emergency_vulnerable: {
    label: "Emergency Vulnerable",
    badgeColor: "bg-amber-100 text-amber-800 border-amber-200",
    description: "Living close to cash reserves with high necessity expenses and limited liquidity buffer against shocks.",
  },
  impulsive_spender: {
    label: "Impulsive Spender",
    badgeColor: "bg-rose-100 text-rose-800 border-rose-200",
    description: "Elevated discretionary cash-outs and variable month-to-month outflow spikes.",
  },
  balanced_optimizer: {
    label: "Balanced Optimizer",
    badgeColor: "bg-blue-100 text-blue-800 border-blue-200",
    description: "Maintains sustainable necessity-to-savings ratios with conscious cash-out planning.",
  },
};

export function BehaviorProfileCard({ profile, isLoading }: BehaviorProfileCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm animate-pulse">
        <div className="h-6 w-48 bg-slate-200 rounded mb-4" />
        <div className="h-4 w-full bg-slate-100 rounded mb-2" />
        <div className="h-4 w-3/4 bg-slate-100 rounded" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-sm font-bold">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">Balanced Optimizer</h2>
              <span className="rounded-full border border-blue-200 bg-blue-100 text-blue-800 px-2.5 py-0.5 text-xs font-semibold">
                Cold-Start Baseline
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Personalized behavioral persona will calibrate dynamically as monthly transactions are recorded.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const archetypeKey = (profile.profile || profile.persona_label || "balanced_optimizer").toLowerCase();
  const meta = ARCHETYPE_METADATA[archetypeKey] || {
    label: profile.profile.replace(/_/g, " "),
    badgeColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
    description: profile.description || "Active financial behavioral archetype.",
  };

  const confidencePct = Math.round((Number(profile.confidence) || 0.85) * 100);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-sm font-bold">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">{meta.label}</h2>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${meta.badgeColor}`}>
                Active Archetype
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Personalized behavioral persona derived from MFS cash flow telemetry
            </p>
          </div>
        </div>

        {/* Confidence & Model Version Badges */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-xl bg-slate-50 border border-slate-200 px-3 py-1.5 text-xs">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span className="font-semibold text-slate-800">{confidencePct}%</span>
            <span className="text-slate-500">Confidence</span>
          </div>

          {profile.model_version && (
            <div className="rounded-xl bg-slate-50 border border-slate-200 px-2.5 py-1.5 text-xs font-mono text-slate-600">
              {profile.model_version}
            </div>
          )}
        </div>
      </div>

      {/* Description & Cold Start Warning */}
      <div className="mt-4">
        <p className="text-sm text-slate-700 leading-relaxed">{meta.description}</p>

        {profile.is_cold_start && (
          <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-blue-200 bg-blue-50/80 p-3 text-xs text-blue-900">
            <AlertCircle className="h-4 w-4 shrink-0 text-blue-600" />
            <span>
              <strong>Cold-Start Persona:</strong> You have fewer than 2 complete billing cycles. Archetype confidence will recalibrate dynamically as more transactions are recorded.
            </span>
          </div>
        )}
      </div>

      {/* Metadata bar */}
      <div className="mt-5 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2">
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5 text-slate-400" />
          <span>Evaluated as of: <strong>{profile.as_of_month || "October 2026"}</strong></span>
        </div>
        <div className="flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-slate-400" />
          <span>Model refresh frequency: <strong>Debounced (1 per 15m)</strong></span>
        </div>
      </div>
    </div>
  );
}
