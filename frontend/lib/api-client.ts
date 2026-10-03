/**
 * Typed API Client for Sohoj Backend.
 * Features:
 * - In-memory access token storage (Security Principle: no tokens in localStorage)
 * - Automatic token refresh via HttpOnly cookie on 401
 * - Strict RFC 7807 problem+json error formatting
 * - Cache-Control: no-store for authenticated data
 */

import {
  Anomaly,
  AnomalyFeedbackRequest,
  BehaviorInsights,
  BehaviorProfile,
  CashOutCreateRequest,
  CategoryBreakdown,
  DashboardOverview,
  DoublingSimulationRequest,
  DoublingSimulationResponse,
  Goal,
  GoalContributionRequest,
  GoalContributionResponse,
  GoalCreateRequest,
  GoalUpdateRequest,
  GrowthSimulationRequest,
  GrowthSimulationResponse,
  LoginRequest,
  MonthlySummary,
  ProblemDetails,
  RegisterRequest,
  SavingsForecast,
  ScenarioSimulationRequest,
  ScenarioSimulationResponse,
  SpendingForecast,
  TokenResponse,
  Transaction,
  TransactionCreateRequest,
  TransactionListResponse,
  User,
  UserUpdateRequest,
  ChatFeedbackRequest,
  ChatFeedbackResponse,
  ChatRequest,
  ChatResponse,
  ConversationHistoryResponse,
  StreamDoneEvent,
  StreamTokenEvent,
  StreamToolStatusEvent,
  StreamUiActionEvent,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export class ApiError extends Error {
  public problem: ProblemDetails;
  public status: number;

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title || "API Error");
    this.name = "ApiError";
    this.problem = problem;
    this.status = problem.status;
  }
}

class ApiClient {
  private inMemoryAccessToken: string | null = null;
  private isRefreshing: boolean = false;
  private refreshPromise: Promise<string | null> | null = null;

  public setAccessToken(token: string | null) {
    this.inMemoryAccessToken = token;
  }

  public getAccessToken(): string | null {
    return this.inMemoryAccessToken;
  }

  /**
   * Core fetch wrapper with auth header injection and 401 refresh retry.
   */
  public async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = new Headers(options.headers || {});

    // Ensure JSON content type if body is present and not FormData
    if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    // Attach in-memory access token if available
    if (this.inMemoryAccessToken) {
      headers.set("Authorization", `Bearer ${this.inMemoryAccessToken}`);
      headers.set("Cache-Control", "no-store");
    }

    // Ensure cookies are included (for HttpOnly refresh_token)
    const fetchOptions: RequestInit = {
      ...options,
      headers,
      credentials: "include",
    };

    let response = await fetch(url, fetchOptions);

    // If 401 Unauthorized and not already calling auth endpoints, attempt token refresh
    if (response.status === 401 && !endpoint.startsWith("/auth/")) {
      const refreshedToken = await this.refreshToken();
      if (refreshedToken) {
        // Retry original request with newly refreshed token
        headers.set("Authorization", `Bearer ${refreshedToken}`);
        response = await fetch(url, { ...fetchOptions, headers });
      }
    }

    // Handle non-2xx responses
    if (!response.ok) {
      let problem: ProblemDetails;
      try {
        problem = await response.json();
      } catch {
        problem = {
          status: response.status,
          detail: response.statusText || "An unexpected error occurred",
        };
      }
      throw new ApiError(problem);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  }

