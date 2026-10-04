"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import { CashOutPurposeModal } from "@/components/transactions/CashOutPurposeModal";
import {
  CashOutCreateRequest,
  TransactionCreateRequest,
  TransactionType,
  Purpose,
} from "@/types/api";
import { formatBDT, formatDateTime } from "@/lib/formatters";
import {
  Receipt,
  ArrowDownLeft,
  ArrowUpRight,
  Filter,
  Plus,
  RefreshCw,
  Search,
} from "lucide-react";

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const [filterType, setFilterType] = useState<string>("all");
  const [isCashOutModalOpen, setIsCashOutModalOpen] = useState<boolean>(false);
  const [isAddTxnModalOpen, setIsAddTxnModalOpen] = useState<boolean>(false);

  // Add Transaction Modal state
  const [newAmount, setNewAmount] = useState("");
  const [newType, setNewType] = useState<TransactionType>("cash_in");
  const [newPurpose, setNewPurpose] = useState<Purpose>("necessity");
  const [newCategory, setNewCategory] = useState("salary_deposit");
  const [newProvider, setNewProvider] = useState<"upay" | "bkash" | "nagad" | "rocket">("upay");
  const [newDesc, setNewDesc] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["transactions", filterType],
    queryFn: () =>
      apiClient.listTransactions({
        transaction_type: filterType === "all" ? undefined : filterType,
        limit: 50,
      }),
  });

  const cashOutMutation = useMutation({
    mutationFn: (req: CashOutCreateRequest) => apiClient.createCashOut(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
    },
  });

  const addTxnMutation = useMutation({
    mutationFn: (req: TransactionCreateRequest) => apiClient.createTransaction(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
      setIsAddTxnModalOpen(false);
      setNewAmount("");
      setNewDesc("");
    },
  });

  const handleCashOutSubmit = async (req: CashOutCreateRequest) => {
    await cashOutMutation.mutateAsync(req);
  };

  const handleAddTxnSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsedAmount = parseFloat(newAmount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) return;

    await addTxnMutation.mutateAsync({
      amount: parsedAmount,
      transaction_type: newType,
      purpose: newPurpose,
      category: newCategory,
      mfs_provider: newProvider,
      description: newDesc.trim() || undefined,
    });
  };

  const items = data?.items || [];

  return (
    <div className="min-h-screen bg-slate-50 pb-20 md:pb-12">
      <AppHeader />

      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-navy-900">
              Transactions Ledger
            </h1>
            <p className="mt-1 text-xs text-slate-500 font-medium">
              Complete history of cash-in, cash-outs, payments, and transfers
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsCashOutModalOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-rose-500 transition"
            >
              <ArrowDownLeft className="h-4 w-4" />
              Record Cash-Out
            </button>
            <button
              onClick={() => setIsAddTxnModalOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-navy-900 px-3.5 py-2 text-xs font-bold text-upay-yellow shadow-sm hover:bg-navy-800 transition border border-navy-800"
            >
              <Plus className="h-4 w-4 stroke-[3]" />
              Add Transaction
            </button>
          </div>
        </div>

        {/* Filters bar */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: "all", label: "All Types" },
              { id: "cash_in", label: "Cash In" },
              { id: "cash_out", label: "Cash Out" },
              { id: "payment", label: "Payments" },
              { id: "transfer", label: "Transfers" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilterType(f.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  filterType === f.id
                    ? "bg-navy-900 text-upay-yellow font-bold shadow-sm border border-navy-800"
                    : "text-slate-600 hover:bg-slate-100 hover:text-navy-900"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => refetch()}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {/* Table Container */}
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          {isLoading && (
            <div className="p-8 text-center text-xs text-slate-500 animate-pulse">
              Loading transaction records...
            </div>
          )}

          {error && (
            <div className="p-8 text-center text-xs text-rose-600">
              Failed to load transactions.
            </div>
          )}

          {!isLoading && !error && items.length === 0 && (
            <div className="p-12 text-center">
              <Receipt className="mx-auto h-10 w-10 text-slate-300" />
              <p className="mt-2 text-sm font-semibold text-slate-700">
                No transactions recorded
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Use &quot;Record Cash-Out&quot; or &quot;Add Transaction&quot; to log your first entry.
              </p>
            </div>
          )}

          {!isLoading && !error && items.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50/80 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-5 py-3.5">Timestamp</th>
                    <th className="px-4 py-3.5">Type</th>
                    <th className="px-4 py-3.5">Purpose</th>
                    <th className="px-4 py-3.5">Category</th>
                    <th className="px-4 py-3.5">MFS</th>
                    <th className="px-5 py-3.5 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {items.map((txn) => {
                    const isInflow = txn.transaction_type === "cash_in";
                    return (
                      <tr key={txn.id} className="hover:bg-slate-50/80 transition">
                        <td className="px-5 py-3.5 whitespace-nowrap text-slate-500">
                          {formatDateTime(txn.timestamp)}
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                              isInflow
                                ? "bg-navy-900 text-upay-yellow border border-navy-800 shadow-sm"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {isInflow ? (
                              <ArrowUpRight className="h-3 w-3 stroke-[2.5]" />
                            ) : (
                              <ArrowDownLeft className="h-3 w-3" />
                            )}
                            {txn.transaction_type.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap">
                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700 capitalize">
                            {txn.purpose.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap font-medium text-slate-900 capitalize">
                          <div>{txn.category.replace(/_/g, " ")}</div>
                          {txn.description && (
                            <div className="text-[11px] text-slate-400 font-normal lowercase">
                              {txn.description}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap">
                          {txn.mfs_provider === "upay" ? (
                            <span className="inline-flex items-center rounded-full bg-upay-yellow/20 px-2.5 py-0.5 text-[10px] font-black text-navy-950 border border-upay-yellow/50">
                              Upay
                            </span>
                          ) : (
                            <span className="font-semibold uppercase text-[10px] text-slate-600">
                              {txn.mfs_provider}
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 whitespace-nowrap text-right font-black text-sm">
                          <span className={isInflow ? "text-navy-900" : "text-rose-600"}>
                            {isInflow ? "+" : "-"}
                            {formatBDT(txn.amount)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* CashOut Purpose Modal */}
      <CashOutPurposeModal
        isOpen={isCashOutModalOpen}
        onClose={() => setIsCashOutModalOpen(false)}
        onSubmit={handleCashOutSubmit}
      />

      {/* Add Transaction Modal */}
      {isAddTxnModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-slate-100">
            <h2 className="text-base font-black text-navy-900 pb-3 border-b">
              Add MFS Transaction
            </h2>
            <form onSubmit={handleAddTxnSubmit} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Amount (৳)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="1"
                  required
                  placeholder="1000.00"
                  value={newAmount}
                  onChange={(e) => setNewAmount(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Transaction Type
                </label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as TransactionType)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900"
                >
                  <option value="cash_in">Cash In / Deposit</option>
                  <option value="payment">Merchant Payment</option>
                  <option value="send_money">Send Money</option>
                  <option value="transfer">Bank Transfer</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Purpose
                </label>
                <select
                  value={newPurpose}
                  onChange={(e) => setNewPurpose(e.target.value as Purpose)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900"
                >
                  <option value="necessity">Necessity</option>
                  <option value="savings_goal">Savings Goal</option>
                  <option value="discretionary">Discretionary</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  MFS Channel
                </label>
                <select
                  value={newProvider}
                  onChange={(e) => setNewProvider(e.target.value as any)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900 focus:border-navy-900 font-medium"
                >
                  <option value="upay">Upay</option>
                  <option value="bkash">bKash</option>
                  <option value="nagad">Nagad</option>
                  <option value="rocket">Rocket</option>
                </select>
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setIsAddTxnModalOpen(false)}
                  className="flex-1 rounded-xl border border-slate-300 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addTxnMutation.isPending}
                  className="flex-1 rounded-xl bg-navy-900 py-2.5 text-xs font-bold text-upay-yellow hover:bg-navy-800 border border-navy-800 shadow-sm"
                >
                  {addTxnMutation.isPending ? "Adding..." : "Save Entry"}
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
