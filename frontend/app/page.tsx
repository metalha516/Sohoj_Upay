import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  Shield,
  Zap,
  TrendingUp,
  Calculator,
  Compass,
} from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-slate-50">
      <div className="max-w-3xl text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
          <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
          MFS Telemetry Active
        </div>

        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-6xl">
          Shohoj Upay Financial Coach
        </h1>

        <p className="text-lg text-slate-600 max-w-xl mx-auto leading-relaxed">
          Turning Mobile Financial Services (bKash, Nagad, Rocket) transactions into
          grounded behavioral insights, pure mathematical simulations, and AI coaching.
        </p>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-wrap justify-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 text-white font-bold text-sm shadow-md hover:bg-emerald-500 transition"
          >
            Launch Dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-900 text-white font-bold text-sm hover:bg-slate-800 transition"
          >
            Sign In
          </Link>
          <Link
            href="/simulator"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white border border-slate-200 text-slate-700 font-bold text-sm hover:bg-slate-50 transition"
          >
            <Calculator className="h-4 w-4" />
            Try Simulator
          </Link>
        </div>

        {/* Feature Highlights Grid */}
        <div className="pt-10 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <Zap className="h-5 w-5 text-emerald-600 mb-2" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Deterministic Math
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Pure Financial Engine with Decimal precision for future values, doubling times, and goal plans.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <Compass className="h-5 w-5 text-emerald-600 mb-2" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Behavioral Insights
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Classifies MFS spending patterns into 6 archetypes to deliver actionable nudges.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <Shield className="h-5 w-5 text-emerald-600 mb-2" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Grounded AI
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Tool-calling agent with strict numeric validation and 100% data minimization.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