  /**
   * Refreshes access token via HttpOnly refresh cookie.
   */
  public async refreshToken(): Promise<string | null> {
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: "POST",
          credentials: "include",
        });

        if (!response.ok) {
          this.inMemoryAccessToken = null;
          return null;
        }

        const data: TokenResponse = await response.json();
        this.inMemoryAccessToken = data.access_token;
        return data.access_token;
      } catch {
        this.inMemoryAccessToken = null;
        return null;
      } finally {
        this.isRefreshing = false;
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  // ==================== AUTH & USERS ====================

  public async login(req: LoginRequest): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(req),
    });
    this.setAccessToken(data.access_token);
    return data;
  }

  public async register(req: RegisterRequest): Promise<User> {
    const payload = {
      name: (req as any).name || (req as any).full_name || "New User",
      email: req.email,
      password: req.password,
      monthly_income: req.monthly_income ?? null,
      consent_ai: req.consent_ai ?? true,
    };
    return this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  public async logout(): Promise<void> {
    try {
      await this.request<void>("/auth/logout", {
        method: "POST",
      });
    } finally {
      this.setAccessToken(null);
    }
  }

  public async getMe(): Promise<User> {
    return this.request<User>("/users/me");
  }

  public async updateMe(req: UserUpdateRequest): Promise<User> {
    return this.request<User>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(req),
    });
  }

  public async exportUserData(): Promise<Blob> {
    const url = `${API_BASE_URL}/users/me/export`;
    const headers = new Headers();
    if (this.inMemoryAccessToken) {
      headers.set("Authorization", `Bearer ${this.inMemoryAccessToken}`);
    }
    const response = await fetch(url, {
      method: "GET",
      headers,
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error("Failed to export user data");
    }
    return response.blob();
  }

  public async deleteAccount(): Promise<void> {
    await this.request<void>("/users/me", {
      method: "DELETE",
    });
    this.setAccessToken(null);
  }

  // ==================== DASHBOARD ====================

  public async getDashboardOverview(): Promise<DashboardOverview> {
    return this.request<DashboardOverview>("/dashboard");
  }

  public async getMonthlyTrends(months: number = 6): Promise<MonthlySummary[]> {
    const res = await this.request<any>(`/dashboard/monthly?limit=${months}`);
    if (Array.isArray(res)) {
      return res;
    }
    if (res && Array.isArray(res.months)) {
      return res.months.map((m: any) => ({
        year_month: typeof m.month === "string" ? m.month.slice(0, 7) : (m.year_month || "2026-10"),
        total_income: Number(m.income ?? m.total_income ?? 0),
        total_expense: Number(m.expense ?? m.total_expense ?? 0),
        net_savings: Number(m.savings ?? m.net_savings ?? 0),
        savings_rate: Number(m.savings_rate ?? 0),
        necessity_expense: Number(m.necessity_expense ?? 0),
        discretionary_expense: Number(m.discretionary_expense ?? 0),
        transaction_count: Number(m.txn_count ?? m.transaction_count ?? 0),
      }));
    }
    return [];
  }

  public async getCategoryBreakdown(month?: string): Promise<CategoryBreakdown[]> {
    const q = month ? `?month=${month}` : "";
    return this.request<CategoryBreakdown[]>(`/dashboard/categories${q}`);
  }

  // ==================== TRANSACTIONS & CASHOUTS ====================

  public async listTransactions(params?: {
    cursor?: string;
    limit?: number;
    transaction_type?: string;
    category?: string;
  }): Promise<TransactionListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.cursor) searchParams.set("cursor", params.cursor);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.transaction_type) searchParams.set("transaction_type", params.transaction_type);
    if (params?.category) searchParams.set("category", params.category);

    const q = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request<TransactionListResponse>(`/transactions${q}`);
  }

  public async createTransaction(req: TransactionCreateRequest): Promise<Transaction> {
    const payload = {
      amount: req.amount,
      transaction_type: req.transaction_type,
      purpose: req.purpose,
      category: req.category,
      merchant: req.merchant || req.mfs_provider,
      description: req.description,
      idempotency_key: req.idempotency_key,
      ts: req.timestamp,
    };
    return this.request<Transaction>("/transactions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  public async createCashOut(req: CashOutCreateRequest): Promise<Transaction> {
    const payload = {
      amount: req.amount,
      purpose: req.purpose,
      category: req.category || "Cash Out",
      merchant: req.merchant || req.mfs_provider || "bkash",
      description: req.description,
      idempotency_key: req.idempotency_key,
      ts: req.timestamp,
    };
    return this.request<Transaction>("/cashouts", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  public async deleteTransaction(id: string): Promise<void> {
    return this.request<void>(`/transactions/${id}`, {
      method: "DELETE",
    });
  }

  // ==================== FINANCIAL GOALS ====================

  public async listGoals(): Promise<Goal[]> {
    const res = await this.request<any[]>("/goals");
    if (!Array.isArray(res)) return [];
    return res.map((g) => ({
      ...g,
      title: g.name || g.title,
    }));
  }

  public async getGoal(id: string): Promise<Goal> {
    const raw = await this.request<any>(`/goals/${id}`);
    return {
      ...raw,
      title: raw.name || raw.title,
    };
  }

  public async createGoal(req: GoalCreateRequest): Promise<Goal> {
    const payload: any = {
      name: (req as any).name || req.title,
      target_amount: req.target_amount,
    };
    if (req.target_date) {
      payload.target_date = req.target_date;
    }
    if ((req as any).initial_amount !== undefined) {
      payload.initial_amount = (req as any).initial_amount;
    } else if (req.current_amount !== undefined) {
      payload.initial_amount = req.current_amount;
    }

    const raw = await this.request<any>("/goals", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return {
      ...raw,
      title: raw.name || raw.title,
    };
  }

  public async updateGoal(id: string, req: GoalUpdateRequest): Promise<Goal> {
    const payload: any = {};
    if (req.title !== undefined || (req as any).name !== undefined) {
      payload.name = (req as any).name || req.title;
    }
    if (req.target_amount !== undefined) payload.target_amount = req.target_amount;
    if (req.target_date !== undefined) payload.target_date = req.target_date;
    if (req.status !== undefined) payload.status = req.status;

    const raw = await this.request<any>(`/goals/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    return {
      ...raw,
      title: raw.name || raw.title,
    };
  }

  public async deleteGoal(id: string): Promise<void> {
    return this.request<void>(`/goals/${id}`, {
      method: "DELETE",
    });
  }

  public async addGoalContribution(
    id: string,
    req: GoalContributionRequest
  ): Promise<GoalContributionResponse> {
    const payload: any = {
      amount: req.amount,
    };
    if ((req as any).transaction_id) {
      payload.transaction_id = (req as any).transaction_id;
    }
    return this.request<GoalContributionResponse>(`/goals/${id}/contributions`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // ==================== SIMULATION (PURE ENGINE) ====================

  public async simulateGrowth(req: GrowthSimulationRequest): Promise<GrowthSimulationResponse> {
    const rateDecimal = (req as any).annual_rate !== undefined
      ? (req as any).annual_rate
      : (req.annual_rate_percent !== undefined ? req.annual_rate_percent / 100 : 0.07);

    const payload = {
      initial_deposit: (req as any).initial_deposit ?? req.principal ?? 0,
      monthly_contribution: req.monthly_contribution ?? 0,
      annual_rate: rateDecimal,
      years: req.years ?? 5,
      compounding_per_year: req.compounding_per_year ?? 12,
      timing: (req as any).timing ?? "end",
      rate_type: req.rate_type ?? "assumed",
      inflation_adjusted: (req as any).inflation_adjusted ?? false,
    };

    const res = await this.request<any>("/simulate/growth", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    return {
      future_value: Number(res.future_value),
      total_contributed: Number(res.total_contributed),
      total_growth: Number(res.total_growth),
      assumptions: res.assumptions || {},
      series: (res.series || []).map((pt: any) => ({
        year: pt.year,
        balance: Number(pt.balance),
        total_contributed: Number(pt.contributions ?? pt.total_contributed ?? 0),
        total_growth: Number(pt.growth ?? pt.total_growth ?? 0),
      })),
      disclaimer: res.disclaimer_code || "PROJECTION_NOT_GUARANTEED",
    };
  }

  public async simulateDoubling(req: DoublingSimulationRequest): Promise<DoublingSimulationResponse> {
    const rateDecimal = (req as any).annual_rate !== undefined
      ? (req as any).annual_rate
      : (req.annual_rate_percent !== undefined ? req.annual_rate_percent / 100 : 0.08);

    const payload = {
      annual_rate: rateDecimal,
      compounding_per_year: (req as any).compounding_per_year ?? 12,
      rate_type: req.rate_type ?? "assumed",
    };

    const res = await this.request<any>("/simulate/doubling", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    return {
      years_exact: Number(res.years ?? 0),
      years_rule_of_72: Number(res.rule_of_72_approx ?? 0),
      disclaimer: res.disclaimer_code || "PROJECTION_NOT_GUARANTEED",
    };
  }

  public async simulateScenario(req: ScenarioSimulationRequest): Promise<ScenarioSimulationResponse> {
    const res = await this.request<any>("/simulate/scenario", {
      method: "POST",
      body: JSON.stringify(req),
    });
    return res;
  }

  // ==================== ML & AI INSIGHTS ====================

  public async getSpendingForecast(): Promise<SpendingForecast> {
    return this.request<SpendingForecast>("/forecast/expenses");
  }

  public async getSavingsForecast(): Promise<SavingsForecast> {
    return this.request<SavingsForecast>("/forecast/savings");
  }

  public async listAnomalies(): Promise<Anomaly[]> {
    return this.request<Anomaly[]>("/anomalies");
  }

  public async updateAnomalyStatus(
    id: string,
    req: AnomalyFeedbackRequest
  ): Promise<Anomaly> {
    return this.request<Anomaly>(`/anomalies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(req),
    });
  }

  public async getBehaviorProfile(allowColdStart: boolean = true): Promise<BehaviorProfile> {
    const q = allowColdStart ? "?allow_cold_start=true" : "";
    return this.request<BehaviorProfile>(`/behavior/profile${q}`);
  }

  public async getBehaviorInsights(allowColdStart: boolean = true): Promise<BehaviorInsights> {
    const q = allowColdStart ? "?allow_cold_start=true" : "";
    return this.request<BehaviorInsights>(`/behavior/insights${q}`);
  }

  // ==================== AI COACH & CHAT ====================

  public async getChatHistory(
    conversationId?: string,
    limit: number = 20
  ): Promise<ConversationHistoryResponse> {
    const q = new URLSearchParams();
    if (conversationId) q.set("conversation_id", conversationId);
    if (limit) q.set("limit", limit.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : "";
    return this.request<ConversationHistoryResponse>(`/chat/history${queryStr}`);
  }

  public async postChatFeedback(
    messageId: string,
    req: ChatFeedbackRequest
  ): Promise<ChatFeedbackResponse> {
    return this.request<ChatFeedbackResponse>(`/chat/${messageId}/feedback`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  public async postChat(req: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ ...req, stream: false }),
    });
  }

  public async streamChat(
    req: ChatRequest,
    callbacks: {
      onToken?: (event: StreamTokenEvent) => void;
      onToolStatus?: (event: StreamToolStatusEvent) => void;
      onUiAction?: (event: StreamUiActionEvent) => void;
      onDone?: (event: StreamDoneEvent) => void;
      onError?: (err: Error) => void;
    },
    signal?: AbortSignal
  ): Promise<void> {
    const url = `${API_BASE_URL}/chat`;
    const headers = new Headers({
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    });

    if (this.inMemoryAccessToken) {
      headers.set("Authorization", `Bearer ${this.inMemoryAccessToken}`);
    }

    try {
      let response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify({ ...req, stream: true }),
        credentials: "include",
        signal,
      });

      if (response.status === 401) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          headers.set("Authorization", `Bearer ${refreshed}`);
          response = await fetch(url, {
            method: "POST",
            headers,
            body: JSON.stringify({ ...req, stream: true }),
            credentials: "include",
            signal,
          });
        }
      }

      if (!response.ok) {
        let prob: ProblemDetails;
        try {
          prob = await response.json();
        } catch {
          prob = {
            status: response.status,
            title: "Chat Error",
            detail: `Server responded with ${response.status}`,
          };
        }
        throw new ApiError(prob);
      }

      if (!response.body) {
        throw new Error("ReadableStream not supported on this response");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        // Keep the last uncompleted block in the buffer
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.trim()) continue;

          let currentEvent = "message";
          let dataText = "";

          const lines = part.split("\n");
          for (const line of lines) {
            if (line.startsWith("event:")) {
              currentEvent = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              dataText += line.slice(5).trim();
            }
          }

          if (!dataText) continue;

          try {
            const parsedData = JSON.parse(dataText);
            if (currentEvent === "token" && callbacks.onToken) {
              callbacks.onToken(parsedData as StreamTokenEvent);
            } else if (currentEvent === "tool_status" && callbacks.onToolStatus) {
              callbacks.onToolStatus(parsedData as StreamToolStatusEvent);
            } else if (currentEvent === "ui_action" && callbacks.onUiAction) {
              callbacks.onUiAction(parsedData as StreamUiActionEvent);
            } else if (currentEvent === "done" && callbacks.onDone) {
              callbacks.onDone(parsedData as StreamDoneEvent);
            }
          } catch (e) {
            console.warn("Failed to parse SSE payload:", dataText, e);
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        return;
      }
      callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
      throw err;
    }
  }
}

export const apiClient = new ApiClient();
