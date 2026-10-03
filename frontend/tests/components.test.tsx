import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { formatBDT, formatPercent, formatDate } from "@/lib/formatters";
import { BalanceCard } from "@/components/dashboard/BalanceCard";
import { IncomeCard } from "@/components/dashboard/IncomeCard";
import { ExpenseCard } from "@/components/dashboard/ExpenseCard";
import { SavingsCard } from "@/components/dashboard/SavingsCard";
import { ForecastCard } from "@/components/dashboard/ForecastCard";
import { AnomalyCard } from "@/components/dashboard/AnomalyCard";
import { CashOutPurposeModal } from "@/components/transactions/CashOutPurposeModal";
import { SimulatorView } from "@/components/simulator/SimulatorView";

describe("Formatting Utilities", () => {
  it("formats BDT figures using Intl en-BD grouping and ৳ symbol", () => {
    expect(formatBDT(25000)).toContain("25,000");
    expect(formatBDT(25000)).toContain("৳");
    expect(formatBDT(100000)).toContain("100,000");
    expect(formatBDT(0)).toBe("৳ 0");
    expect(formatBDT(null)).toBe("৳ 0");
  });

  it("formats percentages correctly", () => {
    expect(formatPercent(0.235)).toBe("23.5%");
    expect(formatPercent(0.05)).toBe("5.0%");
    expect(formatPercent(1.0)).toBe("100.0%");
  });

  it("formats dates gracefully", () => {
    expect(formatDate("2026-10-15T09:00:00Z")).toContain("Oct");
    expect(formatDate(null)).toBe("—");
  });
});

describe("Dashboard Key Components", () => {
  it("renders BalanceCard and triggers action callbacks", () => {
    const handleCashOut = vi.fn();
    const handleAddTxn = vi.fn();

    render(
      <BalanceCard
        balance={45200}
        onRecordCashOut={handleCashOut}
        onAddTransaction={handleAddTxn}
      />
    );

    expect(screen.getByText("৳ 45,200")).toBeInTheDocument();
    expect(screen.getByText("Current Net Balance")).toBeInTheDocument();

    const cashOutBtn = screen.getByRole("button", { name: /Record Cash-Out/i });
    fireEvent.click(cashOutBtn);
    expect(handleCashOut).toHaveBeenCalledTimes(1);

    const addBtn = screen.getByRole("button", { name: /Add Transaction/i });
    fireEvent.click(addBtn);
    expect(handleAddTxn).toHaveBeenCalledTimes(1);
  });

  it("renders IncomeCard with monthly inflow amount", () => {
    render(<IncomeCard amount={65000} transactionCount={3} />);
    expect(screen.getByText("৳ 65,000")).toBeInTheDocument();
    expect(screen.getByText(/3 salary\/cash-in deposits/i)).toBeInTheDocument();
  });

  it("renders ExpenseCard with necessity ratio split", () => {
    render(<ExpenseCard amount={38000} necessityRatio={0.72} />);
    expect(screen.getByText("৳ 38,000")).toBeInTheDocument();
    expect(screen.getByText(/Necessity: 72%/i)).toBeInTheDocument();
    expect(screen.getByText(/Discretionary: 28%/i)).toBeInTheDocument();
  });

  it("renders SavingsCard with emergency runway and healthy rate badge", () => {
    render(
      <SavingsCard
        savingsAmount={27000}
        savingsRate={0.415}
        emergencyFundMonths={4.2}
      />
    );
    expect(screen.getByText("৳ 27,000")).toBeInTheDocument();
    expect(screen.getByText(/41.5% rate/i)).toBeInTheDocument();
    expect(screen.getByText(/4.2 mo/i)).toBeInTheDocument();
  });

  it("renders ForecastCard with confidence interval and model version", () => {
    render(
      <ForecastCard
        forecast={{
          predicted_expense: 35000,
          interval_p10: 29000,
          interval_p90: 41000,
          confidence: 0.88,
          model_version: "expense-forecaster-v2.1",
          disclaimer: "Projection based on machine learning estimate; not guaranteed.",
        }}
      />
    );

    expect(screen.getByText("৳ 35,000")).toBeInTheDocument();
    expect(screen.getByText("expense-forecaster-v2.1")).toBeInTheDocument();
    expect(screen.getByText(/৳ 29,000 – ৳ 41,000/i)).toBeInTheDocument();
    expect(screen.getByText(/88.0%/i)).toBeInTheDocument();
  });

  it("renders AnomalyCard with observed vs baseline and handles feedback", async () => {
    const handleFeedback = vi.fn().mockResolvedValue(undefined);

    render(
      <AnomalyCard
        anomalies={[
          {
            id: "anom-1",
            anomaly_score: 0.85,
            confidence: 0.9,
            observed: 12500,
            baseline: 3200,
            deviation_pct: 2.9,
            scope: "category_month",
            explanation: "Unusual surge in electronics expenditure",
            status: "pending",
            created_at: "2026-10-01T12:00:00Z",
          },
        ]}
        onFeedback={handleFeedback}
      />
    );

    expect(screen.getByText(/Unusual Activity Detected/i)).toBeInTheDocument();
    expect(screen.getByText(/Unusual surge in electronics expenditure/i)).toBeInTheDocument();
    expect(screen.getByText("Observed: ৳ 12,500")).toBeInTheDocument();

    const legitBtn = screen.getByRole("button", { name: /Legitimate Expense/i });
    fireEvent.click(legitBtn);
    await waitFor(() => {
      expect(handleFeedback).toHaveBeenCalledWith("anom-1", "confirmed");
    });
  });
});

describe("CashOutPurposeModal Mandatory Flow", () => {
  it("enforces mandatory purpose and validates amount", async () => {
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    const handleClose = vi.fn();

    const { rerender } = render(
      <CashOutPurposeModal
        isOpen={false}
        onClose={handleClose}
        onSubmit={handleSubmit}
      />
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    rerender(
      <CashOutPurposeModal
        isOpen={true}
        onClose={handleClose}
        onSubmit={handleSubmit}
      />
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/Record MFS Cash-Out/i)).toBeInTheDocument();

    // Select purpose "Necessity"
    const necessityBtn = screen.getByRole("button", { name: /Necessity/i });
    fireEvent.click(necessityBtn);

    // Enter amount
    const amountInput = screen.getByLabelText(/Cash-Out Amount/i);
    fireEvent.change(amountInput, { target: { value: "3200" } });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: /Record Cash-Out/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledTimes(1);
      const callArg = handleSubmit.mock.calls[0][0];
      expect(callArg.amount).toBe(3200);
      expect(callArg.purpose).toBe("necessity");
      expect(callArg.mfs_provider).toBe("bkash");
    });
  });
});

describe("Simulator Component", () => {
  it("renders with assumed-rate badge and slider controls", async () => {
    render(<SimulatorView />);

    expect(screen.getByText(/Deterministic Wealth Simulator/i)).toBeInTheDocument();
    expect(screen.getByText(/Assumed-Rate Badge/i)).toBeInTheDocument();
    expect(screen.getByText(/Projections not guaranteed/i)).toBeInTheDocument();

    // Sliders exist
    expect(screen.getByLabelText(/Initial Deposit/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Monthly Saving/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Assumed Annual Rate/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Horizon/i)).toBeInTheDocument();
  });
});
