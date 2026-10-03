import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SafeMarkdown } from "../components/coach/SafeMarkdown";
import { ToolStatusChip } from "../components/coach/ToolStatusChip";
import { UiActionButton } from "../components/coach/UiActionButton";
import { BehaviorProfileCard } from "../components/behavior/BehaviorProfileCard";
import { FactorBarsCard } from "../components/behavior/FactorBarsCard";
import { AnomalyListTable } from "../components/behavior/AnomalyListTable";

describe("SafeMarkdown Component", () => {
  it("renders headers, lists, code, and bold without dangerouslySetInnerHTML", () => {
    const markdown = `# Title 1
## Title 2
### Title 3

Here is **bold text** and \`inline code\`.

- First item
- Second item

> Grounded guidance blockquote
`;
    render(<SafeMarkdown content={markdown} />);

    expect(screen.getByText("Title 1")).toBeInTheDocument();
    expect(screen.getByText("Title 2")).toBeInTheDocument();
    expect(screen.getByText("Title 3")).toBeInTheDocument();
    expect(screen.getByText("bold text")).toBeInTheDocument();
    expect(screen.getByText("inline code")).toBeInTheDocument();
    expect(screen.getByText("First item")).toBeInTheDocument();
    expect(screen.getByText("Second item")).toBeInTheDocument();
    expect(screen.getByText("Grounded guidance blockquote")).toBeInTheDocument();
  });

  it("neutralizes javascript: links and renders plain label", () => {
    const malicious = `[Malicious Link](javascript:alert('pwned'))`;
    render(<SafeMarkdown content={malicious} />);

    // Link tag should not have href="javascript:..."
    const link = screen.queryByRole("link");
    expect(link).toBeNull();
    expect(screen.getByText("Malicious Link")).toBeInTheDocument();
  });

  it("allows safe https links", () => {
    const safe = `[Safe Link](https://example.com/docs)`;
    render(<SafeMarkdown content={safe} />);

    const link = screen.getByRole("link", { name: "Safe Link" });
    expect(link).toHaveAttribute("href", "https://example.com/docs");
  });
});

describe("ToolStatusChip Component", () => {
  it("renders friendly tool labels and completed checkmarks", () => {
    render(<ToolStatusChip tool="check_affordability" status="completed" />);
    expect(screen.getByText("Verifying affordability impact")).toBeInTheDocument();
  });

  it("renders running tool with spinner indicator", () => {
    render(<ToolStatusChip tool="get_current_balance" status="running" />);
    expect(screen.getByText("Checking current balance")).toBeInTheDocument();
  });
});

describe("UiActionButton Component", () => {
  it("renders deep links for allowed actions", () => {
    render(<UiActionButton action="open_simulator" />);
    const link = screen.getByRole("link", { name: /Open Wealth Simulator/i });
    expect(link).toHaveAttribute("href", "/simulator");
  });

  it("renders goals deep link", () => {
    render(<UiActionButton action="navigate_to_goals" />);
    const link = screen.getByRole("link", { name: /View Financial Goals/i });
    expect(link).toHaveAttribute("href", "/goals");
  });
});

describe("BehaviorProfileCard Component", () => {
  it("renders archetype, confidence score, and model version", () => {
    render(
      <BehaviorProfileCard
        profile={{
          profile: "disciplined_saver",
          confidence: 0.92,
          top_factors: [],
          model_version: "xgb-v1.0.0",
          as_of_month: "2026-10",
          is_cold_start: false,
        }}
      />
    );

    expect(screen.getByText("Disciplined Saver")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
    expect(screen.getByText("xgb-v1.0.0")).toBeInTheDocument();
  });

  it("shows cold-start banner when is_cold_start is true", () => {
    render(
      <BehaviorProfileCard
        profile={{
          profile: "balanced_optimizer",
          confidence: 0.7,
          top_factors: [],
          model_version: "rule-v1",
          as_of_month: "2026-10",
          is_cold_start: true,
        }}
      />
    );

    expect(screen.getByText(/Cold-Start Persona/i)).toBeInTheDocument();
  });
});

describe("FactorBarsCard Component", () => {
  it("renders explainability factor bars and benchmarks", () => {
    render(
      <FactorBarsCard
        profile={{
          profile: "disciplined_saver",
          confidence: 0.9,
          top_factors: [],
          savings_rate: 0.25,
          necessity_rate: 0.52,
          discretionary_rate: 0.23,
          cashout_frequency: 3,
          spending_variance: 0.15,
        }}
      />
    );

    expect(screen.getByText("Explainability Factors")).toBeInTheDocument();
    expect(screen.getByText("Savings Rate")).toBeInTheDocument();
    expect(screen.getByText("Necessity Expense Ratio")).toBeInTheDocument();
    expect(screen.getByText("Discretionary Ratio")).toBeInTheDocument();
  });
});

describe("AnomalyListTable Component", () => {
  it("renders anomalies and supports filter pills", () => {
    const mockAnomalies = [
      {
        id: "a-1",
        scope: "dining",
        category: "dining",
        anomaly_score: 0.9,
        confidence: 0.95,
        observed_value: 8500,
        baseline_value: 2000,
        deviation_pct: 325,
        explanation: "Unusual weekend dining spike",
        status: "open" as const,
        created_at: "2026-10-01T10:00:00Z",
      },
      {
        id: "a-2",
        scope: "electronics",
        category: "electronics",
        anomaly_score: 0.85,
        confidence: 0.9,
        observed_value: 15000,
        baseline_value: 3000,
        deviation_pct: 400,
        explanation: "Large gadget purchase",
        status: "confirmed" as const,
        created_at: "2026-10-01T11:00:00Z",
      },
    ];

    render(<AnomalyListTable initialAnomalies={mockAnomalies} />);

    expect(screen.getByText("Dining Outlier")).toBeInTheDocument();
    expect(screen.getByText("Electronics Outlier")).toBeInTheDocument();

    // Click "open" filter
    fireEvent.click(screen.getByRole("button", { name: "open" }));
    expect(screen.getByText("Dining Outlier")).toBeInTheDocument();
    expect(screen.queryByText("Electronics Outlier")).toBeNull();
  });
});
