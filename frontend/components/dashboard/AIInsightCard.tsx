"use client";

import React from "react";
import Link from "next/link";
import { BehaviorProfile, BehaviorInsights } from "@/types/api";
import { formatPercent } from "@/lib/formatters";
import { Lightbulb, Compass, ArrowRight, ShieldCheck } from "lucide-react";

interface AIInsightCardProps {
  profile?: BehaviorProfile | null;
  insights?: BehaviorInsights | null;
}

export function AIInsightCard({ profile, insights }: AIInsightCardProps) {
  const persona = profile?.persona_label || "Active Transactor";
  const confidence = profile?.confidence ?? 0.85;

  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <div className="rounded-xl bg-navy-900 p-1.5 text-upay-yellow shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
            <Compass className="h-4 w-4" aria-hidden="true" />
          </div>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Financial Persona</h3>
        </div>
        <div className="flex items-center gap-1 text-[11px] font-bold text-slate-600">
          <ShieldCheck className="h-3.5 w-3.5 text-navy-900" />
          <span>Private & Grounded</span>
        </div>
      </div>

      <div className="rounded-xl bg-navy-900 p-4 text-white border border-navy-800 shadow-inner">
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase tracking-wider text-upay-yellow font-extrabold">
            Behavior Archetype
          </span>
          <span className="rounded-full bg-navy-800 px-2 py-0.5 text-[10px] text-slate-200 border border-navy-700">
            {formatPercent(confidence)} match
          </span>
        </div>
        <h4 className="mt-1 text-lg font-black capitalize text-white">
          {persona.replace(/_/g, " ")}
        </h4>
        <p className="mt-1 text-xs text-slate-300 leading-relaxed font-medium">
          {profile?.description ||
            "Your transaction cadence exhibits consistent MFS spending with balanced necessity allocations."}
        </p>

        {/* Top factors */}
        {profile?.top_factors && Array.isArray(profile.top_factors) && profile.top_factors.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5 pt-2 border-t border-navy-800">
            {profile.top_factors.slice(0, 3).map((f: any, idx: number) => (
              <span
                key={f.factor || idx}
                className="rounded-md bg-navy-800/90 border border-navy-700/60 px-2 py-0.5 text-[10px] text-slate-200 font-medium"
              >
                {(f.factor || `factor_${idx}`).replace(/_/g, " ")}: {f.impact || "high"}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Actionable coaching nudge */}
      <div className="mt-3.5 rounded-xl border border-upay-yellow/40 bg-amber-50/50 p-3.5 text-xs text-navy-950">
        <div className="flex items-center gap-1.5 font-bold text-navy-900 mb-1">
          <Lightbulb className="h-4 w-4 text-amber-600" />
          <span>Personalized Coaching Nudge</span>
        </div>
        <p className="text-slate-700 leading-relaxed font-medium">
          {insights && typeof insights === "object" && "primary_recommendation" in insights
            ? (insights as any).primary_recommendation
            : "Maintaining an emergency buffer of 3 months expenses in a dedicated MFS savings pot can safeguard against unexpected cash-out fees."}
        </p>
      </div>
    </div>
  );
}
