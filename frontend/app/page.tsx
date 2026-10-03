import React from "react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
          <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse"></span>
          System Operational
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          Sohoj Financial Coach
        </h1>
        <p className="text-lg text-slate-600 leading-relaxed">
          Turning Mobile Financial Services (bKash, Nagad, Rocket) transactions into behavioral
          insights, deterministic simulations, and grounded coaching.
        </p>
        <div className="pt-4 flex justify-center gap-4">
          <a
            href="/api/health"
            className="px-4 py-2 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800 transition"
          >
            System Health
          </a>
        </div>
      </div>
    </main>
  );
}
