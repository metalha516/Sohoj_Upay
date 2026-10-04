"use client";

import React, { useEffect } from "react";
import { motion, useSpring, useTransform } from "framer-motion";

function DigitColumn({ digit }: { digit: string }) {
  const isNumber = !isNaN(parseInt(digit));
  const num = isNumber ? parseInt(digit) : 0;

  const spring = useSpring(num, {
    stiffness: 100,
    damping: 18,
    mass: 0.8,
  });

  useEffect(() => {
    if (isNumber) spring.set(num);
  }, [num, spring, isNumber]);

  const y = useTransform(spring, (current) => `${-current * 10}%`);

  if (!isNumber) {
    return <span className="inline-block font-sans px-0 text-slate-400 select-none">{digit}</span>;
  }

  return (
    <span className="relative inline-block h-[1.18em] w-[0.6em] overflow-hidden align-baseline">
      <motion.span
        style={{ y }}
        className="absolute left-0 top-0 flex flex-col font-mono tabular-nums leading-[1.18em]"
      >
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
          <span key={n} className="flex h-[1.18em] items-center justify-center">
            {n}
          </span>
        ))}
      </motion.span>
    </span>
  );
}

interface RollingOdometerProps {
  value: number;
  prefix?: string;
  className?: string;
  showDecimals?: boolean;
}

export function RollingOdometer({
  value,
  prefix = "৳",
  className = "text-3xl sm:text-4xl font-black text-white",
  showDecimals = false,
}: RollingOdometerProps) {
  const formatted = showDecimals
    ? value.toLocaleString("en-BD", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : Math.round(value).toLocaleString("en-BD");

  return (
    <div className={`inline-flex items-baseline font-mono select-none ${className}`}>
      {prefix && (
        <span className="font-sans text-[0.78em] font-extrabold text-upay-400 mr-1.5 self-center">
          {prefix}
        </span>
      )}
      {formatted.split("").map((char, index) => (
        <DigitColumn key={`${index}-${char}`} digit={char} />
      ))}
    </div>
  );
}
