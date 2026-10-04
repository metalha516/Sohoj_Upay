"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Sparkles, ShieldCheck, Lock, EyeOff, CheckCircle } from "lucide-react";

interface ConsentGateProps {
  onConsentGranted?: () => void;
}

export function ConsentGate({ onConsentGranted }: ConsentGateProps) {
  const { updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGrantConsent = async () => {
    try {
      setLoading(true);
      setError(null);
      await updateUser({ consent_ai: true });
      onConsentGranted?.();
    } catch (err: any) {
      setError(err.message || "Failed to enable AI features. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl py-12 px-4 sm:px-6">
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-navy-900 text-upay-yellow border border-navy-800 shadow-sm">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-black text-navy-900">AI Financial Coach Consent</h2>
            <p className="text-sm text-slate-500 font-medium">
              Personalized, privacy-first guidance for your financial wellness
            </p>
          </div>
        </div>

        <div className="space-y-4 my-6 text-sm text-slate-600 font-medium">
          <p className="leading-relaxed">
            Sohoj AI Coach analyzes your transaction aggregates, savings rates, and goals to provide
            grounded coaching, affordability checks, and savings strategies.
          </p>

          <div className="rounded-xl bg-slate-50/80 border border-slate-200/80 p-4 space-y-3">
            <div className="flex items-start gap-3">
              <ShieldCheck className="h-5 w-5 text-navy-900 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-navy-900">Strict Data Minimization:</span>
                <span className="text-slate-600 ml-1">
                  Only compact numerical aggregates are queried. Names, phone numbers, emails, and raw transaction notes are never sent to language models.
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <EyeOff className="h-5 w-5 text-navy-900 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-navy-900">Zero Model Training:</span>
                <span className="text-slate-600 ml-1">
                  Your conversations and personal data are strictly isolated and never used for foundation model pre-training.
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Lock className="h-5 w-5 text-navy-900 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-navy-900">Revocable Anytime:</span>
                <span className="text-slate-600 ml-1">
                  You can withdraw consent at any time in Account Settings, immediately cutting AI processing.
                </span>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700 border border-rose-200">
            {error}
          </div>
        )}

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <CheckCircle className="h-4 w-4 text-navy-900" />
            <span>Bangladeshi Personal Data Protection standards applied</span>
          </div>

          <button
            onClick={handleGrantConsent}
            disabled={loading}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-navy-900 px-6 py-3 text-sm font-bold text-upay-yellow shadow-sm hover:bg-navy-800 focus:outline-none focus:ring-2 focus:ring-navy-900 disabled:opacity-50 transition-colors border border-navy-800"
          >
            {loading ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-upay-yellow border-t-transparent" />
                <span>Enabling Coach...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Enable AI Financial Coach</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
