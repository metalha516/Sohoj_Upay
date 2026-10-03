/**
 * Formatting utilities for Sohoj financial figures and dates.
 * Enforces Intl.NumberFormat('en-BD') with BDT / ৳ symbol.
 */

const bdtCurrencyFormatter = new Intl.NumberFormat("en-BD", {
  style: "currency",
  currency: "BDT",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const bdtDecimalFormatter = new Intl.NumberFormat("en-BD", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

/**
 * Format an amount into Bangladeshi Taka (৳).
 * e.g., 25000 -> "৳ 25,000" or "BDT 25,000"
 */
export function formatBDT(amount: number | string | null | undefined, showSymbol: boolean = true): string {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return showSymbol ? "৳ 0" : "0";
  }
  const numeric = typeof amount === "string" ? parseFloat(amount) : amount;
  
  if (showSymbol) {
    // Format with explicit ৳ symbol using Bengali / en-BD grouping
    return `৳ ${bdtDecimalFormatter.format(numeric)}`;
  }
  return bdtDecimalFormatter.format(numeric);
}

/**
 * Format a decimal fraction or percentage into a display string.
 * e.g. 0.234 -> "23.4%"
 */
export function formatPercent(value: number | null | undefined, decimals: number = 1): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "0.0%";
  }
  // If value is between 0 and 1, multiply by 100
  const pct = Math.abs(value) <= 1 ? value * 100 : value;
  return `${pct.toFixed(decimals)}%`;
}

/**
 * Format ISO date string into readable Dhaka local format (e.g., "15 Oct 2026").
 */
export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      timeZone: "Asia/Dhaka",
    }).format(d);
  } catch {
    return isoString;
  }
}

/**
 * Format ISO datetime string with time in Dhaka local time.
 */
export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Dhaka",
    }).format(d);
  } catch {
    return isoString;
  }
}
