"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import { formatBDT, formatDate } from "@/lib/formatters";
import {
  User as UserIcon,
  Mail,
  Phone,
  Briefcase,
  Wallet,
  Calendar,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [occupation, setOccupation] = useState(user?.occupation || "salaried_private");
  const [monthlyIncome, setMonthlyIncome] = useState(
    user?.monthly_income ? user.monthly_income.toString() : ""
  );
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      await updateUser({
        full_name: fullName.trim(),
        occupation,
        monthly_income: monthlyIncome ? parseFloat(monthlyIncome) : null,
      });
      setSuccessMsg("Profile updated successfully");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20 md:pb-12">
      <AppHeader />

      <main className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 pt-6">
        <div className="pb-6">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            User Profile
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Account identity, socioeconomic classification, and baseline metrics
          </p>
        </div>

        {successMsg && (
          <div className="mb-4 flex items-center gap-2 rounded-xl bg-upay-yellow/20 border border-upay-yellow/40 p-3 text-xs text-navy-900 font-medium">
            <CheckCircle2 className="h-4 w-4" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="mb-4 flex items-center gap-2 rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-800">
            <AlertCircle className="h-4 w-4" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-md hover:-translate-y-1 space-y-6">
          {/* Identity Header */}
          <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
            <div className="h-16 w-16 rounded-2xl bg-navy-900 text-upay-yellow flex items-center justify-center font-bold text-2xl shadow-sm border border-navy-800">
              {user?.full_name ? user.full_name[0] : "U"}
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">{user?.full_name}</h2>
              <p className="text-xs text-slate-500">{user?.email}</p>
              <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                <Calendar className="h-3 w-3" />
                <span>Member since {formatDate(user?.created_at)}</span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="prof-name"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
              >
                Full Name
              </label>
              <input
                id="prof-name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                  Email (Immutable)
                </label>
                <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-500">
                  <Mail className="h-4 w-4" />
                  <span>{user?.email}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                  Phone (Immutable)
                </label>
                <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-500">
                  <Phone className="h-4 w-4" />
                  <span>{user?.phone_number}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="prof-occ"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
                >
                  Occupation Segment
                </label>
                <select
                  id="prof-occ"
                  value={occupation}
                  onChange={(e) => setOccupation(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 bg-white"
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
                  htmlFor="prof-income"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1"
                >
                  Estimated Monthly Income (৳)
                </label>
                <input
                  id="prof-income"
                  type="number"
                  placeholder="35000"
                  value={monthlyIncome}
                  onChange={(e) => setMonthlyIncome(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Baseline Starting MFS Balance
              </label>
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-600">
                <Wallet className="h-4 w-4 text-navy-900" />
                <span className="font-bold">{formatBDT(user?.starting_balance)}</span>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSaving}
                className="rounded-xl bg-slate-900 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50 transition"
              >
                {isSaving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      </main>

      <AppBottomNav />
    </div>
  );
}
