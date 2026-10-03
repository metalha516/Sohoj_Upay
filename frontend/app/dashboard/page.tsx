"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import { BalanceCard } from "@/components/dashboard/BalanceCard";
import { IncomeCard } from "@/components/dashboard/IncomeCard";
import { ExpenseCard } from "@/components/dashboard/ExpenseCard";
import { SavingsCard } from "@/components/dashboard/SavingsCard";
import { SavingsRateChart } from "@/components/dashboard/SavingsRateChart";
import { ExpenseCategoryChart } from "@/components/dashboard/ExpenseCategoryChart";
import { MonthlyExpenseChart } from "@/components/dashboard/MonthlyExpenseChart";
import { FinancialGoalCard } from "@/components/dashboard/FinancialGoalCard";
import { ForecastCard } from "@/components/dashboard/ForecastCard";
import { AnomalyCard } from "@/components/dashboard/AnomalyCard";
import { AIInsightCard } from "@/components/dashboard/AIInsightCard";
import { CashOutPurposeModal } from "@/components/transactions/CashOutPurposeModal";
import { CashOutCreateRequest } from "@/types/api";
import { AlertCircle, RefreshCw, Sparkles } from "lucide-react";

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [isCashOutModalOpen, setIsCashOutModalOpen] = useState(false);

  // Queries
  const {
    data: overview,
    isLoading: isOverviewLoading,
    error: overviewError,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: () => apiClient.getDashboardOverview(),
  });

  const { data: forecast, isLoading: isForecastLoading } = useQuery({
    queryKey: ["spending-forecast"],
    queryFn: () => apiClient.getSpendingForecast().catch(() => null),
  });

  const { data: anomalies, refetch: refetchAnomalies } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () => apiClient.listAnomalies().catch(() => []),
  });

  const { data: profile } = useQuery({
    queryKey: ["behavior-profile"],
    queryFn: () => apiClient.getBehaviorProfile().catch(() => null),
  });

  const { data: insights } = useQuery({
    queryKey: ["behavior-insights"],
    queryFn: () => apiClient.getBehaviorInsights().catch(() => null),
  });

  // Cashout mutation
  const cashOutMutation = useMutation({
    mutationFn: (data: CashOutCreateRequest) => apiClient.createCashOut(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["anomalies"] });
    },
  });

  const handleCashOutSubmit = async (data: CashOutCreateRequest) => {
    await cashOutMutation.mutateAsync(data);
  };

  const handleAnomalyFeedback = async (id: string, status: "dismissed" | "confirmed") => {
    await apiClient.updateAnomalyStatus(id, { status });
    refetchAnomalies();
    refetchOverview();
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20 md:pb-12">
      <AppHeader />

      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-6">
        {/* Header Title & Refresh */}
        <div className="flex items-center justify-between pb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
              Financial Dashboard
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Live MFS telemetry, behavior archetypes, and spending intelligence
            </p>
          </div>
          <button
            onClick={() => {
              refetchOverview();
              refetchAnomalies();
            }}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-400"
            aria-label="Refresh Dashboard"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>

        {/* Error State */}
        {overviewError && (
          <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-800">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />
              <h2 className="text-sm font-bold">Unable to load dashboard data</h2>
            </div>
            <p className="mt-1 text-xs text-rose-700">
              {(overviewError as any)?.problem?.detail ||
                (overviewError as Error).message ||
                "Failed to communicate with backend."}
            </p>
            <button
              onClick={() => refetchOverview()}
              className="mt-3 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-500"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {isOverviewLoading && (
          <div className="space-y-6 animate-pulse">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="h-44 rounded-2xl bg-slate-200 md:col-span-2" />
              <div className="h-44 rounded-2xl bg-slate-200" />
              <div className="h-44 rounded-2xl bg-slate-200" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="h-72 rounded-2xl bg-slate-200" />
              <div className="h-72 rounded-2xl bg-slate-200" />
            </div>
          </div>
        )}

        {/* Dashboard Content */}
        {overview && (
          <div className="space-y-6">
            {/* Top Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              <div className="sm:col-span-2">
                <BalanceCard
                  balance={overview.current_balance}
                  onRecordCashOut={() => setIsCashOutModalOpen(true)}
                  onAddTransaction={() => setIsCashOutModalOpen(true)}
                />
              </div>
              <IncomeCard
                amount={overview.monthly_income}
                transactionCount={overview.recent_transactions?.length || 0}
              />
              <ExpenseCard
                amount={overview.monthly_expense}
                necessityRatio={overview.necessity_ratio}
              />
            </div>

            {/* Second Row: Savings & AI Forecast / Persona */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <SavingsCard
                savingsAmount={overview.monthly_savings}
                savingsRate={overview.savings_rate}
                emergencyFundMonths={overview.emergency_fund_months}
              />
              <ForecastCard forecast={forecast} isLoading={isForecastLoading} />
              <AIInsightCard profile={profile} insights={insights} />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <MonthlyExpenseChart data={overview.monthly_trend} />
              </div>
              <div>
                <ExpenseCategoryChart categories={overview.category_breakdown} />
              </div>
            </div>

            {/* Fourth Row: Goals, Savings Rate Trend & Anomalies */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div>
                <FinancialGoalCard goals={overview.active_goals} />
              </div>
              <div>
                <SavingsRateChart data={overview.monthly_trend} />
              </div>
              <div>
                <AnomalyCard
                  anomalies={anomalies || []}
                  onFeedback={handleAnomalyFeedback}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Mandatory Cash-Out Purpose Modal */}
      <CashOutPurposeModal
        isOpen={isCashOutModalOpen}
        onClose={() => setIsCashOutModalOpen(false)}
        onSubmit={handleCashOutSubmit}
      />

      <AppBottomNav />
    </div>
  );
}
