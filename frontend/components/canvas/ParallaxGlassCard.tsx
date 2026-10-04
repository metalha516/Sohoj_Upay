"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { Wifi } from "lucide-react";

interface ParallaxGlassCardProps {
  cardHolder?: string;
  maskedPan?: string;
  expiry?: string;
  balanceTaka?: string;
  tier?: string;
}

export function ParallaxGlassCard({
  cardHolder = "SUMAIYA AKTER",
  maskedPan = "•••• •••• •••• 8421",
  expiry = "09/29",
  balanceTaka = "৳ 42,500.00",
  tier = "UPAY PLATINUM",
}: ParallaxGlassCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [rotate, setRotate] = useState({ x: 0, y: 0 });
  const [glare, setGlare] = useState({ x: 50, y: 50, opacity: 0 });

  // 1. Mouse/Pointer Parallax
  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotX = -((y - centerY) / centerY) * 14;
    const rotY = ((x - centerX) / centerX) * 14;

    setRotate({ x: rotX, y: rotY });
    setGlare({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
      opacity: 0.65,
    });
  }, []);

  const handlePointerLeave = useCallback(() => {
    setRotate({ x: 0, y: 0 });
    setGlare((prev) => ({ ...prev, opacity: 0 }));
  }, []);

  // 2. Mobile Gyroscope Parallax
  useEffect(() => {
    const handleOrientation = (e: DeviceOrientationEvent) => {
      if (e.gamma === null || e.beta === null) return;
      const clampedGamma = Math.min(Math.max(e.gamma, -30), 30);
      const clampedBeta = Math.min(Math.max(e.beta - 45, -30), 30);

      setRotate({
        x: -clampedBeta * 0.45,
        y: clampedGamma * 0.45,
      });
      setGlare({
        x: 50 + (clampedGamma / 30) * 40,
        y: 50 + (clampedBeta / 30) * 40,
        opacity: 0.5,
      });
    };

    if (typeof window !== "undefined" && "DeviceOrientationEvent" in window) {
      window.addEventListener("deviceorientation", handleOrientation);
    }

    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("deviceorientation", handleOrientation);
      }
    };
  }, []);

  return (
    <div className="perspective-1000 py-4 flex justify-center items-center">
      <div
        ref={cardRef}
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
        style={{
          transform: `rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`,
          transition: glare.opacity === 0 ? "transform 0.5s ease-out" : "none",
        }}
        className="relative w-[320px] sm:w-[380px] h-[208px] sm:h-[230px] rounded-3xl p-6 sm:p-7 
                   bg-gradient-to-br from-[#0d234c]/90 via-[#0a1c3c]/95 to-[#061325]/95
                   border border-upay-500/35 shadow-2xl shadow-navy-950/90
                   backdrop-blur-2xl select-none cursor-pointer overflow-hidden transform-gpu"
      >
        {/* Holographic Specular Glare Layer */}
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-300"
          style={{
            opacity: glare.opacity,
            background: `radial-gradient(circle at ${glare.x}% ${glare.y}%, rgba(255, 199, 9, 0.42) 0%, rgba(0, 210, 255, 0.18) 30%, transparent 65%)`,
          }}
        />

        {/* Card Header: Upay Logo & Contactless */}
        <div className="flex justify-between items-start relative z-10">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-upay-500 flex items-center justify-center font-black text-navy-950 text-sm shadow-md upay-glow">
              S
            </div>
            <div>
              <span className="font-black text-white tracking-wide text-sm">SOHOJ</span>
              <span className="ml-1.5 text-[9px] font-bold px-1.5 py-0.5 rounded bg-upay-500/20 text-upay-400 border border-upay-500/30">
                {tier}
              </span>
            </div>
          </div>
          <Wifi className="h-5 w-5 text-slate-400 rotate-90" />
        </div>

        {/* EMV Gold Chip & Balance */}
        <div className="mt-4 flex items-center justify-between relative z-10">
          {/* Metallic Gold EMV Chip */}
          <div className="w-10 h-7 rounded-md bg-gradient-to-tr from-amber-400 via-yellow-200 to-amber-500 border border-yellow-600/60 shadow-inner flex flex-col justify-around p-1">
            <div className="w-full h-px bg-yellow-700/50" />
            <div className="w-full h-px bg-yellow-700/50" />
          </div>

          <div className="text-right">
            <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">
              Available MFS Liquidity
            </div>
            <div className="text-lg font-black text-upay-400 drop-shadow">
              {balanceTaka}
            </div>
          </div>
        </div>

        {/* Masked Card Number */}
        <div className="mt-4 font-mono text-base sm:text-lg tracking-widest text-slate-200 font-bold relative z-10 drop-shadow">
          {maskedPan}
        </div>

        {/* Card Footer */}
        <div className="mt-3 flex justify-between items-end relative z-10 text-[10px] font-bold text-slate-400">
          <div>
            <div className="text-[8px] uppercase tracking-wider text-slate-500">MFS SUBSCRIBER</div>
            <div className="text-slate-200 font-semibold uppercase tracking-wider">{cardHolder}</div>
          </div>
          <div className="text-right">
            <div className="text-[8px] uppercase tracking-wider text-slate-500">NETWORK</div>
            <div className="text-upay-400 font-bold">UPAY • UCB</div>
          </div>
        </div>
      </div>
    </div>
  );
}
