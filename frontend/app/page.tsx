"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ShieldCheck,
  Zap,
  TrendingUp,
  Calculator,
  Sparkles,
  Bot,
  Layers,
  Lock,
  Smartphone,
  CheckCircle2,
  ChevronRight,
  User,
  Activity,
  Percent,
  Clock,
  Wallet,
  Play,
  Scale,
  Building2,
  Shield,
  Award,
} from "lucide-react";

export default function Home() {
  // Simulator State
  const [activeWidgetTab, setActiveWidgetTab] = useState<"compound" | "tariff">("compound");

  // Compound Simulator controls
  const [monthlySavings, setMonthlySavings] = useState<number>(3000);
  const [returnRate, setReturnRate] = useState<number>(8.5);
  const [years, setYears] = useState<number>(5);

  // Tariff Simulator controls
  const [cashOutAmount, setCashOutAmount] = useState<number>(5000);
  const [selectedChannel, setSelectedChannel] = useState<"app" | "atm" | "agent">("agent");

  // Persona State
  const [activePersonaIndex, setActivePersonaIndex] = useState<number>(0);

  // Deterministic Compound Calculation
  const compoundCalculation = useMemo(() => {
    const monthlyRate = returnRate / 100 / 12;
    const totalMonths = years * 12;
    const principal = monthlySavings * totalMonths;

    let futureValue = 0;
    if (monthlyRate > 0) {
      futureValue = monthlySavings * ((Math.pow(1 + monthlyRate, totalMonths) - 1) / monthlyRate);
    } else {
      futureValue = principal;
    }

    const interestEarned = Math.max(0, futureValue - principal);
    // Rule of 72 doubling time
    const doublingYears = returnRate > 0 ? (72 / returnRate).toFixed(1) : "N/A";

    return {
      principal: Math.round(principal),
      futureValue: Math.round(futureValue),
      interestEarned: Math.round(interestEarned),
      doublingYears,
    };
  }, [monthlySavings, returnRate, years]);

  // Tariff Calculation
  const tariffCalculation = useMemo(() => {
    // Upay standard charges per 1000:
    // Agent: 1.4% (৳14/1000)
    // ATM: 0.8% (৳8/1000)
    // App/POS: 1.4% (৳14/1000)
    // Typical competitor rate: 1.85% (৳18.5/1000)
    let upayRate = 0.014;
    if (selectedChannel === "atm") upayRate = 0.008;

    const competitorRate = 0.0185;

    const upayFee = cashOutAmount * upayRate;
    const competitorFee = cashOutAmount * competitorRate;
    const perTxSavings = competitorFee - upayFee;
    const annualSavings = perTxSavings * 12 * 4; // assuming 4 cashouts a month

    return {
      upayFee: Math.round(upayFee),
      competitorFee: Math.round(competitorFee),
      perTxSavings: Math.round(perTxSavings),
      annualSavings: Math.round(annualSavings),
      upayRatePercent: (upayRate * 100).toFixed(1),
    };
  }, [cashOutAmount, selectedChannel]);

  // Personas Data
  const personas = [
    {
      name: "Sumaiya",
      role: "Ride-Share Driver & Gig Earner",
      location: "Dhaka (Mirpur)",
      income: "৳38,000 / month",
      archetype: "Volatile Earner & High Velocity",
      tagColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      quote: "My daily cash-outs used to eat a huge chunk of my fuel money without me noticing.",
      problem: "Performed 15+ small cash-outs every month at high 1.85% competitor rates, losing over ৳1,400 monthly in tariff friction.",
      solution: "Sohoj AI flagged the tariff drain and nudged Sumaiya to batch withdrawals through the Upay agent network at 1.4%, plus auto-stashed ৳100/day into an emergency fund.",
      impact: "Saved ৳17,040 annually in cash-out tariffs and built a ৳42,000 rainy-day cushion.",
      statNumber: "৳17,040",
      statLabel: "Annual Tariff Savings",
    },
    {
      name: "Roksana",
      role: "Undergraduate Student & Freelance Tutor",
      location: "University of Dhaka",
      income: "৳14,500 / month",
      archetype: "Impulsive Micro-Spender",
      tagColor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      quote: "Small ৳150 snack orders and peer transfers made my money vanish halfway through the semester.",
      problem: "Frequent peer transfers and unmonitored evening food deliveries drained 64% of her tutoring stipend within the first 10 days.",
      solution: "Sohoj behavioral classifier set up micro-savings round-ups into an 8.5% DPS goal ('New Laptop Fund') and generated predictive spend limits before weekend outings.",
      impact: "Hit her ৳35,000 tech goal in 7 months without borrowing or taking high-interest loans.",
      statNumber: "7 Months",
      statLabel: "To Reach Laptop Goal",
    },
    {
      name: "Kamrul",
      role: "Remittance Receiver & Family Trustee",
      location: "Sylhet (Beanibazar)",
      income: "৳65,000 / month (UAE Inflow)",
      archetype: "Family Trustee & Lumpy Inflow",
      tagColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      quote: "When remittance lands, money disappears instantly among extended family expenses unless structured.",
      problem: "Large bi-monthly overseas inflows left no emergency buffer; remittance incentives (2.5% govt subsidy) were untracked.",
      solution: "Grounded Gemini AI Coach created an automatic 20% instant lock into high-yield Islamic Shariah DPS upon remittance receipt, routing payouts through Upay's zero-hidden-fee channel.",
      impact: "Accumulated ৳180,000 in dedicated health & farming reserves in under one year.",
      statNumber: "৳180,000",
      statLabel: "Emergency Reserve Built",
    },
  ];

  const currentPersona = personas[activePersonaIndex];

  return (
    <div className="min-h-screen bg-[#061325] text-slate-100 selection:bg-upay-500 selection:text-navy-950 font-sans">
      {/* 1. Sleek Navigation Bar */}
      <header className="sticky top-0 z-50 border-b border-navy-800/80 bg-navy-950/85 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-upay-500 text-navy-950 font-black text-xl shadow-lg upay-glow transition-transform duration-300 group-hover:scale-105">
              S
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-2xl font-black tracking-tight text-white">Sohoj</span>
                <span className="rounded-md bg-upay-500/20 px-2 py-0.5 text-xs font-bold text-upay-400 border border-upay-500/30">
                  Upay
                </span>
              </div>
              <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">
                AI Financial Copilot
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-upay-400 transition-colors">
              Features
            </a>
            <a href="#simulator" className="hover:text-upay-400 transition-colors">
              Live Simulator
            </a>
            <a href="#personas" className="hover:text-upay-400 transition-colors">
              Personas
            </a>
            <a href="#security" className="hover:text-upay-400 transition-colors">
              Security & Compliance
            </a>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden sm:inline-flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold text-slate-200 hover:text-white hover:bg-navy-800/60 transition-all border border-navy-700/60"
            >
              Sign In
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-upay-500 text-navy-950 font-bold text-sm shadow-md hover:bg-upay-400 hover:scale-[1.02] active:scale-[0.98] transition-all upay-glow"
            >
              Launch App
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-24 md:pt-24 md:pb-32 mesh-gradient-hero fintech-grid">
        {/* Ambient background glows */}
        <div className="pointer-events-none absolute top-12 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-upay-500/10 blur-[130px] rounded-full" />
        <div className="pointer-events-none absolute top-40 right-10 w-[400px] h-[300px] bg-navy-600/25 blur-[120px] rounded-full" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          {/* Dynamic Pill */}
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-navy-900/90 border border-navy-700 text-xs font-semibold text-slate-200 shadow-md mb-8 badge-glow animate-pulse-subtle">
            <span className="flex h-2 w-2 rounded-full bg-upay-500 animate-ping" />
            <span className="flex h-2 w-2 rounded-full bg-upay-500 -ml-4" />
            <span className="text-upay-400 font-bold">Bangladesh&apos;s First AI Financial Copilot</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-300">Upay MFS Intelligence</span>
          </div>

          {/* Headline */}
          <h1 className="mx-auto max-w-5xl text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.12]">
            Turn Every MFS Taka Into <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-upay-400 via-yellow-200 to-upay-500 bg-clip-text text-transparent">
              Compounded Wealth
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mx-auto mt-6 max-w-3xl text-lg sm:text-xl text-slate-300 leading-relaxed font-normal">
            Autonomous expense forecasting, deterministic compound wealth simulation, and grounded
            Gemini AI coaching. Seamlessly integrated with Upay, bKash, Nagad, and Rocket — with zero PII exposure.
          </p>

          {/* Hero CTAs */}
          <div className="mt-10 flex flex-wrap justify-center items-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-2xl bg-upay-500 text-navy-950 font-black text-base shadow-xl hover:bg-upay-400 hover:scale-[1.02] active:scale-[0.98] transition-all upay-glow"
            >
              Launch Dashboard
              <ArrowRight className="h-5 w-5" />
            </Link>
            <a
              href="#simulator"
              className="inline-flex items-center gap-2.5 px-7 py-4 rounded-2xl bg-navy-900/90 text-white font-bold text-base hover:bg-navy-800 transition-all border border-navy-700/80 shadow-md"
            >
              <Calculator className="h-5 w-5 text-upay-400" />
              Try Live Simulator
            </a>
            <Link
              href="/coach"
              className="inline-flex items-center gap-2 px-6 py-4 rounded-2xl bg-navy-950/60 text-slate-300 font-semibold text-base hover:text-white hover:bg-navy-900 transition-all border border-navy-800/80"
            >
              <Bot className="h-5 w-5 text-cyan-400" />
              Chat With AI Coach
            </Link>
          </div>

          {/* Live Trust & Metrics Row */}
          <div className="mt-16 pt-8 border-t border-navy-800/60 grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-5xl mx-auto">
            <div className="p-4 rounded-2xl bg-navy-900/40 border border-navy-800/60 backdrop-blur-sm text-center">
              <div className="text-2xl sm:text-3xl font-black text-upay-400">৳45M+</div>
              <div className="mt-1 text-xs text-slate-400 font-medium">Simulated Wealth Volume</div>
            </div>
            <div className="p-4 rounded-2xl bg-navy-900/40 border border-navy-800/60 backdrop-blur-sm text-center">
              <div className="text-2xl sm:text-3xl font-black text-white">0.8% - 1.4%</div>
              <div className="mt-1 text-xs text-slate-400 font-medium">Upay Tariff Optimization</div>
            </div>
            <div className="p-4 rounded-2xl bg-navy-900/40 border border-navy-800/60 backdrop-blur-sm text-center">
              <div className="text-2xl sm:text-3xl font-black text-emerald-400">100% Grounded</div>
              <div className="mt-1 text-xs text-slate-400 font-medium">Strict Math & Zero Hallucination</div>
            </div>
            <div className="p-4 rounded-2xl bg-navy-900/40 border border-navy-800/60 backdrop-blur-sm text-center">
              <div className="text-2xl sm:text-3xl font-black text-white">Zero PII</div>
              <div className="mt-1 text-xs text-slate-400 font-medium">HMAC-SHA256 Tokenized</div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Interactive Live Simulation & Coach Preview Widget */}
      <section id="simulator" className="py-20 md:py-28 relative bg-[#070D18]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-upay-500/10 border border-upay-500/30 text-xs font-bold text-upay-400 mb-3">
              <Sparkles className="h-3.5 w-3.5" />
              Interactive Engine
            </div>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
              Test The Financial Engine Live
            </h2>
            <p className="mt-4 text-slate-400 text-base sm:text-lg">
              No account required. Experiment with Bangladesh bank DPS compounding or calculate your exact Upay tariff savings instantly.
            </p>
          </div>

          {/* Interactive Widget Box */}
          <div className="max-w-4xl mx-auto rounded-3xl glass-card border border-navy-700/80 p-6 sm:p-10 shadow-2xl relative overflow-hidden">
            {/* Ambient accent inside card */}
            <div className="pointer-events-none absolute -right-20 -bottom-20 w-80 h-80 bg-upay-500/10 blur-[100px] rounded-full" />

            {/* Tab Switcher */}
            <div className="flex items-center justify-center gap-3 p-1.5 rounded-2xl bg-navy-950/80 border border-navy-800/80 max-w-md mx-auto mb-8">
              <button
                onClick={() => setActiveWidgetTab("compound")}
                className={`flex-1 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                  activeWidgetTab === "compound"
                    ? "bg-upay-500 text-navy-950 shadow-md upay-glow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <TrendingUp className="h-4 w-4" />
                Wealth Simulator
              </button>
              <button
                onClick={() => setActiveWidgetTab("tariff")}
                className={`flex-1 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                  activeWidgetTab === "tariff"
                    ? "bg-upay-500 text-navy-950 shadow-md upay-glow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Scale className="h-4 w-4" />
                Tariff Optimizer
              </button>
            </div>

            {/* Tab 1: Wealth Simulator */}
            {activeWidgetTab === "compound" && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Controls Column */}
                <div className="lg:col-span-7 space-y-6">
                  {/* Slider 1: Monthly Savings */}
                  <div>
                    <div className="flex justify-between items-center text-sm font-semibold mb-2">
                      <span className="text-slate-300">Monthly DPS Contribution</span>
                      <span className="text-upay-400 font-bold text-base">
                        ৳ {monthlySavings.toLocaleString("en-BD")}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={500}
                      max={25000}
                      step={500}
                      value={monthlySavings}
                      onChange={(e) => setMonthlySavings(Number(e.target.value))}
                      className="w-full h-2.5 bg-navy-800 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
                    />
                    <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                      <span>৳500</span>
                      <span>৳10,000</span>
                      <span>৳25,000</span>
                    </div>
                  </div>

                  {/* Slider 2: Annual Return Rate */}
                  <div>
                    <div className="flex justify-between items-center text-sm font-semibold mb-2">
                      <span className="text-slate-300">Annual Return / DPS Rate</span>
                      <span className="text-upay-400 font-bold text-base">{returnRate}%</span>
                    </div>
                    <input
                      type="range"
                      min={5.0}
                      max={12.0}
                      step={0.5}
                      value={returnRate}
                      onChange={(e) => setReturnRate(Number(e.target.value))}
                      className="w-full h-2.5 bg-navy-800 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
                    />
                    <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                      <span>5% (Savings)</span>
                      <span>8.5% (Bank DPS)</span>
                      <span>12% (Equity/Bond)</span>
                    </div>
                  </div>

                  {/* Slider 3: Horizon */}
                  <div>
                    <div className="flex justify-between items-center text-sm font-semibold mb-2">
                      <span className="text-slate-300">Investment Horizon</span>
                      <span className="text-upay-400 font-bold text-base">{years} Years</span>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={15}
                      step={1}
                      value={years}
                      onChange={(e) => setYears(Number(e.target.value))}
                      className="w-full h-2.5 bg-navy-800 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
                    />
                    <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                      <span>1 Year</span>
                      <span>5 Years</span>
                      <span>15 Years</span>
                    </div>
                  </div>

                  {/* Grounded Explanation Box */}
                  <div className="p-3.5 rounded-xl bg-navy-950/60 border border-navy-800 text-xs text-slate-300 leading-relaxed flex items-start gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-upay-400 shrink-0 mt-0.5" />
                    <span>
                      Grounded Rule of 72: At <strong>{returnRate}%</strong>, your deposited capital doubles every{" "}
                      <strong className="text-upay-400">{compoundCalculation.doublingYears} years</strong> without risking principal.
                    </span>
                  </div>
                </div>

                {/* Calculation Output Card */}
                <div className="lg:col-span-5 rounded-2xl bg-gradient-to-br from-navy-900/90 to-navy-950/95 border border-navy-700/70 p-6 flex flex-col justify-between shadow-lg">
                  <div>
                    <div className="text-xs uppercase tracking-wider font-extrabold text-slate-400 mb-1">
                      Projected Maturity Value
                    </div>
                    <div className="text-3xl sm:text-4xl font-black text-white">
                      ৳ {compoundCalculation.futureValue.toLocaleString("en-BD")}
                    </div>
                    <div className="text-xs text-upay-400 font-semibold mt-1">
                      +৳ {compoundCalculation.interestEarned.toLocaleString("en-BD")} pure compound gain
                    </div>

                    <div className="mt-6 space-y-3 pt-4 border-t border-navy-800">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">Total Capital Saved:</span>
                        <span className="font-bold text-slate-200">
                          ৳ {compoundCalculation.principal.toLocaleString("en-BD")}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">Compound Returns:</span>
                        <span className="font-bold text-emerald-400">
                          +৳ {compoundCalculation.interestEarned.toLocaleString("en-BD")}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">Doubling Cycle:</span>
                        <span className="font-bold text-upay-400">
                          ~{compoundCalculation.doublingYears} Years
                        </span>
                      </div>
                    </div>
                  </div>

                  <Link
                    href="/simulator"
                    className="mt-6 w-full py-3 rounded-xl bg-upay-500 hover:bg-upay-400 text-navy-950 text-xs font-bold transition-all text-center flex items-center justify-center gap-2 upay-glow"
                  >
                    Open Full Simulator
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            )}

            {/* Tab 2: Tariff Optimizer */}
            {activeWidgetTab === "tariff" && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Controls */}
                <div className="lg:col-span-7 space-y-6">
                  <div>
                    <div className="flex justify-between items-center text-sm font-semibold mb-2">
                      <span className="text-slate-300">Single Cash-Out Amount</span>
                      <span className="text-upay-400 font-bold text-base">
                        ৳ {cashOutAmount.toLocaleString("en-BD")}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={500}
                      max={25000}
                      step={500}
                      value={cashOutAmount}
                      onChange={(e) => setCashOutAmount(Number(e.target.value))}
                      className="w-full h-2.5 bg-navy-800 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
                    />
                    <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                      <span>৳500</span>
                      <span>৳10,000</span>
                      <span>৳25,000</span>
                    </div>
                  </div>

                  {/* Channel Selector */}
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Cash-Out Channel
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={() => setSelectedChannel("agent")}
                        className={`p-3 rounded-xl border text-xs font-bold transition-all ${
                          selectedChannel === "agent"
                            ? "bg-upay-500 text-navy-950 border-upay-500 shadow-md"
                            : "bg-navy-900/60 border-navy-800 text-slate-300 hover:bg-navy-800"
                        }`}
                      >
                        Upay Agent (1.4%)
                      </button>
                      <button
                        onClick={() => setSelectedChannel("atm")}
                        className={`p-3 rounded-xl border text-xs font-bold transition-all ${
                          selectedChannel === "atm"
                            ? "bg-upay-500 text-navy-950 border-upay-500 shadow-md"
                            : "bg-navy-900/60 border-navy-800 text-slate-300 hover:bg-navy-800"
                        }`}
                      >
                        UCB ATM (0.8%)
                      </button>
                      <button
                        onClick={() => setSelectedChannel("app")}
                        className={`p-3 rounded-xl border text-xs font-bold transition-all ${
                          selectedChannel === "app"
                            ? "bg-upay-500 text-navy-950 border-upay-500 shadow-md"
                            : "bg-navy-900/60 border-navy-800 text-slate-300 hover:bg-navy-800"
                        }`}
                      >
                        Upay App / POS (1.4%)
                      </button>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-navy-950/60 border border-navy-800 text-xs text-slate-300 leading-relaxed flex items-start gap-2.5">
                    <Award className="h-4 w-4 text-upay-400 shrink-0 mt-0.5" />
                    <span>
                      Standard market cash-out tariffs average <strong>1.85% (৳18.5/1000)</strong>. Upay provides the country&apos;s lowest ATM tariff at{" "}
                      <strong className="text-upay-400">0.8%</strong> and agent tariff at{" "}
                      <strong className="text-upay-400">1.4%</strong>.
                    </span>
                  </div>
                </div>

                {/* Tariff Output Card */}
                <div className="lg:col-span-5 rounded-2xl bg-gradient-to-br from-navy-900/90 to-navy-950/95 border border-navy-700/70 p-6 flex flex-col justify-between shadow-lg">
                  <div>
                    <div className="text-xs uppercase tracking-wider font-extrabold text-slate-400 mb-1">
                      Upay Tariff Fee
                    </div>
                    <div className="text-3xl sm:text-4xl font-black text-upay-400">
                      ৳ {tariffCalculation.upayFee.toLocaleString("en-BD")}
                    </div>
                    <div className="text-xs text-slate-400 line-through mt-0.5">
                      Competitor Fee: ৳ {tariffCalculation.competitorFee.toLocaleString("en-BD")}
                    </div>

                    <div className="mt-6 space-y-3 pt-4 border-t border-navy-800">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">Savings This Withdrawal:</span>
                        <span className="font-bold text-emerald-400">
                          ৳ {tariffCalculation.perTxSavings.toLocaleString("en-BD")} saved
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">Annual Friction Saved:</span>
                        <span className="font-bold text-upay-400">
                          ৳ {tariffCalculation.annualSavings.toLocaleString("en-BD")} / year
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">Effective Tariff Rate:</span>
                        <span className="font-bold text-white">
                          {tariffCalculation.upayRatePercent}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <Link
                    href="/dashboard"
                    className="mt-6 w-full py-3 rounded-xl bg-upay-500 hover:bg-upay-400 text-navy-950 text-xs font-bold transition-all text-center flex items-center justify-center gap-2 upay-glow"
                  >
                    Track All My Cash-Outs
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 4. Four Core Pillars Grid */}
      <section id="features" className="py-20 md:py-28 relative bg-[#061325]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-upay-500/10 border border-upay-500/30 text-xs font-bold text-upay-400 mb-3">
              <Layers className="h-3.5 w-3.5" />
              Core Architecture
            </div>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
              Engineered For Financial Clarity
            </h2>
            <p className="mt-4 text-slate-400 text-base sm:text-lg">
              Four grounded pillars uniting mathematical determinism, machine learning forecasting, and localized MFS intelligence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Pillar 1 */}
            <div className="rounded-3xl glass-card glass-card-hover p-8 border border-navy-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-upay-500/15 border border-upay-500/30 text-upay-400">
                    <TrendingUp className="h-6 w-6" />
                  </div>
                  <span className="rounded-full bg-navy-800/80 px-3 py-1 text-xs font-semibold text-slate-300 border border-navy-700">
                    Predictive Engine
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  1. Autonomous Expense Forecasting
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Hybrid statistical projection trained on localized MFS spending velocity. Predicts 7-day and 30-day cash drains, factoring in salary dates, utility deadlines, and festival seasonality like Eid-ul-Fitr and Puja.
                </p>
              </div>
              <div className="mt-8 pt-4 border-t border-navy-800/80 flex items-center gap-2 text-xs text-upay-400 font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Prevents overdrafts before they happen</span>
              </div>
            </div>

            {/* Pillar 2 */}
            <div className="rounded-3xl glass-card glass-card-hover p-8 border border-navy-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
                    <Bot className="h-6 w-6" />
                  </div>
                  <span className="rounded-full bg-navy-800/80 px-3 py-1 text-xs font-semibold text-slate-300 border border-navy-700">
                    Gemini 1.5 Flash
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  2. Grounded AI Financial Coach
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Conversational assistant with strict tool-calling boundaries. Powered by Gemini with numeric function verification against actual Upay tariff sheets. Never provides hallucinated rates or speculative stock bets.
                </p>
              </div>
              <div className="mt-8 pt-4 border-t border-navy-800/80 flex items-center gap-2 text-xs text-cyan-400 font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Strict prompt-injected math guardrails</span>
              </div>
            </div>

            {/* Pillar 3 */}
            <div className="rounded-3xl glass-card glass-card-hover p-8 border border-navy-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
                    <Calculator className="h-6 w-6" />
                  </div>
                  <span className="rounded-full bg-navy-800/80 px-3 py-1 text-xs font-semibold text-slate-300 border border-navy-700">
                    Deterministic Math
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  3. Deterministic Compound Simulator
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Pure Python and TypeScript Decimal math. Computes future values, exact logarithmic doubling times via the Rule of 72, and target goal amortization schedules with zero floating point drift.
                </p>
              </div>
              <div className="mt-8 pt-4 border-t border-navy-800/80 flex items-center gap-2 text-xs text-amber-400 font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Arbitrary-precision arithmetic</span>
              </div>
            </div>

            {/* Pillar 4 */}
            <div className="rounded-3xl glass-card glass-card-hover p-8 border border-navy-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-400">
                    <Activity className="h-6 w-6" />
                  </div>
                  <span className="rounded-full bg-navy-800/80 px-3 py-1 text-xs font-semibold text-slate-300 border border-navy-700">
                    Z-Score Anomaly Trigger
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  4. MFS Behavioral Archetypes & Anomalies
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Automatically classifies user telemetry into 6 behavioral archetypes (Volatile Earner, Impulsive Micro-Spender, Family Trustee, etc.). Detects velocity spikes, unexpected midnight transfers, and unauthorized drains.
                </p>
              </div>
              <div className="mt-8 pt-4 border-t border-navy-800/80 flex items-center gap-2 text-xs text-rose-400 font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Flags anomalous drain before funds evaporate</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Persona Switcher Showcase */}
      <section id="personas" className="py-20 md:py-28 relative bg-[#070D18]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-upay-500/10 border border-upay-500/30 text-xs font-bold text-upay-400 mb-3">
              <User className="h-3.5 w-3.5" />
              Real Personas
            </div>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
              Built For Real Bangladeshi Lives
            </h2>
            <p className="mt-4 text-slate-400 text-base sm:text-lg">
              Explore how Sohoj adapts to different income cycles, spending habits, and financial goals across Bangladesh.
            </p>
          </div>

          {/* Persona Selection Buttons */}
          <div className="flex flex-wrap justify-center gap-3 mb-10">
            {personas.map((persona, index) => (
              <button
                key={persona.name}
                onClick={() => setActivePersonaIndex(index)}
                className={`px-5 py-3 rounded-2xl text-sm font-bold transition-all flex items-center gap-2.5 border ${
                  activePersonaIndex === index
                    ? "bg-upay-500 text-navy-950 border-upay-500 shadow-lg upay-glow"
                    : "bg-navy-900/60 border-navy-800 text-slate-300 hover:bg-navy-800/80"
                }`}
              >
                <span>{persona.name}</span>
                <span className="text-xs opacity-75 font-normal">({persona.role.split("&")[0]})</span>
              </button>
            ))}
          </div>

          {/* Persona Card Detail */}
          <div className="max-w-4xl mx-auto rounded-3xl glass-card border border-navy-700/80 p-8 sm:p-12 shadow-2xl relative">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
              <div className="md:col-span-8 space-y-4">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h3 className="text-2xl sm:text-3xl font-black text-white">
                    {currentPersona.name}
                  </h3>
                  <span className="text-xs px-2.5 py-1 rounded-lg bg-navy-800 text-slate-300 font-medium">
                    {currentPersona.location}
                  </span>
                  <span className={`text-xs px-2.5 py-1 rounded-lg font-bold border ${currentPersona.tagColor}`}>
                    {currentPersona.archetype}
                  </span>
                </div>

                <div className="text-sm font-semibold text-slate-400">
                  Monthly Cash Flow: <span className="text-white font-bold">{currentPersona.income}</span>
                </div>

                <blockquote className="italic text-slate-300 text-base border-l-2 border-upay-500 pl-4 py-1">
                  &ldquo;{currentPersona.quote}&rdquo;
                </blockquote>

                <div className="space-y-3 pt-3">
                  <div>
                    <span className="text-xs uppercase font-extrabold tracking-wider text-rose-400">The Friction:</span>
                    <p className="text-sm text-slate-300 mt-0.5">{currentPersona.problem}</p>
                  </div>
                  <div>
                    <span className="text-xs uppercase font-extrabold tracking-wider text-emerald-400">Sohoj Intervention:</span>
                    <p className="text-sm text-slate-300 mt-0.5">{currentPersona.solution}</p>
                  </div>
                </div>
              </div>

              {/* Persona Stat Highlight Box */}
              <div className="md:col-span-4 rounded-2xl bg-gradient-to-br from-navy-900 to-navy-950 border border-navy-700 p-6 text-center flex flex-col justify-center items-center shadow-inner">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Verified Outcome
                </div>
                <div className="text-3xl sm:text-4xl font-black text-upay-400 mt-1">
                  {currentPersona.statNumber}
                </div>
                <div className="text-xs font-semibold text-slate-300 mt-1">
                  {currentPersona.statLabel}
                </div>
                <div className="mt-6 w-full pt-4 border-t border-navy-800 text-[11px] text-slate-400">
                  {currentPersona.impact}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Security & MFS Compliance Banner */}
      <section id="security" className="py-20 md:py-24 relative bg-[#061325] border-t border-navy-800/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-3xl bg-gradient-to-br from-navy-900/90 via-navy-950 to-navy-900/80 border border-navy-700/80 p-8 sm:p-12 shadow-2xl relative overflow-hidden">
            <div className="pointer-events-none absolute -left-16 -top-16 w-64 h-64 bg-cyan-500/10 blur-[90px] rounded-full" />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 space-y-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-xs font-bold text-cyan-400">
                  <ShieldCheck className="h-4 w-4" />
                  Bank-Grade Privacy Standards
                </div>
                <h3 className="text-2xl sm:text-4xl font-extrabold text-white">
                  Zero PII. 100% Data Minimization.
                </h3>
                <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
                  Sohoj operates strictly under principles of data minimization. We never read or store SMS bodies, bank PINs, or national IDs. Phone numbers are pseudonymized using SHA-256 HMAC salts before transaction patterns are analyzed.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-upay-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">
                      <strong>Zero Raw SMS Storage:</strong> Transactions extracted in transient RAM only.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-upay-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">
                      <strong>Upay Tariff Optimization:</strong> Bangladesh Bank PSD regulatory guidelines compliant.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-upay-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">
                      <strong>Client-Side Tokenization:</strong> Strict role-based JWT sessions with instant expiry.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-upay-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">
                      <strong>Grounded Boundaries:</strong> AI coach restricted from offering unverified financial speculation.
                    </span>
                  </div>
                </div>
              </div>

              {/* Compliance Visual Badge */}
              <div className="lg:col-span-5 flex flex-col items-center justify-center p-8 rounded-2xl bg-navy-950/80 border border-navy-800 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-upay-500/15 border border-upay-500/40 text-upay-400 mb-4 upay-glow">
                  <Lock className="h-8 w-8" />
                </div>
                <div className="text-lg font-bold text-white">Bangladesh Bank MFS Aligned</div>
                <div className="text-xs text-slate-400 mt-1 max-w-xs">
                  Tested and calibrated against official Mobile Financial Services tariff schedules (Upay, bKash, Nagad, Rocket).
                </div>
                <div className="mt-6 inline-flex items-center gap-2 text-xs font-semibold text-upay-400">
                  <Building2 className="h-4 w-4" />
                  <span>UCB & Upay Network Calibrated</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Conversion CTA Banner */}
      <section className="py-20 relative bg-gradient-to-b from-[#061325] to-[#0A1C3C] text-center">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            Ready To Stop Leaking Money On MFS Fees?
          </h2>
          <p className="mt-4 text-slate-300 text-base sm:text-lg max-w-2xl mx-auto">
            Join thousands of smart earners in Bangladesh optimizing their Mobile Financial Services with deterministic math and grounded AI.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-upay-500 text-navy-950 font-black text-base shadow-xl hover:bg-upay-400 hover:scale-[1.02] active:scale-[0.98] transition-all upay-glow"
            >
              Launch Sohoj Copilot
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-7 py-4 rounded-2xl bg-navy-900/90 text-white font-bold text-base hover:bg-navy-800 transition-all border border-navy-700 shadow-md"
            >
              Create Free Account
            </Link>
          </div>
        </div>
      </section>

      {/* 8. Polished Footer */}
      <footer className="border-t border-navy-800 bg-navy-950 py-14 text-slate-400 text-xs">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
            {/* Brand Column */}
            <div className="space-y-3 md:col-span-1">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-upay-500 text-navy-950 font-black text-sm">
                  S
                </div>
                <span className="text-lg font-black text-white tracking-tight">Sohoj Upay</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Autonomous financial copilot for Mobile Financial Services users across Bangladesh.
              </p>
              <div className="text-[11px] text-slate-500">
                Brand Partner: Upay (UCB Fintech Alliance)
              </div>
            </div>

            {/* Platform Links */}
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3">
                Platform
              </div>
              <ul className="space-y-2">
                <li>
                  <Link href="/dashboard" className="hover:text-upay-400 transition-colors">
                    Dashboard Overview
                  </Link>
                </li>
                <li>
                  <Link href="/simulator" className="hover:text-upay-400 transition-colors">
                    Wealth Simulator
                  </Link>
                </li>
                <li>
                  <Link href="/transactions" className="hover:text-upay-400 transition-colors">
                    Transaction Telemetry
                  </Link>
                </li>
                <li>
                  <Link href="/coach" className="hover:text-upay-400 transition-colors">
                    Grounded AI Coach
                  </Link>
                </li>
              </ul>
            </div>

            {/* MFS Providers */}
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3">
                Supported Networks
              </div>
              <ul className="space-y-2">
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-upay-500" />
                  <span>Upay (UCB Fintech) — 1.4% / 0.8%</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#E2136E]" />
                  <span>bKash Network — 1.85%</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#F7941D]" />
                  <span>Nagad Post Office — 1.5%</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#8C3494]" />
                  <span>Rocket (Dutch-Bangla) — 1.8%</span>
                </li>
              </ul>
            </div>

            {/* Compliance */}
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3">
                Compliance & Security
              </div>
              <ul className="space-y-2">
                <li>
                  <a href="/public/.well-known/security.txt" className="hover:text-upay-400 transition-colors">
                    Security Disclosure (security.txt)
                  </a>
                </li>
                <li>
                  <span className="text-slate-400">Zero PII Data Minimization</span>
                </li>
                <li>
                  <span className="text-slate-400">Bangladesh Bank PSD Guidelines</span>
                </li>
                <li>
                  <span className="text-slate-400">Deterministic Decimal Engine</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-navy-800/80 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-[11px] text-slate-500 text-center sm:text-left">
              &copy; 2026 Sohoj Financial Intelligence. Built with pride for Bangladesh&apos;s digital economy. Powered by Upay MFS &amp; Google Gemini.
            </div>
            <div className="flex items-center gap-4 text-[11px] text-slate-400">
              <span className="inline-flex items-center gap-1.5 text-emerald-400 font-semibold">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                Telemetry Systems Operational
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
