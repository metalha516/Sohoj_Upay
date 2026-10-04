"use client";

import React from "react";
import { formatBDT } from "@/lib/formatters";
import { Wallet, ArrowUpRight, ArrowDownLeft, Plus } from "lucide-react";
import { BorderBeam } from "@/components/ui/BorderBeam";

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
    <div className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-navy-900 via-[#0A1C3C] to-navy-950 p-6 text-white shadow-2xl border border-navy-700/80 transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-upay-glow/20">
      <BorderBeam size={160} duration={8} colorFrom="#FFC709" colorTo="#1E4D9F" />

      {/* Decorative Upay ambient glow */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-upay-yellow/15 blur-3xl" />

      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-300">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-navy-800/90 border border-navy-700/80 text-upay-yellow shadow-inner">
            <Wallet className="h-4 w-4" aria-hidden="true" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Current Net Balance</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-navy-800/90 px-3 py-1 text-xs font-bold text-upay-yellow border border-upay-yellow/30 shadow-inner">
          <span className="h-2 w-2 rounded-full bg-upay-yellow animate-ping" />
          <span className="h-2 w-2 rounded-full bg-upay-yellow -ml-3.5" />
          MFS Live
        </div>
      </div>

      <div className="relative z-10 mt-5">
        <div className="tabular-nums font-mono text-3xl sm:text-4xl font-black tracking-tight text-white drop-shadow">
          {formatBDT(balance)}
        </div>
        <p className="mt-1 text-xs text-slate-400 font-medium">
          Combined liquidity across connected Upay &amp; MFS accounts
        </p>
      </div>

      <div className="relative z-10 mt-6 flex flex-wrap gap-2.5">
        <button
          onClick={onRecordCashOut}
          className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98]"
          aria-label="Record Cash-Out"
        >
          <ArrowDownLeft className="h-4 w-4" aria-hidden="true" />
          Record Cash-Out
        </button>

        <button
          onClick={onAddTransaction}
          className="inline-flex items-center gap-1.5 rounded-xl bg-upay-yellow px-4.5 py-2 text-xs font-extrabold text-navy-950 hover:bg-upay-400 focus:outline-none focus:ring-2 focus:ring-upay-yellow/50 transition-all duration-300 ease-out shadow-lg shadow-upay-yellow/20 hover:scale-[1.02] active:scale-[0.98]"
          aria-label="Add Transaction"
        >
          <Plus className="h-4 w-4 stroke-[2.5]" aria-hidden="true" />
          Add Transaction
        </button>
      </div>
    </div>
  );
}
