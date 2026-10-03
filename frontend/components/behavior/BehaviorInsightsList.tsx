"use client";

import React from "react";
import { BehaviorInsights, BehaviorInsightItem } from "@/types/api";
import { Lightbulb, Tag, CheckCircle2, Bookmark, ArrowRight } from "lucide-react";
import Link from "next/link";

interface BehaviorInsightsListProps {
  insightsData: BehaviorInsights | null;
  isLoading?: boolean;
}

export function BehaviorInsightsList({ insightsData, isLoading }: BehaviorInsightsListProps) {
  if (isLoading || !insightsData) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm animate-pulse">
        <div className="h-5 w-48 bg-slate-200 rounded mb-4" />
        <div className="space-y-3">
          <div className="h-16 bg-slate-100 rounded-xl" />
          <div className="h-16 bg-slate-100 rounded-xl" />
        </div>
      </div>
    );
  }

  const items: BehaviorInsightItem[] = insightsData.insights || [];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-amber-500" />
          <h3 className="text-base font-bold text-slate-900">Personalized Coaching Insights</h3>
        </div>
        <span className="text-xs text-slate-500">Non-judgmental & Grounded</span>
      </div>

      <div className="space-y-4">
        {items.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">
            No specific recommendations at this time. Keep tracking expenses!
          </p>
        ) : (
          items.map((item) => {
            const isHighPriority = item.priority <= 1;
            return (
              <div
                key={item.id}
                className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 transition-all hover:bg-slate-50"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        isHighPriority
                          ? "bg-amber-100 text-amber-900 border border-amber-200"
                          : "bg-blue-50 text-blue-800 border border-blue-200"
                      }`}
                    >
                      {item.type.replace(/_/g, " ")}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                  </div>

                  {item.source_refs && (
                    <div className="flex items-center gap-1 text-[11px] text-slate-400">
                      <Bookmark className="h-3 w-3" />
                      <span>Grounded in monthly aggregates</span>
                    </div>
                  )}
                </div>

                <p className="text-xs text-slate-600 leading-relaxed mb-3">{item.content}</p>

                <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 text-xs">
                  <span className="text-slate-400 text-[11px]">
                    Recommendation #{item.priority}
                  </span>

                  <Link
                    href="/coach"
                    className="inline-flex items-center gap-1 text-emerald-700 font-semibold hover:text-emerald-800 transition-colors"
                  >
                    <span>Ask Coach about this</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
