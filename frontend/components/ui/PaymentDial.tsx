"use client";

import React, { useState, useRef, useCallback } from "react";

interface PaymentDialProps {
  totalDue?: number;
  minDue?: number;
  initialValue?: number;
  onAmountChange?: (amount: number) => void;
  label?: string;
  unitLabel?: string;
}

export function PaymentDial({
  totalDue = 25000,
  minDue = 1000,
  initialValue = 5000,
  onAmountChange,
  label = "Monthly Savings Goal",
  unitLabel = "Rule of 72 Compounding",
}: PaymentDialProps) {
  const [amount, setAmount] = useState(initialValue);
  const svgRef = useRef<SVGSVGElement>(null);

  const radius = 96;
  const stroke = 16;
  const center = 130;
  const circumference = 2 * Math.PI * radius;

  // Percentage between minDue and totalDue
  const percentage = Math.max(0, Math.min(1, (amount - minDue) / (totalDue - minDue)));
  const strokeDashoffset = circumference - percentage * circumference;

  const handlePointer = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!svgRef.current) return;
      const rect = svgRef.current.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;

      let angle = Math.atan2(e.clientY - cy, e.clientX - cx) * (180 / Math.PI) + 90;
      if (angle < 0) angle += 360;

      const progress = Math.min(1, Math.max(0, angle / 360));
      const calculated = Math.round((minDue + progress * (totalDue - minDue)) / 500) * 500;
      setAmount(calculated);
      onAmountChange?.(calculated);
    },
    [minDue, totalDue, onAmountChange]
  );

  const getDialColor = () => {
    if (percentage > 0.6) return "#FFC709"; // Upay Gold
    if (percentage > 0.25) return "#38BDF8"; // Sky Cyan
    return "#F59E0B"; // Amber
  };

  return (
    <div className="flex flex-col items-center select-none">
      <div className="relative h-[260px] w-[260px]">
        <svg
          ref={svgRef}
          onPointerDown={handlePointer}
          onPointerMove={(e) => e.buttons === 1 && handlePointer(e)}
          className="h-full w-full cursor-grab active:cursor-grabbing"
          viewBox="0 0 260 260"
        >
          {/* Background Track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="transparent"
            stroke="#0F2B5C"
            strokeWidth={stroke}
          />
          {/* Active Arc */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="transparent"
            stroke={getDialColor()}
            strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-colors duration-200"
            transform={`rotate(-90 ${center} ${center})`}
          />
        </svg>

        {/* Center Hub */}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            {label}
          </span>
          <span className="font-mono text-3xl font-black text-white mt-1">
            ৳ {amount.toLocaleString("en-BD")}
          </span>
          <span
            className="mt-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider"
            style={{
              backgroundColor: `${getDialColor()}20`,
              color: getDialColor(),
              border: `1px solid ${getDialColor()}40`,
            }}
          >
            {unitLabel}
          </span>
        </div>
      </div>
      <p className="mt-2 text-xs text-slate-400">
        Drag around the dial to calibrate wealth velocity
      </p>
    </div>
  );
}
