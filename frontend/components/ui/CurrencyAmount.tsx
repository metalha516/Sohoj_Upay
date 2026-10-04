import React from "react";

interface CurrencyAmountProps {
  amount: number;
  size?: "sm" | "md" | "lg" | "hero";
  sign?: "+" | "-" | null;
  className?: string;
  showDecimals?: boolean;
}

export function CurrencyAmount({
  amount,
  size = "md",
  sign,
  className = "",
  showDecimals = false,
}: CurrencyAmountProps) {
  const absAmount = Math.abs(amount);
  
  const sizeClasses = {
    sm: "text-sm",
    md: "text-base font-bold",
    lg: "text-2xl font-extrabold",
    hero: "text-3xl sm:text-4xl lg:text-5xl font-black",
  };

  const formattedParts = new Intl.NumberFormat("en-BD", {
    minimumFractionDigits: showDecimals ? 2 : 0,
    maximumFractionDigits: showDecimals ? 2 : 0,
  }).formatToParts(absAmount);

  const integerPart = formattedParts
    .filter((p) => p.type !== "decimal" && p.type !== "fraction")
    .map((p) => p.value)
    .join("");

  const fractionPart = formattedParts.find((p) => p.type === "fraction")?.value;

  return (
    <span
      className={`inline-flex items-baseline font-mono tabular-nums select-none ${sizeClasses[size]} ${className}`}
    >
      {sign && <span className="mr-0.5 text-slate-400 font-semibold">{sign}</span>}
      {/* Symbol: Rendered with humanistic Sans for balanced Bengali typography */}
      <span className="font-sans text-[0.78em] font-extrabold text-upay-400 mr-1 self-center tracking-normal">
        ৳
      </span>
      {/* Integer value: High-impact bold tabular display */}
      <span className="tracking-tight">{integerPart}</span>
      {/* Fractional value: Optical de-emphasis */}
      {showDecimals && fractionPart && (
        <span className="text-[0.68em] font-medium text-slate-400 ml-0.5 opacity-80">
          .{fractionPart}
        </span>
      )}
    </span>
  );
}
