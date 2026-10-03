"use client";

import React from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import { SimulatorView } from "@/components/simulator/SimulatorView";

export default function SimulatorPage() {
  return (
    <div className="min-h-screen bg-slate-50 pb-20 md:pb-12">
      <AppHeader />
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-6">
        <SimulatorView />
      </main>
      <AppBottomNav />
    </div>
  );
}
