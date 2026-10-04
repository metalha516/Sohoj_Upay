/**
 * Formatting utilities for Sohoj financial figures, percentages, and timestamps.
 */

export function formatBDT(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "৳ 0";
  }
  const formatted = new Intl.NumberFormat("en-BD", {
    maximumFractionDigits: 2,
  }).format(val);
  return `৳ ${formatted}`;
}

export function formatPercent(val: number | null | undefined, digits: number = 1): string {
  if (val === null || val === undefined || isNaN(val)) {
    return digits === 0 ? "0%" : "0.0%";
  }
  return `${(val * 100).toFixed(digits)}%`;
}

export function formatDate(val: string | Date | null | undefined): string {
  if (!val) return "—";
  try {
    const d = typeof val === "string" ? new Date(val) : val;
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

export function formatDateTime(val: string | Date | null | undefined): string {
  if (!val) return "—";
  try {
    const d = typeof val === "string" ? new Date(val) : val;
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}
