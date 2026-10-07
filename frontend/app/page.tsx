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
import { DynamicGoldTakaCoin, DynamicParticleWave } from "@/components/canvas/ThreeDVisuals";
import { ParallaxGlassCard } from "@/components/canvas/ParallaxGlassCard";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { BorderBeam } from "@/components/ui/BorderBeam";
import { RollingOdometer } from "@/components/ui/RollingOdometer";
import { MagneticButton } from "@/components/ui/MagneticButton";
import { CurrencyAmount } from "@/components/ui/CurrencyAmount";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, isAuthenticated } = useAuth();

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
      tagColor: "bg-amber-500/10 text-amber-700 border-amber-500/30",
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
      tagColor: "bg-cyan-500/10 text-cyan-700 border-cyan-500/30",
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
      tagColor: "bg-amber-500/10 text-amber-800 border-amber-500/30",
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
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-upay-500 selection:text-navy-950 font-sans">
      {/* 1. Sleek Navigation Bar */}
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-upay-500 text-navy-950 font-black text-xl shadow-lg upay-glow transition-transform duration-300 group-hover:scale-105">
              S
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-2xl font-black tracking-tight text-slate-900">Sohoj</span>
                <span className="rounded-md bg-upay-500/20 px-2 py-0.5 text-xs font-bold text-amber-700 border border-upay-500/30">
                  Upay
                </span>
              </div>
              <span className="text-[10px] uppercase font-bold tracking-widest text-slate-500">
                AI Financial Copilot
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
            <a href="#features" className="hover:text-amber-600 transition-colors">
              Features
            </a>
            <a href="#simulator" className="hover:text-amber-600 transition-colors">
              Live Simulator
            </a>
            <a href="#personas" className="hover:text-amber-600 transition-colors">
              Personas
            </a>
            <a href="#security" className="hover:text-amber-600 transition-colors">
              Security & Compliance
            </a>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-slate-700 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="truncate max-w-[120px]">{user?.full_name?.split(" ")[0] || "User"}</span>
                </div>
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-upay-500 text-navy-950 font-bold text-sm shadow-md hover:bg-upay-400 hover:scale-[1.02] active:scale-[0.98] transition-all upay-glow"
                >
                  Dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="hidden sm:inline-flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition-all border border-slate-300/80 shadow-sm"
                >
                  Sign In
                </Link>
                <Link
                  href="/login?redirect=/dashboard"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-upay-500 text-navy-950 font-bold text-sm shadow-md hover:bg-upay-400 hover:scale-[1.02] active:scale-[0.98] transition-all upay-glow"
                >
                  Launch App
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28 mesh-gradient-hero fintech-grid-light">
        {/* GPU 3D Particle Wave Field */}
        <DynamicParticleWave />

        {/* Ambient background glows */}
        <div className="pointer-events-none absolute top-12 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-upay-500/10 blur-[130px] rounded-full" />
        <div className="pointer-events-none absolute top-40 right-10 w-[400px] h-[300px] bg-slate-300/30 blur-[120px] rounded-full" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center text-left">
            {/* Left Column: Value Prop & Magnetic CTAs */}
            <div className="lg:col-span-7 space-y-6">
              {/* Dynamic Pill */}
              <div
                className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/90 border border-slate-300 text-xs font-semibold text-slate-700 shadow-sm badge-glow animate-pulse-subtle animate-fade-in-up"
                style={{ "--stagger": 0 } as React.CSSProperties}
              >
                <span className="flex h-2 w-2 rounded-full bg-upay-500 animate-ping" />
                <span className="flex h-2 w-2 rounded-full bg-upay-500 -ml-4" />
                <span className="text-amber-700 font-bold">Bangladesh&apos;s First AI Financial Copilot</span>
                <span className="text-slate-300">|</span>
                <span className="text-slate-600">Upay MFS Intelligence</span>
              </div>

              {/* Headline */}
              <h1
                className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tighter text-slate-900 leading-[1.08] animate-fade-in-up"
                style={{ "--stagger": 1 } as React.CSSProperties}
              >
                Turn Every MFS Taka Into <br />
                <span className="bg-gradient-to-r from-amber-500 via-upay-500 to-amber-600 bg-clip-text text-transparent">
                  Compounded Wealth
                </span>
              </h1>

              {/* Subtitle */}
              <p
                className="max-w-2xl text-base sm:text-lg text-slate-600 leading-relaxed font-normal animate-fade-in-up"
                style={{ "--stagger": 2 } as React.CSSProperties}
              >
                Autonomous forecasting, deterministic wealth simulation, and grounded AI coaching. Seamlessly integrated with Upay and Bangladesh MFS networks with zero PII exposure.
              </p>

              {/* Magnetic Hero CTAs */}
              <div
                className="pt-2 flex flex-wrap items-center gap-4 animate-fade-in-up"
                style={{ "--stagger": 3 } as React.CSSProperties}
              >
                <Link href={isAuthenticated ? "/dashboard" : "/login?redirect=/dashboard"}>
                  <MagneticButton
                    variant="primary"
                    icon={<ArrowRight className="h-4 w-4" />}
                  >
                    {isAuthenticated ? "Open Dashboard" : "Launch Dashboard"}
                  </MagneticButton>
                </Link>
                <a href="#simulator">
                  <MagneticButton
                    variant="secondary"
                    icon={<Calculator className="h-4 w-4 text-upay-400" />}
                  >
                    Try Live Simulator
                  </MagneticButton>
                </a>
              </div>
            </div>

            {/* Right Column: Interactive 3D Gold Taka Coin */}
            <div className="lg:col-span-5 flex flex-col items-center justify-center relative">
              <div className="relative">
                {/* Luminous aura behind coin */}
                <div className="pointer-events-none absolute inset-0 rounded-full bg-upay-500/15 blur-3xl scale-125" />
                <DynamicGoldTakaCoin />
              </div>
              <span className="mt-1 text-[11px] font-mono uppercase tracking-widest text-slate-500 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-upay-400 animate-ping" />
                Interactive 3D Taka Token • Drag to Spin
              </span>
            </div>
          </div>

          {/* Live Trust & Metrics Row */}
          <div className="mt-16 pt-8 border-t border-slate-200/80 grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 max-w-5xl mx-auto">
            <SpotlightCard variant="light" className="p-5 rounded-2xl text-center bg-white border border-slate-200/90 shadow-sm" withDoubleBezel={false}>
              <div className="text-3xl sm:text-4xl font-black text-amber-500">
                <RollingOdometer value={45} prefix="৳" className="text-3xl sm:text-4xl font-black text-amber-500" />
                <span>M+</span>
              </div>
              <div className="mt-1.5 text-xs text-slate-600 font-semibold">Simulated Wealth Volume</div>
            </SpotlightCard>
            <SpotlightCard variant="light" className="p-5 rounded-2xl text-center bg-white border border-slate-200/90 shadow-sm" withDoubleBezel={false}>
              <div className="text-2xl sm:text-3xl font-black text-slate-900">0.8% - 1.4%</div>
              <div className="mt-1.5 text-xs text-slate-600 font-semibold">Upay Tariff Optimization</div>
            </SpotlightCard>
            <SpotlightCard variant="light" className="p-5 rounded-2xl text-center bg-white border border-slate-200/90 shadow-sm" withDoubleBezel={false}>
              <div className="text-2xl sm:text-3xl font-black text-amber-500">100% Grounded</div>
              <div className="mt-1.5 text-xs text-slate-600 font-semibold">Strict Math Guardrails</div>
            </SpotlightCard>
            <SpotlightCard variant="light" className="p-5 rounded-2xl text-center bg-white border border-slate-200/90 shadow-sm" withDoubleBezel={false}>
              <div className="text-2xl sm:text-3xl font-black text-slate-900">Zero PII</div>
              <div className="mt-1.5 text-xs text-slate-600 font-semibold">HMAC-SHA256 Tokenized</div>
            </SpotlightCard>
          </div>
        </div>
      </section>

      {/* 3. Interactive Live Simulation & Coach Preview Widget */}
      <section id="simulator" className="py-20 md:py-28 relative bg-slate-100/60 border-t border-slate-200/80">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12 animate-fade-in-up">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-upay-500/10 border border-upay-500/30 text-xs font-bold text-amber-700 mb-3">
              <Calculator className="h-3.5 w-3.5" />
              Interactive Sandbox
            </div>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
              Test The Financial Engine Live
            </h2>
            <p className="mt-4 text-slate-600 text-base sm:text-lg">
              No account required. Experiment with Bangladesh bank DPS compounding or calculate your exact Upay tariff savings instantly.
            </p>
          </div>

          {/* Interactive Widget Box with Double-Bezel and BorderBeam */}
          <div className="relative max-w-4xl mx-auto">
            <SpotlightCard variant="light" className="shadow-xl overflow-hidden relative bg-white border border-slate-200/80" withDoubleBezel={true}>
              <BorderBeam size={180} duration={8} colorFrom="#FFC709" colorTo="#1E4D9F" />

              {/* Tab Switcher */}
              <div className="flex items-center justify-center gap-3 p-1.5 rounded-2xl bg-slate-100 border border-slate-200 max-w-md mx-auto mb-8">
                <button
                  onClick={() => setActiveWidgetTab("compound")}
                  className={`flex-1 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                    activeWidgetTab === "compound"
                      ? "bg-upay-500 text-navy-950 shadow-md upay-glow"
                      : "text-slate-600 hover:text-slate-900"
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
                      : "text-slate-600 hover:text-slate-900"
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
                        <span className="text-slate-700">Monthly DPS Contribution</span>
                        <span className="text-amber-600 font-bold text-base">
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
                        className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
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
                        <span className="text-slate-700">Annual Return / DPS Rate</span>
                        <span className="text-amber-600 font-bold text-base">{returnRate}%</span>
                      </div>
                      <input
                        type="range"
                        min={5.0}
                        max={12.0}
                        step={0.5}
                        value={returnRate}
                        onChange={(e) => setReturnRate(Number(e.target.value))}
                        className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
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
                        <span className="text-slate-700">Investment Horizon</span>
                        <span className="text-amber-600 font-bold text-base">{years} Years</span>
                      </div>
                      <input
                        type="range"
                        min={1}
                        max={15}
                        step={1}
                        value={years}
                        onChange={(e) => setYears(Number(e.target.value))}
                        className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
                      />
                      <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                        <span>1 Year</span>
                        <span>5 Years</span>
                        <span>15 Years</span>
                      </div>
                    </div>

                    {/* Grounded Explanation Box */}
                    <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200/80 text-xs text-slate-700 leading-relaxed flex items-start gap-2.5">
                      <CheckCircle2 className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                      <span>
                        Grounded Rule of 72: At <strong>{returnRate}%</strong>, your deposited capital doubles every{" "}
                        <strong className="text-amber-700 font-bold">{compoundCalculation.doublingYears} years</strong> without risking principal.
                      </span>
                    </div>
                  </div>

                  {/* Calculation Output Card (Executive Navy Terminal) */}
                  <div className="lg:col-span-5 rounded-2xl bg-gradient-to-br from-[#0A1C3C] via-[#0D234C] to-[#061325] border border-navy-800 p-6 flex flex-col justify-between shadow-xl text-white">
                    <div>
                      <div className="text-xs uppercase tracking-wider font-extrabold text-slate-300 mb-1">
                        Projected Maturity Value
                      </div>
                      <div className="mt-1">
                        <RollingOdometer
                          value={compoundCalculation.futureValue}
                          prefix="৳"
                          className="text-3xl sm:text-4xl font-black text-upay-400"
                        />
                      </div>
                      <div className="text-xs text-emerald-400 font-semibold mt-1">
                        +৳ {compoundCalculation.interestEarned.toLocaleString("en-BD")} pure compound gain
                      </div>

                      <div className="mt-6 space-y-3 pt-4 border-t border-white/10">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-300">Total Capital Saved:</span>
                          <span className="font-bold text-white">
                            ৳ {compoundCalculation.principal.toLocaleString("en-BD")}
                          </span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-300">Compound Returns:</span>
                          <span className="font-bold text-upay-400">
                            +৳ {compoundCalculation.interestEarned.toLocaleString("en-BD")}
                          </span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-300">Doubling Cycle:</span>
                          <span className="font-bold text-cyan-300">
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
                        <span className="text-slate-700">Single Cash-Out Amount</span>
                        <span className="text-amber-600 font-bold text-base">
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
                        className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#FFC709]"
                      />
                      <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                        <span>৳500</span>
                        <span>৳10,000</span>
                        <span>৳25,000</span>
                      </div>
                    </div>

                    {/* Channel Selector */}
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
                        Cash-Out Channel
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          onClick={() => setSelectedChannel("agent")}
                          className={`p-3 rounded-xl border text-xs font-bold transition-all ${
                            selectedChannel === "agent"
                              ? "bg-upay-500 text-navy-950 border-upay-500 shadow-md"
                              : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                          }`}
                        >
                          Upay Agent (1.4%)
                        </button>
                        <button
                          onClick={() => setSelectedChannel("atm")}
                          className={`p-3 rounded-xl border text-xs font-bold transition-all ${
                            selectedChannel === "atm"
                              ? "bg-upay-500 text-navy-950 border-upay-500 shadow-md"
                              : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                          }`}
                        >
                          UCB ATM (0.8%)
                        </button>
                        <button
                          onClick={() => setSelectedChannel("app")}
                          className={`p-3 rounded-xl border text-xs font-bold transition-all ${
                            selectedChannel === "app"
                              ? "bg-upay-500 text-navy-950 border-upay-500 shadow-md"
                              : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                          }`}
                        >
                          Upay App / POS (1.4%)
                        </button>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200/80 text-xs text-slate-700 leading-relaxed flex items-start gap-2.5">
                      <Award className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                      <span>
                        Standard market cash-out tariffs average <strong>1.85% (৳18.5/1000)</strong>. Upay provides the country&apos;s lowest ATM tariff at{" "}
                        <strong className="text-amber-700">0.8%</strong> and agent tariff at{" "}
                        <strong className="text-amber-700">1.4%</strong>.
                      </span>
                    </div>
                  </div>

                  {/* Tariff Output Card (Executive Navy Terminal) */}
                  <div className="lg:col-span-5 rounded-2xl bg-gradient-to-br from-[#0A1C3C] via-[#0D234C] to-[#061325] border border-navy-800 p-6 flex flex-col justify-between shadow-xl text-white">
                    <div>
                      <div className="text-xs uppercase tracking-wider font-extrabold text-slate-300 mb-1">
                        Upay Tariff Fee
                      </div>
                      <div className="mt-1">
                        <RollingOdometer
                          value={tariffCalculation.upayFee}
                          prefix="৳"
                          className="text-3xl sm:text-4xl font-black text-upay-400"
                        />
                      </div>
                      <div className="text-xs text-slate-400 line-through mt-0.5">
                        Competitor Fee: ৳ {tariffCalculation.competitorFee.toLocaleString("en-BD")}
                      </div>

                      <div className="mt-6 space-y-3 pt-4 border-t border-white/10">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-300">Savings This Withdrawal:</span>
                          <span className="font-bold text-emerald-400">
                            ৳ {tariffCalculation.perTxSavings.toLocaleString("en-BD")} saved
                          </span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-300">Annual Friction Saved:</span>
                          <span className="font-bold text-upay-400">
                            ৳ {tariffCalculation.annualSavings.toLocaleString("en-BD")} / year
                          </span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-300">Effective Tariff Rate:</span>
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
            </SpotlightCard>
          </div>
        </div>
      </section>

      {/* 4. Four Core Pillars Grid */}
      <section id="features" className="py-20 md:py-28 relative bg-white border-t border-slate-200/80">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-bold text-slate-700 mb-3">
              <Sparkles className="h-3.5 w-3.5 text-amber-600" />
              Platform Architecture
            </div>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
              Engineered For Financial Clarity
            </h2>
            <p className="mt-4 text-slate-600 text-base sm:text-lg">
              Four grounded pillars uniting mathematical determinism, machine learning forecasting, and localized MFS intelligence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 sm:gap-8">
            {/* Pillar 1 */}
            <div className="md:col-span-7 animate-fade-in-scale" style={{ "--stagger": 1 } as React.CSSProperties}>
              <SpotlightCard variant="light" className="h-full flex flex-col justify-between p-8 bg-white border border-slate-200/90 shadow-sm hover:shadow-lg transition-all" withDoubleBezel={false}>
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-600">
                      <TrendingUp className="h-6 w-6" />
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 border border-slate-200">
                      Predictive Engine
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">
                    Autonomous Expense Forecasting
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    Hybrid statistical projection trained on localized MFS spending velocity. Predicts 7-day and 30-day cash drains, factoring in salary dates, utility deadlines, and festival seasonality like Eid-ul-Fitr and Puja.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-amber-700 font-semibold">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Prevents overdrafts before they happen</span>
                </div>
              </SpotlightCard>
            </div>

            {/* Pillar 2 */}
            <div className="md:col-span-5 animate-fade-in-scale" style={{ "--stagger": 2 } as React.CSSProperties}>
              <SpotlightCard variant="light" className="h-full flex flex-col justify-between p-8 bg-white border border-slate-200/90 shadow-sm hover:shadow-lg transition-all" withDoubleBezel={false} spotlightColor="rgba(0, 210, 255, 0.14)">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-600">
                      <Bot className="h-6 w-6" />
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 border border-slate-200">
                      Gemini 1.5 Flash
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">
                    Grounded AI Financial Coach
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    Conversational assistant with strict tool-calling boundaries. Powered by Gemini with numeric function verification against actual Upay tariff sheets. Never provides hallucinated rates or speculative stock bets.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-cyan-600 font-semibold">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Strict prompt-injected math guardrails</span>
                </div>
              </SpotlightCard>
            </div>

            {/* Pillar 3 */}
            <div className="md:col-span-5 animate-fade-in-scale" style={{ "--stagger": 3 } as React.CSSProperties}>
              <SpotlightCard variant="light" className="h-full flex flex-col justify-between p-8 bg-white border border-slate-200/90 shadow-sm hover:shadow-lg transition-all" withDoubleBezel={false} spotlightColor="rgba(245, 158, 11, 0.14)">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-600">
                      <Calculator className="h-6 w-6" />
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 border border-slate-200">
                      Deterministic Math
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">
                    Deterministic Compound Simulator
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    Pure Python and TypeScript Decimal math. Computes future values, exact logarithmic doubling times via the Rule of 72, and target goal amortization schedules with zero floating point drift.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-amber-700 font-semibold">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Arbitrary-precision arithmetic</span>
                </div>
              </SpotlightCard>
            </div>

            {/* Pillar 4 */}
            <div className="md:col-span-7 animate-fade-in-scale" style={{ "--stagger": 4 } as React.CSSProperties}>
              <SpotlightCard variant="light" className="h-full flex flex-col justify-between p-8 bg-white border border-slate-200/90 shadow-sm hover:shadow-lg transition-all" withDoubleBezel={false} spotlightColor="rgba(244, 63, 94, 0.14)">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-600">
                      <Activity className="h-6 w-6" />
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 border border-slate-200">
                      Z-Score Anomaly Trigger
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">
                    MFS Behavioral Archetypes & Anomalies
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    Automatically classifies user telemetry into 6 behavioral archetypes (Volatile Earner, Impulsive Micro-Spender, Family Trustee, etc.). Detects velocity spikes, unexpected midnight transfers, and unauthorized drains.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-rose-600 font-semibold">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Flags anomalous drain before funds evaporate</span>
                </div>
              </SpotlightCard>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Persona Switcher Showcase */}
      <section id="personas" className="py-20 md:py-28 relative bg-slate-50 border-t border-slate-200/80">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-upay-500/10 border border-upay-500/30 text-xs font-bold text-amber-700 mb-3">
              <User className="h-3.5 w-3.5" />
              Real Personas
            </div>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
              Built For Real Bangladeshi Lives
            </h2>
            <p className="mt-4 text-slate-600 text-base sm:text-lg">
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
                    : "bg-white border-slate-200 text-slate-700 hover:bg-slate-100 hover:border-slate-300 shadow-sm"
                }`}
              >
                <span>{persona.name}</span>
                <span className="text-xs opacity-75 font-normal">({persona.role.split("&")[0]})</span>
              </button>
            ))}
          </div>

          {/* Persona Card Detail */}
          <div className="max-w-4xl mx-auto rounded-3xl bg-white border border-slate-200/90 p-8 sm:p-12 shadow-xl relative overflow-hidden transition-all duration-500 ease-out">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center transition-all duration-500 ease-out" key={activePersonaIndex}>
              <div className="md:col-span-8 space-y-4">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h3 className="text-2xl sm:text-3xl font-black text-slate-900">
                    {currentPersona.name}
                  </h3>
                  <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
                    {currentPersona.location}
                  </span>
                  <span className={`text-xs px-2.5 py-1 rounded-lg font-bold border ${currentPersona.tagColor}`}>
                    {currentPersona.archetype}
                  </span>
                </div>

                <div className="text-sm font-semibold text-slate-600">
                  Monthly Cash Flow: <span className="text-slate-900 font-bold">{currentPersona.income}</span>
                </div>

                <blockquote className="italic text-slate-700 text-base border-l-4 border-upay-500 pl-4 py-2 bg-slate-50/80 rounded-r-xl">
                  &ldquo;{currentPersona.quote}&rdquo;
                </blockquote>

                <div className="space-y-3 pt-3">
                  <div>
                    <span className="text-xs uppercase font-extrabold tracking-wider text-rose-600">The Friction:</span>
                    <p className="text-sm text-slate-700 mt-0.5">{currentPersona.problem}</p>
                  </div>
                  <div>
                    <span className="text-xs uppercase font-extrabold tracking-wider text-amber-700">Sohoj Intervention:</span>
                    <p className="text-sm text-slate-700 mt-0.5">{currentPersona.solution}</p>
                  </div>
                </div>
              </div>

              {/* Persona Stat & 3D Interactive Holographic Card */}
              <div className="md:col-span-4 flex flex-col items-center justify-center space-y-3">
                <ParallaxGlassCard
                  cardHolder={
                    activePersonaIndex === 0
                      ? "SUMAIYA TALUKDER"
                      : activePersonaIndex === 1
                      ? "ROKSANA PARVEEN"
                      : "KAMRUL HASAN"
                  }
                  maskedPan={
                    activePersonaIndex === 0
                      ? "•••• •••• •••• 8421"
                      : activePersonaIndex === 1
                      ? "•••• •••• •••• 3190"
                      : "•••• •••• •••• 9054"
                  }
                  balanceTaka={
                    activePersonaIndex === 0
                      ? "৳ 38,500.00"
                      : activePersonaIndex === 1
                      ? "৳ 14,500.00"
                      : "৳ 65,000.00"
                  }
                  tier={
                    activePersonaIndex === 0
                      ? "UPAY GIG PILOT"
                      : activePersonaIndex === 1
                      ? "UPAY CAMPUS DPS"
                      : "UPAY SHARIAH TRUST"
                  }
                />
                <div className="w-full rounded-2xl bg-gradient-to-br from-[#0A1C3C] to-[#061325] border border-navy-800 p-4 text-center shadow-md text-white">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-300">
                    Verified Outcome
                  </div>
                  <div className="text-2xl font-black text-upay-400 mt-0.5">
                    {currentPersona.statNumber}
                  </div>
                  <div className="text-xs font-semibold text-slate-300">
                    {currentPersona.statLabel}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Security & MFS Compliance Banner */}
      <section id="security" className="py-20 md:py-24 relative bg-white border-t border-slate-200/80">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-3xl bg-gradient-to-br from-[#0A1C3C] via-[#0D234C] to-[#061325] border border-navy-800 p-8 sm:p-12 shadow-2xl relative overflow-hidden text-white">
            <div className="pointer-events-none absolute -left-16 -top-16 w-64 h-64 bg-cyan-500/10 blur-[90px] rounded-full" />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 space-y-4">
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
                      <strong className="text-white">Zero Raw SMS Storage:</strong> Transactions extracted in transient RAM only.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-upay-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">
                      <strong className="text-white">Upay Tariff Optimization:</strong> Bangladesh Bank PSD regulatory guidelines compliant.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-upay-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">
                      <strong className="text-white">Client-Side Tokenization:</strong> Strict role-based JWT sessions with instant expiry.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-upay-400 shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">
                      <strong className="text-white">Grounded Boundaries:</strong> AI coach restricted from offering unverified financial speculation.
                    </span>
                  </div>
                </div>
              </div>

              {/* Compliance Visual Badge */}
              <div className="lg:col-span-5 flex flex-col items-center justify-center p-8 rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 text-center text-white">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-upay-500/20 border border-upay-500/40 text-upay-400 mb-4 upay-glow">
                  <Lock className="h-8 w-8" />
                </div>
                <div className="text-lg font-bold text-white">Bangladesh Bank MFS Aligned</div>
                <div className="text-xs text-slate-300 mt-1 max-w-xs">
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
      <section className="py-20 relative bg-gradient-to-b from-[#0A1C3C] to-[#061325] text-center text-white border-t border-slate-200/20">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 animate-fade-in-up">
          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            Ready To Stop Leaking Money On MFS Fees?
          </h2>
          <p className="mt-4 text-slate-300 text-base sm:text-lg max-w-2xl mx-auto">
            Join thousands of smart earners in Bangladesh optimizing their Mobile Financial Services with deterministic math and grounded AI.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link href={isAuthenticated ? "/dashboard" : "/login?redirect=/dashboard"}>
              <MagneticButton
                variant="primary"
                icon={<ArrowRight className="h-5 w-5" />}
              >
                {isAuthenticated ? "Open Sohoj Dashboard" : "Launch Sohoj Copilot"}
              </MagneticButton>
            </Link>
            <Link href={isAuthenticated ? "/dashboard" : "/register"}>
              <MagneticButton variant="secondary">
                {isAuthenticated ? "View Telemetry" : "Create Free Account"}
              </MagneticButton>
            </Link>
          </div>
        </div>
      </section>

      {/* 8. Polished Footer */}
      <footer className="border-t border-slate-200 bg-white py-14 text-slate-600 text-xs">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
            {/* Brand Column */}
            <div className="space-y-3 md:col-span-1">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-upay-500 text-navy-950 font-black text-sm">
                  S
                </div>
                <span className="text-lg font-black text-slate-900 tracking-tight">Sohoj Upay</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Autonomous financial copilot for Mobile Financial Services users across Bangladesh.
              </p>
              <div className="text-[11px] text-slate-500 font-medium">
                Brand Partner: Upay (UCB Fintech Alliance)
              </div>
            </div>

            {/* Platform Links */}
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3">
                Platform
              </div>
              <ul className="space-y-2">
                <li>
                  <Link href={isAuthenticated ? "/dashboard" : "/login?redirect=/dashboard"} className="hover:text-amber-600 transition-colors">
                    Dashboard Overview
                  </Link>
                </li>
                <li>
                  <Link href={isAuthenticated ? "/simulator" : "/login?redirect=/simulator"} className="hover:text-amber-600 transition-colors">
                    Wealth Simulator
                  </Link>
                </li>
                <li>
                  <Link href={isAuthenticated ? "/transactions" : "/login?redirect=/transactions"} className="hover:text-amber-600 transition-colors">
                    Transaction Telemetry
                  </Link>
                </li>
                <li>
                  <Link href={isAuthenticated ? "/coach" : "/login?redirect=/coach"} className="hover:text-amber-600 transition-colors">
                    Grounded AI Coach
                  </Link>
                </li>
              </ul>
            </div>

            {/* MFS Providers */}
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3">
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
              <div className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3">
                Compliance & Security
              </div>
              <ul className="space-y-2">
                <li>
                  <a href="/public/.well-known/security.txt" className="hover:text-amber-600 transition-colors">
                    Security Disclosure (security.txt)
                  </a>
                </li>
                <li>
                  <span className="text-slate-500">Zero PII Data Minimization</span>
                </li>
                <li>
                  <span className="text-slate-500">Bangladesh Bank PSD Guidelines</span>
                </li>
                <li>
                  <span className="text-slate-500">Deterministic Decimal Engine</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-[11px] text-slate-500 text-center sm:text-left">
              &copy; 2026 Sohoj Financial Intelligence. Built with pride for Bangladesh&apos;s digital economy. Powered by Upay MFS &amp; Google Gemini.
            </div>
            <div className="flex items-center gap-4 text-[11px] text-slate-500">
              <span className="inline-flex items-center gap-1.5 text-amber-700 font-semibold">
                <span className="h-2 w-2 rounded-full bg-upay-500 animate-pulse" />
                Telemetry Systems Operational
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
