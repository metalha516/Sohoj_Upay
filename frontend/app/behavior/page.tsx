"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import { BehaviorProfileCard } from "@/components/behavior/BehaviorProfileCard";
import { FactorBarsCard } from "@/components/behavior/FactorBarsCard";
import { BehaviorTrendChart } from "@/components/behavior/BehaviorTrendChart";
import { AnomalyListTable } from "@/components/behavior/AnomalyListTable";
import { BehaviorInsightsList } from "@/components/behavior/BehaviorInsightsList";
import { apiClient } from "@/lib/api-client";
import { Sparkles, Brain, AlertTriangle } from "lucide-react";

export default function BehaviorPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["behavior-profile"],
    queryFn: () => apiClient.getBehaviorProfile(),
    enabled: isAuthenticated,
  });

  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ["behavior-insights"],
    queryFn: () => apiClient.getBehaviorInsights(),
    enabled: isAuthenticated,
  });

  const { data: anomalies, isLoading: anomaliesLoading } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () => apiClient.listAnomalies(),
    enabled: isAuthenticated,
  });

  const { data: monthlyTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ["monthly-trends", 6],
    queryFn: () => apiClient.getMonthlyTrends(6),
    enabled: isAuthenticated,
  });

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-20 md:pb-12">
      <AppHeader />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        {/* Page Title & Intro */}
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-100 text-purple-700">
              <Brain className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                Behavior & Anomaly Intelligence
              </h1>
              <p className="text-sm text-slate-500">
                Calibrated financial archetype, explainability drivers, and outlier detection
              </p>
            </div>
          </div>
        </div>

        {/* Top Section: Profile Card */}
        <BehaviorProfileCard profile={profile || null} isLoading={profileLoading} />

        {/* Middle Section: Explainability Factors & Spending Trends */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <FactorBarsCard profile={profile || null} isLoading={profileLoading} />
          <BehaviorTrendChart data={monthlyTrends || []} isLoading={trendsLoading} />
        </div>

        {/* Bottom Section: Anomalies List & Behavioral Coaching Insights */}
        <div className="space-y-8">
          <AnomalyListTable initialAnomalies={anomalies || []} isLoading={anomaliesLoading} />
          <BehaviorInsightsList insightsData={insights || null} isLoading={insightsLoading} />
        </div>
      </main>

      <AppBottomNav />
    </div>
  );
}
