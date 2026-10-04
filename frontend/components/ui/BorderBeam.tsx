"use client";

import React from "react";

interface BorderBeamProps {
  className?: string;
  size?: number;
  duration?: number;
  delay?: number;
  colorFrom?: string;
  colorTo?: string;
  borderWidth?: number;
}

export function BorderBeam({
  className = "",
  size = 140,
  duration = 8,
  delay = 0,
  colorFrom = "#FFC709", // Upay Gold
  colorTo = "#1E4D9F",   // Upay Navy Accent
  borderWidth = 1.5,
}: BorderBeamProps) {
  return (
    <div
      style={
        {
          "--size": `${size}px`,
          "--duration": `${duration}s`,
          "--delay": `-${delay}s`,
          "--color-from": colorFrom,
          "--color-to": colorTo,
          "--border-width": `${borderWidth}px`,
        } as React.CSSProperties
      }
      className={`pointer-events-none absolute inset-0 rounded-[inherit] border border-transparent [mask-clip:padding-box,border-box] [mask-composite:intersect] [mask-image:linear-gradient(transparent,transparent),linear-gradient(#000,#000)] ${className}`}
    >
      <div className="absolute aspect-square w-[var(--size)] [animation:border-beam_var(--duration)_infinite_linear] [animation-delay:var(--delay)] [background:radial-gradient(circle_at_center,var(--color-from)_0%,var(--color-to)_60%,transparent_100%)] [offset-anchor:calc(var(--size)/2)_calc(var(--size)/2)] [offset-path:rect(0_auto_auto_0_round_inherit)]" />
    </div>
  );
}
