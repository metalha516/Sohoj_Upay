"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import { Goal, GoalCreateRequest, GoalContributionRequest } from "@/types/api";
import { formatBDT, formatPercent, formatDate } from "@/lib/formatters";
import { AuthGuard } from "@/components/layout/AuthGuard";
import { useAuth } from "@/lib/auth-context";
import {
  Target,
  Plus,
  CheckCircle2,
  AlertCircle,
  PiggyBank,
  Calendar,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export default function GoalsPage() {
  return (
    <AuthGuard>
      <GoalsContent />
    </AuthGuard>
  );
}

function GoalsContent() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedGoalForFund, setSelectedGoalForFund] = useState<Goal | null>(null);

  // Create form
  const [title, setTitle] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [currentAmount, setCurrentAmount] = useState("0");
  const [targetDate, setTargetDate] = useState("2027-12-31");
  const [category, setCategory] = useState("emergency_fund");

  // Contribution form
  const [fundAmount, setFundAmount] = useState("");
  const [fundNote, setFundNote] = useState("");

  const { data: goals, isLoading, error } = useQuery({
    queryKey: ["goals"],
    queryFn: () => apiClient.listGoals(),
    enabled: !!user,
  });

  const createGoalMutation = useMutation({
    mutationFn: (req: GoalCreateRequest) => apiClient.createGoal(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
      setIsCreateOpen(false);
      setTitle("");
      setTargetAmount("");
    },
  });

  const contributeMutation = useMutation({
    mutationFn: ({ id, req }: { id: string; req: GoalContributionRequest }) =>
      apiClient.addGoalContribution(id, req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
      setSelectedGoalForFund(null);
      setFundAmount("");
    },
  });

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const tAmt = parseFloat(targetAmount);
    if (isNaN(tAmt) || tAmt <= 0) return;

    await createGoalMutation.mutateAsync({
      title: title.trim(),
      target_amount: tAmt,
      current_amount: parseFloat(currentAmount) || 0,
      target_date: targetDate,
      category,
    });
  };

  const handleFundSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGoalForFund) return;
    const fAmt = parseFloat(fundAmount);
    if (isNaN(fAmt) || fAmt <= 0) return;

    await contributeMutation.mutateAsync({
      id: selectedGoalForFund.id,
      req: {
        amount: fAmt,
        note: fundNote.trim() || undefined,
      },
    });
  };

  const goalList = goals || [];

  return (
    <div className="min-h-screen bg-slate-50 pb-20 md:pb-12">
      <AppHeader />

      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-navy-900">
              Financial Goals & Milestones
            </h1>
            <p className="mt-1 text-xs text-slate-500 font-medium">
              Deterministic progress calculations, monthly savings requirements, and feasibility metrics
            </p>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-navy-900 px-4 py-2 text-xs font-bold text-upay-yellow shadow-sm hover:bg-navy-800 transition border border-navy-800"
          >
            <Plus className="h-4 w-4 stroke-[3]" />
            Create New Goal
          </button>
        </div>

        {/* Goals Grid */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-56 rounded-2xl bg-slate-200" />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
            Failed to load financial goals.
          </div>
        )}

        {!isLoading && !error && goalList.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-12 text-center">
            <Target className="mx-auto h-12 w-12 text-slate-300" />
            <h3 className="mt-3 text-sm font-bold text-navy-900">
              No financial goals set yet
            </h3>
            <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto font-medium">
              Start building financial resilience by tracking emergency funds, device upgrades, or DPS milestones.
            </p>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-navy-900 px-4 py-2 text-xs font-bold text-upay-yellow hover:bg-navy-800 border border-navy-800 shadow-sm"
            >
              <Plus className="h-4 w-4" />
              Set First Goal
            </button>
          </div>
        )}

        {!isLoading && !error && goalList.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {goalList.map((g) => {
              const isAchieved = g.progress_pct >= 1;
              return (
                <div
                  key={g.id}
                  className="flex flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2">
                      <span className="rounded-lg bg-navy-900 px-2.5 py-0.5 text-[10px] font-black text-upay-yellow uppercase tracking-wide border border-navy-800 shadow-sm">
                        {g.category?.replace(/_/g, " ") || "Savings"}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                          isAchieved
                            ? "bg-navy-900 text-upay-yellow border border-navy-800"
                            : g.is_feasible
                            ? "bg-upay-yellow/20 text-navy-950 border border-upay-yellow/40"
                            : "bg-amber-100 text-amber-900 border border-amber-200"
                        }`}
                      >
                        {isAchieved ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-upay-yellow" />
                        ) : g.is_feasible ? (
                          "Feasible • "
                        ) : (
                          <>
                            <AlertCircle className="h-3.5 w-3.5" />
                            <span className="ml-1">At Risk • </span>
                          </>
                        )}
                        <span>{formatPercent(g.progress_pct, 0)}</span>
                      </span>
                    </div>

                    <h3 className="mt-3 text-base font-bold text-navy-900 line-clamp-1">
                      {g.title || (g as any).name}
                    </h3>

                    {/* Target and dates */}
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 font-medium">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      <span>Target: {formatDate(g.target_date)}</span>
                    </div>

                    {/* Progress Bar with Upay Yellow gradient */}
                    <div className="mt-5">
                      <div className="flex justify-between text-xs font-semibold mb-1.5">
                        <span className="text-navy-900 font-bold">
                          {formatBDT(g.current_amount)}
                        </span>
                        <span className="text-slate-400">
                          Target: {formatBDT(g.target_amount)}
                        </span>
                      </div>
                      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 p-0.5">
                        <div
                          className="h-full bg-gradient-to-r from-navy-900 via-[#1E3A8A] to-upay-yellow rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(100, g.progress_pct * 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Math breakdown */}
                    <div className="mt-4 grid grid-cols-2 gap-2 border-t border-slate-100 pt-3 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase font-bold">
                          Shortfall
                        </span>
                        <p className="font-bold text-slate-800">
                          {formatBDT(g.shortfall)}
                        </p>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase font-bold">
                          Required / Month
                        </span>
                        <p className="font-bold text-navy-950">
                          {formatBDT(g.required_monthly_saving)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Add Funds Button */}
                  <div className="mt-6 pt-3 border-t border-slate-100">
                    <button
                      onClick={() => setSelectedGoalForFund(g)}
                      className="w-full inline-flex items-center justify-center gap-1.5 rounded-xl bg-navy-900 py-2.5 text-xs font-bold text-white hover:bg-navy-800 transition shadow-sm"
                    >
                      <PiggyBank className="h-4 w-4 text-upay-yellow" />
                      Add Contribution
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* Create Goal Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-slate-100">
            <h2 className="text-base font-black text-navy-900 pb-3 border-b">
              Create Financial Goal
            </h2>
            <form onSubmit={handleCreateSubmit} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Goal Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="Emergency Buffer (3 Months)"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Target Amount (৳)
                </label>
                <input
                  type="number"
                  min="1000"
                  required
                  placeholder="50000"
                  value={targetAmount}
                  onChange={(e) => setTargetAmount(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Initial Saved Amount (৳)
                </label>
                <input
                  type="number"
                  min="0"
                  value={currentAmount}
                  onChange={(e) => setCurrentAmount(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Target Completion Date
                </label>
                <input
                  type="date"
                  required
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900"
                />
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="flex-1 rounded-xl border border-slate-300 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createGoalMutation.isPending}
                  className="flex-1 rounded-xl bg-navy-900 py-2.5 text-xs font-bold text-upay-yellow hover:bg-navy-800 border border-navy-800 shadow-sm"
                >
                  {createGoalMutation.isPending ? "Creating..." : "Save Goal"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Contribution Modal */}
      {selectedGoalForFund && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-slate-100">
            <h2 className="text-base font-black text-navy-900 pb-2 border-b">
              Contribute to &quot;{selectedGoalForFund.title}&quot;
            </h2>
            <form onSubmit={handleFundSubmit} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Deposit Amount (৳)
                </label>
                <input
                  type="number"
                  min="100"
                  step="100"
                  required
                  placeholder="2000"
                  value={fundAmount}
                  onChange={(e) => setFundAmount(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Deposit Note (Optional)
                </label>
                <input
                  type="text"
                  placeholder="Upay / MFS cash-in for monthly goal"
                  value={fundNote}
                  onChange={(e) => setFundNote(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900"
                />
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedGoalForFund(null)}
                  className="flex-1 rounded-xl border border-slate-300 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={contributeMutation.isPending}
                  className="flex-1 rounded-xl bg-navy-900 py-2.5 text-xs font-bold text-upay-yellow hover:bg-navy-800 border border-navy-800 shadow-sm"
                >
                  {contributeMutation.isPending ? "Recording..." : "Confirm Deposit"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <AppBottomNav />
    </div>
  );
}
