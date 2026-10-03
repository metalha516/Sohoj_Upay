"use client";

import React from "react";
import { formatBDT } from "@/lib/formatters";
import { Wallet, ArrowUpRight, ArrowDownLeft, Plus } from "lucide-react";

interface BalanceCardProps {
  balance: number;
  onRecordCashOut?: () => void;
  onAddTransaction?: () => void;
}

export function BalanceCard({
  balance,
  onRecordCashOut,
  onAddTransaction,
}: BalanceCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-6 text-white shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-300">
          <Wallet className="h-5 w-5 text-emerald-400" aria-hidden="true" />
          <span className="text-sm font-medium tracking-wide">Current Net Balance</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-slate-800/80 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-slate-700">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          MFS Live
        </div>
      </div>

      <div className="mt-4">
        <div className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          {formatBDT(balance)}
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Combined liquidity across connected MFS accounts
        </p>
      </div>

      <div className="mt-6 flex flex-wrap gap-2.5">
        <button
          onClick={onRecordCashOut}
          className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-400 transition"
          aria-label="Record Cash-Out"
        >
          <ArrowDownLeft className="h-4 w-4" aria-hidden="true" />
          Record Cash-Out
        </button>

        <button
          onClick={onAddTransaction}
          className="inline-flex items-center gap-1.5 rounded-xl bg-slate-700 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-400 transition"
          aria-label="Add Transaction"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Add Transaction
        </button>
      </div>
    </div>
  );
}
