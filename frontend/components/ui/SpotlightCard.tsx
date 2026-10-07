"use client";

import React, { useRef, useState } from "react";

interface SpotlightCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  spotlightColor?: string;
  className?: string;
  innerClassName?: string;
  withDoubleBezel?: boolean;
  variant?: "light" | "dark";
}

export function SpotlightCard({
  children,
  spotlightColor = "rgba(255, 199, 9, 0.16)", // Luminous Upay Gold
  className = "",
  innerClassName = "",
  withDoubleBezel = true,
  variant = "light",
  ...props
}: SpotlightCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const isLight = variant === "light";

  if (!withDoubleBezel) {
    return (
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setOpacity(1)}
        onMouseLeave={() => setOpacity(0)}
        className={`relative overflow-hidden rounded-3xl transition-all duration-300 ${
          isLight
            ? "border border-slate-200/90 bg-white shadow-sm hover:border-upay-500/50 hover:shadow-xl"
            : "border border-navy-700/60 bg-navy-900/80 hover:border-upay-500/40 hover:shadow-2xl"
        } p-6 backdrop-blur-xl ${className}`}
        {...props}
      >
        <div
          className="pointer-events-none absolute -inset-px transition-opacity duration-300"
          style={{
            opacity,
            background: `radial-gradient(550px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 75%)`,
          }}
        />
        <div className="relative z-10">{children}</div>
      </div>
    );
  }

  // High-End Doppelrand (Double-Bezel) Architecture
  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setOpacity(1)}
      onMouseLeave={() => setOpacity(0)}
      className={`group relative rounded-[2rem] p-1.5 transition-all duration-300 ${
        isLight
          ? "bg-gradient-to-b from-slate-200/80 via-slate-100/60 to-transparent ring-1 ring-slate-200 shadow-xl hover:ring-upay-500/50"
          : "bg-gradient-to-b from-white/[0.08] to-transparent ring-1 ring-white/[0.08] shadow-2xl hover:ring-upay-500/40"
      } backdrop-blur-xl ${className}`}
      {...props}
    >
      {/* Radial Spotlight Overlay */}
      <div
        className="pointer-events-none absolute inset-0 rounded-[2rem] transition-opacity duration-300 overflow-hidden"
        style={{
          opacity,
          background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 70%)`,
        }}
      />

      {/* Inner Core Glass Container */}
      <div
        className={`relative rounded-[calc(2rem-6px)] p-6 transition-colors duration-300 ${
          isLight
            ? "bg-white shadow-sm border border-slate-200/70 group-hover:border-slate-300"
            : "bg-navy-900/90 shadow-[inset_0_1px_1px_rgba(255,255,255,0.12)] border border-navy-800/80 group-hover:border-navy-700"
        } ${innerClassName}`}
      >
        {children}
      </div>
    </div>
  );
}
