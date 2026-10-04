"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { apiClient } from "@/lib/api-client";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import {
  Shield,
  Download,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Lock,
} from "lucide-react";

export default function SettingsPage() {
  const { user, updateUser, logout } = useAuth();
  const [consentAi, setConsentAi] = useState<boolean>(user?.consent_ai ?? true);
  const [isUpdatingConsent, setIsUpdatingConsent] = useState(false);
  const [consentSuccess, setConsentSuccess] = useState(false);

  const [isExporting, setIsExporting] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");

  const handleConsentToggle = async (checked: boolean) => {
    setConsentAi(checked);
    setIsUpdatingConsent(true);
    setConsentSuccess(false);
    try {
      await updateUser({ consent_ai: checked });
      setConsentSuccess(true);
      setTimeout(() => setConsentSuccess(false), 3000);
    } finally {
      setIsUpdatingConsent(false);
    }
  };

  const handleExportData = async () => {
    setIsExporting(true);
    try {
      const blob = await apiClient.exportUserData();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `shohoj-upay-data-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert("Failed to export data: " + (err.message || "Network error"));
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") return;
    setIsDeleting(true);
    try {
      await apiClient.deleteAccount();
      await logout();
    } catch (err: any) {
      alert("Failed to delete account: " + (err.message || "Server error"));
      setIsDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20 md:pb-12">
      <AppHeader />

      <main className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 pt-6">
        <div className="pb-6">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            Privacy & Account Settings
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Control your AI consent, download encrypted archives, and manage data retention
          </p>
        </div>

        <div className="space-y-6">
          {/* Section 1: AI Usage & Consent */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="rounded-xl bg-emerald-50 p-2 text-emerald-600">
                  <Shield className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    AI Coaching & Behavioral Consent
                  </h2>
                  <p className="text-xs text-slate-500">
                    Governs external LLM feature aggregates and personalized coaching
                  </p>
                </div>
              </div>

              {consentSuccess && (
                <span className="flex items-center gap-1 text-xs text-emerald-600 font-semibold">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Saved
                </span>
              )}
            </div>

            <div className="mt-5 rounded-xl border border-slate-100 bg-slate-50 p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consentAi}
                  disabled={isUpdatingConsent}
                  onChange={(e) => handleConsentToggle(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500"
                />
                <div className="text-xs">
                  <span className="font-bold text-slate-900 block">
                    Allow AI coaching agent and aggregate metrics analysis
                  </span>
                  <p className="mt-1 text-slate-500 leading-relaxed">
                    When enabled, Shohoj Upay sends anonymized monthly aggregates to generate insights.
                    No names, phone numbers, or merchant free-text are ever transmitted. Disabling
                    this immediately revokes AI coaching while keeping deterministic features active.
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Section 2: Data Export */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2.5">
              <div className="rounded-xl bg-blue-50 p-2 text-blue-600">
                <Download className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">Data Portability</h2>
                <p className="text-xs text-slate-500">
                  Export your full financial ledger, goal records, and calculated features
                </p>
              </div>
            </div>

            <p className="mt-4 text-xs text-slate-600 leading-relaxed">
              In accordance with Bangladesh data protection principles and Sohoj&apos;s privacy charter,
              you may download your complete personal records at any time as an encrypted JSON export.
            </p>

            <div className="mt-4">
              <button
                onClick={handleExportData}
                disabled={isExporting}
                className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50 transition"
              >
                <Download className="h-4 w-4" />
                {isExporting ? "Generating Export..." : "Download Personal Archive (JSON)"}
              </button>
            </div>
          </div>

          {/* Section 3: Data Deletion & Erasure */}
          <div className="rounded-2xl border border-rose-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2.5">
              <div className="rounded-xl bg-rose-50 p-2 text-rose-600">
                <Trash2 className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-rose-900">
                  Account Erasure & Right to be Forgotten
                </h2>
                <p className="text-xs text-rose-600">
                  Permanently delete account, transactions, and purging traces
                </p>
              </div>
            </div>

            <p className="mt-4 text-xs text-slate-600 leading-relaxed">
              Triggering account erasure permanently deletes your profile and initiates an
              automated cascade that removes all transaction records, goals, and chat messages
              within 30 days.
            </p>

            <div className="mt-4">
              <button
                onClick={() => setIsDeleteDialogOpen(true)}
                className="inline-flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-50 px-4 py-2 text-xs font-bold text-rose-700 hover:bg-rose-100 transition"
              >
                <Trash2 className="h-4 w-4" />
                Request Permanent Deletion
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Delete Confirmation Modal */}
      {isDeleteDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100">
            <div className="flex items-center gap-2 text-rose-600 pb-3 border-b border-slate-100">
              <AlertTriangle className="h-5 w-5" />
              <h3 className="text-base font-bold text-slate-900">Confirm Account Deletion</h3>
            </div>

            <p className="mt-3 text-xs text-slate-600 leading-relaxed">
              This action is permanent and cannot be undone. All your MFS transaction records,
              saved goals, and conversation histories will be irrevocably purged.
            </p>

            <div className="mt-4">
              <label
                htmlFor="del-confirm"
                className="block text-xs font-bold text-slate-700 mb-1"
              >
                Type <strong className="text-rose-600">DELETE</strong> to confirm:
              </label>
              <input
                id="del-confirm"
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="DELETE"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-xs text-slate-900 font-mono"
              />
            </div>

            <div className="mt-5 flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setIsDeleteDialogOpen(false);
                  setDeleteConfirmText("");
                }}
                className="flex-1 rounded-xl border border-slate-300 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleteConfirmText !== "DELETE" || isDeleting}
                onClick={handleDeleteAccount}
                className="flex-1 rounded-xl bg-rose-600 py-2 text-xs font-bold text-white hover:bg-rose-500 disabled:opacity-40"
              >
                {isDeleting ? "Deleting..." : "Permanently Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      <AppBottomNav />
    </div>
  );
}
