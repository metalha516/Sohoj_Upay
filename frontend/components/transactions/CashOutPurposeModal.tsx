"use client";

import React, { useState, useEffect } from "react";
import { CashOutCreateRequest, MFSProvider, Purpose } from "@/types/api";
import { X, ArrowDownLeft, AlertCircle, Check } from "lucide-react";

interface CashOutPurposeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CashOutCreateRequest) => Promise<void>;
}

const PURPOSE_CATEGORIES: Record<Purpose, string[]> = {
  necessity: [
    "groceries",
    "utilities",
    "rent",
    "healthcare",
    "education",
    "transportation",
  ],
  savings_goal: [
    "dps_deposit",
    "fdr_savings",
    "emergency_fund",
    "goal_contribution",
  ],
  discretionary: [
    "dining_out",
    "shopping",
    "entertainment",
    "travel",
    "personal_care",
  ],
  other: [
    "family_support",
    "loan_repayment",
    "fees_tariffs",
    "miscellaneous",
  ],
};

const PROVIDERS: { id: MFSProvider; label: string; color: string }[] = [
  { id: "bkash", label: "bKash", color: "text-[#E2136E]" },
  { id: "nagad", label: "Nagad", color: "text-[#F7941D]" },
  { id: "rocket", label: "Rocket", color: "text-[#8C3494]" },
  { id: "upay", label: "Upay", color: "text-[#005BAC]" },
  { id: "other", label: "Other MFS", color: "text-slate-600" },
];

export function CashOutPurposeModal({
  isOpen,
  onClose,
  onSubmit,
}: CashOutPurposeModalProps) {
  const [amount, setAmount] = useState<string>("");
  const [purpose, setPurpose] = useState<Purpose | "">("");
  const [category, setCategory] = useState<string>("");
  const [provider, setProvider] = useState<MFSProvider>("bkash");
  const [description, setDescription] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setAmount("");
      setPurpose("");
      setCategory("");
      setDescription("");
      setErrorMessage(null);
    }
  }, [isOpen]);

  // When purpose changes, update category to first valid option
  const handlePurposeChange = (newPurpose: Purpose) => {
    setPurpose(newPurpose);
    const availableCategories = PURPOSE_CATEGORIES[newPurpose] || [];
    setCategory(availableCategories[0] || "miscellaneous");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      setErrorMessage("Please enter a valid amount greater than ৳0");
      return;
    }

    if (!purpose) {
      setErrorMessage("Selecting a purpose is mandatory for cash-outs");
      return;
    }

    setIsSubmitting(true);
    try {
      const idempotencyKey = `cashout-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      await onSubmit({
        amount: numAmount,
        purpose,
        category: category || "miscellaneous",
        mfs_provider: provider,
        description: description.trim() || undefined,
        idempotency_key: idempotencyKey,
      });
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to record cash-out");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cashout-modal-title"
    >
      <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2 text-rose-600">
            <ArrowDownLeft className="h-5 w-5" aria-hidden="true" />
            <h2
              id="cashout-modal-title"
              className="text-lg font-bold text-slate-900"
            >
              Record MFS Cash-Out
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-400"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {errorMessage && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Amount Input */}
          <div>
            <label
              htmlFor="cashout-amount"
              className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
            >
              Cash-Out Amount (৳) <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-base">
                ৳
              </span>
              <input
                id="cashout-amount"
                type="number"
                step="0.01"
                min="1"
                placeholder="2,500.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-300 pl-8 pr-4 py-2.5 text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-base font-semibold"
              />
            </div>
          </div>

          {/* Mandatory Purpose Radio Grid */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Purpose (Mandatory) <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  { id: "necessity", label: "Necessity", desc: "Rent, food, medical" },
                  { id: "savings_goal", label: "Savings Goal", desc: "DPS, FDR, buffer" },
                  { id: "discretionary", label: "Discretionary", desc: "Shopping, dining" },
                  { id: "other", label: "Other", desc: "Transfers, loans" },
                ] as const
              ).map((p) => {
                const isSelected = purpose === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handlePurposeChange(p.id)}
                    className={`flex flex-col text-left p-3 rounded-xl border transition ${
                      isSelected
                        ? "border-emerald-600 bg-emerald-50/60 ring-2 ring-emerald-600/30 text-emerald-950"
                        : "border-slate-200 bg-slate-50/50 hover:bg-slate-100 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs">{p.label}</span>
                      {isSelected && <Check className="h-3.5 w-3.5 text-emerald-600" />}
                    </div>
                    <span className="text-[10px] text-slate-500 mt-0.5">{p.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Subcategory Selector (conditional on purpose) */}
          {purpose && (
            <div>
              <label
                htmlFor="cashout-category"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Subcategory <span className="text-rose-500">*</span>
              </label>
              <select
                id="cashout-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-xs text-slate-900 capitalize focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 bg-white"
              >
                {PURPOSE_CATEGORIES[purpose].map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Provider Selection */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              MFS Channel / Agent
            </label>
            <div className="flex flex-wrap gap-2">
              {PROVIDERS.map((pr) => {
                const isSelected = provider === pr.id;
                return (
                  <button
                    key={pr.id}
                    type="button"
                    onClick={() => setProvider(pr.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                      isSelected
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <span className={isSelected ? "text-white" : pr.color}>
                      {pr.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Optional Note / Description */}
          <div>
            <label
              htmlFor="cashout-desc"
              className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
            >
              Note / Agent Number (Optional)
            </label>
            <input
              id="cashout-desc"
              type="text"
              maxLength={150}
              placeholder="e.g. Agent cash-out for house rent"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !purpose || !amount}
              className="flex-1 rounded-xl bg-rose-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-400 disabled:opacity-50 transition"
            >
              {isSubmitting ? "Recording..." : "Record Cash-Out"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
