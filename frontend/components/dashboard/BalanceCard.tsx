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
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-navy-900 via-[#0A1C3C] to-navy-950 p-6 text-white shadow-lg border border-navy-800">
      {/* Decorative Upay ambient glow */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-upay-yellow/10 blur-3xl" />

      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-300">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-800/80 border border-navy-700/60 text-upay-yellow">
            <Wallet className="h-4 w-4" aria-hidden="true" />
          </div>
          <span className="text-sm font-semibold tracking-wide text-slate-200">Current Net Balance</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-navy-800/90 px-3 py-1 text-xs font-bold text-upay-yellow border border-upay-yellow/30 shadow-inner">
          <span className="h-2 w-2 rounded-full bg-upay-yellow ring-2 ring-upay-yellow/40 animate-pulse" />
          MFS Live
        </div>
      </div>

      <div className="relative z-10 mt-5">
        <div className="text-3xl sm:text-4xl font-black tracking-tight text-white drop-shadow-sm">
          {formatBDT(balance)}
        </div>
        <p className="mt-1 text-xs text-slate-400 font-medium">
          Combined liquidity across connected Upay & MFS accounts
        </p>
      </div>

      <div className="relative z-10 mt-6 flex flex-wrap gap-2.5">
        <button
          onClick={onRecordCashOut}
          className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-400 transition"
          aria-label="Record Cash-Out"
        >
          <ArrowDownLeft className="h-4 w-4" aria-hidden="true" />
          Record Cash-Out
        </button>

        <button
          onClick={onAddTransaction}
          className="inline-flex items-center gap-1.5 rounded-xl bg-upay-yellow px-4 py-2 text-xs font-bold text-navy-950 hover:bg-[#E5B100] focus:outline-none focus:ring-2 focus:ring-upay-yellow/50 transition shadow-sm"
          aria-label="Add Transaction"
        >
          <Plus className="h-4 w-4 stroke-[2.5]" aria-hidden="true" />
          Add Transaction
        </button>
      </div>
    </div>
  );
}
