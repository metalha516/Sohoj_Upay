"use client";

import dynamic from "next/dynamic";
import React from "react";

// Client-only dynamic imports with lightweight skeletons
export const DynamicGoldTakaCoin = dynamic(
  () => import("./GoldTakaCoinCanvas"),
  {
    ssr: false,
    loading: () => (
      <div className="w-72 h-72 sm:w-88 sm:h-88 lg:w-96 lg:h-96 mx-auto rounded-full bg-navy-900/30 border border-navy-800 animate-pulse flex items-center justify-center">
        <div className="w-24 h-24 rounded-full border-2 border-upay-500/20 border-t-upay-500 animate-spin" />
      </div>
    ),
  }
);

export const DynamicParticleWave = dynamic(
  () => import("./ParticleWaveCanvas"),
  {
    ssr: false,
    loading: () => null,
  }
);
