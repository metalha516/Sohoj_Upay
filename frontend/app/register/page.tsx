"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { User, Mail, Lock, Phone, Briefcase, ArrowRight, AlertCircle, Shield } from "lucide-react";

export default function RegisterPage() {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [occupation, setOccupation] = useState("salaried_private");
  const [startingBalance, setStartingBalance] = useState("5000");
  const [consentAi, setConsentAi] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await register({
        full_name: fullName,
        email,
        phone_number: phone,
        password,
        occupation,
        starting_balance: parseFloat(startingBalance) || 0,
        consent_ai: consentAi,
      });
    } catch (err: any) {
      setError(err.problem?.detail || err.message || "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-slate-50 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <Link
            href="/"
            className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-white font-black text-lg shadow-sm"
          >
            SU
          </Link>
          <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-slate-900">
            Create Shohoj Upay Account
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Intelligent financial coaching grounded in MFS reality
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
          {error && (
            <div className="mb-5 flex items-center gap-2 rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="reg-name"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="reg-name"
                  type="text"
                  required
                  placeholder="Shamima Akhter"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="reg-email"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="reg-email"
                  type="email"
                  required
                  placeholder="shamima@example.test"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="reg-phone"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Phone Number (Bangladesh)
              </label>
              <div className="relative">
                <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="reg-phone"
                  type="tel"
                  required
                  placeholder="+8801712345678"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="reg-password"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Password (min 8 chars)
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="reg-password"
                  type="password"
                  required
                  minLength={8}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label
                  htmlFor="reg-occ"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
                >
                  Occupation
                </label>
                <select
                  id="reg-occ"
                  value={occupation}
                  onChange={(e) => setOccupation(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 bg-white"
                >
                  <option value="salaried_private">Private Job</option>
                  <option value="salaried_public">Govt Service</option>
                  <option value="rmg_worker">RMG Worker</option>
                  <option value="micro_merchant">Micro Merchant</option>
                  <option value="ride_share_driver">Ride Share Driver</option>
                  <option value="freelancer">Freelancer</option>
                  <option value="student">Student</option>
                  <option value="homemaker_remittance_recipient">Homemaker</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="reg-balance"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
                >
                  Starting MFS ৳
                </label>
                <input
                  id="reg-balance"
                  type="number"
                  min="0"
                  value={startingBalance}
                  onChange={(e) => setStartingBalance(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>
            </div>

            {/* AI Consent Checkbox */}
            <div className="rounded-xl bg-emerald-50/60 border border-emerald-100 p-3">
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consentAi}
                  onChange={(e) => setConsentAi(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500"
                />
                <div className="text-xs text-slate-700">
                  <span className="font-bold text-emerald-950">
                    Consent to AI Coaching (`consent_ai`)
                  </span>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Allow Shohoj Upay to analyze aggregate spending to deliver personalized insights.
                  </p>
                </div>
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 transition"
            >
              {isLoading ? "Creating Account..." : "Create Shohoj Upay Account"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-bold text-emerald-600 hover:text-emerald-500">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
