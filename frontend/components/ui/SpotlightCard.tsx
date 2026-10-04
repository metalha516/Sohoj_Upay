"use client";

import React, { useRef, useState } from "react";

interface SpotlightCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  spotlightColor?: string;
  className?: string;
  innerClassName?: string;
  withDoubleBezel?: boolean;
}

export function SpotlightCard({
  children,
  spotlightColor = "rgba(255, 199, 9, 0.16)", // Luminous Upay Gold
  className = "",
  innerClassName = "",
  withDoubleBezel = true,
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

  if (!withDoubleBezel) {
    return (
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setOpacity(1)}
        onMouseLeave={() => setOpacity(0)}
        className={`relative overflow-hidden rounded-3xl border border-navy-700/60 bg-navy-900/80 p-6 backdrop-blur-xl transition-all duration-300 hover:border-upay-500/40 hover:shadow-2xl ${className}`}
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
      className={`group relative rounded-[2rem] p-1.5 bg-gradient-to-b from-white/[0.08] to-transparent ring-1 ring-white/[0.08] shadow-2xl backdrop-blur-xl transition-all duration-300 hover:ring-upay-500/40 ${className}`}
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
        className={`relative rounded-[calc(2rem-6px)] bg-navy-900/90 p-6 shadow-[inset_0_1px_1px_rgba(255,255,255,0.12)] border border-navy-800/80 transition-colors duration-300 group-hover:border-navy-700 ${innerClassName}`}
      >
        {children}
      </div>
    </div>
  );
}
