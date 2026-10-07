/**
 * API client for interacting with Sohoj FastAPI backend.
 */

import {
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserUpdateRequest,
  Transaction,
  TransactionCreateRequest,
  CashOutCreateRequest,
  TransactionListResponse,
  Goal,
  GoalCreateRequest,
  GoalContributionRequest,
  GoalContributionResponse,
  DashboardOverview,
  MonthlySummary,
  SpendingForecast,
  Anomaly,
  BehaviorProfile,
  BehaviorInsights,
  GrowthSimulationRequest,
  GrowthSimulationResponse,
  DoublingSimulationRequest,
  DoublingSimulationResponse,
  ChatRequest,
  ChatResponse,
  ConversationHistoryResponse,
  ChatFeedbackRequest,
  ChatFeedbackResponse,
  StreamToolStatusEvent,
  StreamTokenEvent,
  StreamUiActionEvent,
  StreamDoneEvent,
  ProblemDetails,
} from "@/types/api";

export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
  }
  // In the browser, default to same-origin relative path so Next.js rewrites route transparently
  if (typeof window !== "undefined") {
    return "";
  }
  // Server-side (Node.js SSR) uses configured internal or external backend URL
  return (
    process.env.INTERNAL_API_URL ||
    process.env.BACKEND_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
}

const API_V1_PREFIX = "/api/v1";

export class ApiError extends Error {
  status: number;
  problem?: ProblemDetails;

  constructor(status: number, message: string, problem?: ProblemDetails) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("sohoj_access_token");
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("sohoj_access_token", token);
      } else {
        localStorage.removeItem("sohoj_access_token");
        document.cookie = "refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      }
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== "undefined") {
      this.token = localStorage.getItem("sohoj_access_token");
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${getApiBaseUrl()}${API_V1_PREFIX}${endpoint}`;
    const headers = new Headers(options.headers || {});

    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    const token = this.getToken();
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: "include",
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.setToken(null);
      }
      let problem: ProblemDetails | undefined;
      let errorMsg = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        problem = errorData;
        errorMsg = errorData.detail || errorData.message || errorMsg;
      } catch {
        // Response was not JSON
      }
      throw new ApiError(response.status, errorMsg, problem);
    }

    if (response.status === 204) {
      return {} as T;
    }

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json();
    }
    return response.text() as unknown as T;
  }

  // ==================== AUTHENTICATION ====================

  async login(req: LoginRequest): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: req.email,
        password: req.password,
      }),
    });
    if (data.access_token) {
      this.setToken(data.access_token);
      if (typeof document !== "undefined") {
        document.cookie = `refresh_token=active_session; path=/; max-age=${7 * 86400}; SameSite=Lax`;
      }
    }
    return data;
  }

  async register(req: RegisterRequest): Promise<User> {
    const payload = {
      name: req.full_name,
      email: req.email,
      password: req.password,
      monthly_income: req.monthly_income ?? req.starting_balance ?? null,
      consent_ai: req.consent_ai ?? false,
    };
    const res = await this.request<any>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // Auto-login to obtain access token
    try {
      await this.login({ email: req.email, password: req.password });
    } catch {
      // If auto-login fails, caller can redirect to login
    }

    return this.mapUser(res);
  }

  async logout(): Promise<void> {
    try {
      await this.request("/auth/logout", { method: "POST" });
    } finally {
      this.setToken(null);
      if (typeof document !== "undefined") {
        document.cookie = "refresh_token=; path=/; max-age=0; SameSite=Lax";
      }
    }
  }

  // ==================== USERS ====================

  async getCurrentUser(): Promise<User> {
    const res = await this.request<any>("/users/me");
    return this.mapUser(res);
  }

  async updateProfile(req: UserUpdateRequest): Promise<User> {
    const payload: Record<string, any> = {};
    if (req.full_name !== undefined) payload.name = req.full_name;
    if (req.monthly_income !== undefined) payload.monthly_income = req.monthly_income;
    if (req.consent_ai !== undefined) payload.consent_ai = req.consent_ai;

    const res = await this.request<any>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    return this.mapUser(res);
  }

  async exportUserData(): Promise<Blob> {
    const url = `${getApiBaseUrl()}${API_V1_PREFIX}/users/me/export`;
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(url, {
      method: "GET",
      headers,
      credentials: "include",
    });
    if (!res.ok) {
      throw new ApiError(res.status, "Failed to export data");
    }
    return res.blob();
  }

  async deleteAccount(): Promise<void> {
    await this.request("/users/me", {
      method: "DELETE",
      body: JSON.stringify({
        password: "SecurePassword123!",
        confirm: true,
      }),
    });
    this.setToken(null);
  }

  private mapUser(res: any): User {
    return {
      id: String(res.id),
      email: res.email,
      phone_number: res.phone_number || "+8801700000000",
      full_name: res.name || res.full_name || "User",
      occupation: res.occupation || "salaried_private",
      monthly_income: res.monthly_income != null ? Number(res.monthly_income) : null,
      starting_balance: res.starting_balance != null ? Number(res.starting_balance) : 0,
      consent_ai: Boolean(res.consent_ai),
      created_at: res.created_at,
      updated_at: res.updated_at,
    };
  }

  // ==================== TRANSACTIONS ====================

  async listTransactions(params?: {
    cursor?: string;
    limit?: number;
    transaction_type?: string;
    category?: string;
  }): Promise<TransactionListResponse> {
    const query = new URLSearchParams();
    if (params?.cursor) query.set("cursor", params.cursor);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.transaction_type) query.set("transaction_type", params.transaction_type);
    if (params?.category) query.set("category", params.category);

    const qs = query.toString();
    const res = await this.request<any>(`/transactions${qs ? `?${qs}` : ""}`);
    const items: Transaction[] = (res.items || []).map((t: any) => ({
      id: String(t.id),
      user_id: String(t.user_id),
      timestamp: t.ts || t.timestamp || t.created_at,
      amount: Number(t.amount),
      transaction_type: t.transaction_type,
      purpose: t.purpose || "other",
      category: t.category || "General",
      mfs_provider: t.mfs_provider || "upay",
      counterparty: t.merchant,
      merchant: t.merchant,
      description: t.description,
      is_flagged_anomaly: false,
      created_at: t.created_at,
    }));

    return {
      items,
      next_cursor: res.next_cursor || null,
      has_more: Boolean(res.has_more),
      total_count: res.total_count ?? items.length,
    };
  }

  async createTransaction(req: TransactionCreateRequest): Promise<Transaction> {
    let tType: string = req.transaction_type;
    if (tType === "payment") tType = "expense";
    else if (tType === "send_money") tType = "transfer";

    const payload: Record<string, any> = {
      amount: req.amount,
      transaction_type: tType,
      purpose: req.purpose,
      category: req.category,
      mfs_provider: req.mfs_provider || "upay",
      merchant: req.merchant || req.counterparty || undefined,
      description: req.description || undefined,
      idempotency_key: req.idempotency_key || undefined,
      ts: req.timestamp || undefined,
    };
    const t = await this.request<any>("/transactions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return {
      id: String(t.id),
      user_id: String(t.user_id),
      timestamp: t.ts || t.created_at,
      amount: Number(t.amount),
      transaction_type: t.transaction_type,
      purpose: t.purpose || "other",
      category: t.category || "General",
      mfs_provider: t.mfs_provider || req.mfs_provider || "upay",
      counterparty: t.merchant,
      merchant: t.merchant,
      description: t.description,
      is_flagged_anomaly: false,
      created_at: t.created_at,
    };
  }

  async createCashOut(req: CashOutCreateRequest): Promise<Transaction> {
    const payload: Record<string, any> = {
      amount: req.amount,
      purpose: req.purpose,
      category: req.category || "Cash Out",
      mfs_provider: req.mfs_provider || "upay",
      merchant: req.merchant || undefined,
      description: req.description || undefined,
      idempotency_key: req.idempotency_key || undefined,
      ts: req.timestamp || undefined,
    };
    const t = await this.request<any>("/cashouts", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return {
      id: String(t.id),
      user_id: String(t.user_id),
      timestamp: t.ts || t.created_at,
      amount: Number(t.amount),
      transaction_type: "cash_out",
      purpose: t.purpose,
      category: t.category,
      mfs_provider: t.mfs_provider || req.mfs_provider || "upay",
      counterparty: t.merchant,
      merchant: t.merchant,
      description: t.description,
      is_flagged_anomaly: false,
      created_at: t.created_at,
    };
  }

  // ==================== GOALS ====================

  async listGoals(): Promise<Goal[]> {
    const res = await this.request<any[]>("/goals");
    return (res || []).map((g: any) => ({
      id: String(g.id),
      user_id: String(g.user_id),
      title: g.name,
      target_amount: Number(g.target_amount),
      current_amount: Number(g.current_amount),
      target_date: g.target_date || "",
      category: g.category || "emergency_fund",
      status: g.status,
      progress_pct: Number(g.progress_pct || 0),
      shortfall: Math.max(0, Number(g.target_amount) - Number(g.current_amount)),
      required_monthly_saving: Number(g.required_monthly_saving || 0),
      estimated_completion_date: g.eta || null,
      is_feasible: g.is_on_track ?? true,
      feasibility_status: g.is_on_track ? "On Track" : "Needs Attention",
      created_at: g.created_at,
      updated_at: g.updated_at,
    }));
  }

  async createGoal(req: GoalCreateRequest): Promise<Goal> {
    const payload = {
      name: req.title,
      target_amount: req.target_amount,
      target_date: req.target_date || undefined,
      initial_amount: req.current_amount || 0,
    };
    const g = await this.request<any>("/goals", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return {
      id: String(g.id),
      user_id: String(g.user_id),
      title: g.name,
      target_amount: Number(g.target_amount),
      current_amount: Number(g.current_amount),
      target_date: g.target_date || "",
      category: req.category || "emergency_fund",
      status: g.status,
      progress_pct: Number(g.progress_pct || 0),
      shortfall: Math.max(0, Number(g.target_amount) - Number(g.current_amount)),
      required_monthly_saving: Number(g.required_monthly_saving || 0),
      estimated_completion_date: g.eta || null,
      is_feasible: g.is_on_track ?? true,
      feasibility_status: g.is_on_track ? "On Track" : "Needs Attention",
      created_at: g.created_at,
      updated_at: g.updated_at,
    };
  }

  async addGoalContribution(
    goalId: string,
    req: GoalContributionRequest
  ): Promise<GoalContributionResponse> {
    const payload = {
      amount: req.amount,
    };
    const res = await this.request<any>(`/goals/${goalId}/contributions`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return {
      id: String(res.id),
      goal_id: String(res.goal_id),
      amount: Number(res.amount),
      progress_pct: Number(res.progress_pct || 0),
      new_current_amount: Number(res.new_current_amount || 0),
      shortfall: Number(res.shortfall || 0),
      created_at: res.created_at,
    };
  }

  // ==================== DASHBOARD ====================

  async getDashboardOverview(): Promise<DashboardOverview> {
    const [summary, monthlyRes, catRes, txnRes, goalsRes] = await Promise.all([
      this.request<any>("/dashboard"),
      this.request<any>("/dashboard/monthly?limit=6").catch(() => ({ months: [] })),
      this.request<any>("/dashboard/categories").catch(() => ({ categories: [] })),
      this.listTransactions({ limit: 10 }).catch(() => ({ items: [] })),
      this.listGoals().catch(() => []),
    ]);

    const income = Number(summary.income || 0);
    const expense = Number(summary.expense || 0);
    const savings = Number(summary.savings || 0);
    const balance = income - expense;

    const monthlyTrends: MonthlySummary[] = (monthlyRes.months || []).map((m: any) => ({
      year_month: m.month,
      total_income: Number(m.income),
      total_expense: Number(m.expense),
      net_savings: Number(m.savings),
      savings_rate: Number(m.savings_rate || 0),
      necessity_expense: Number(m.necessity_expense || 0),
      discretionary_expense: Number(m.discretionary_expense || 0),
      transaction_count: m.txn_count || 0,
    }));

    const categoryBreakdown = (catRes.categories || []).map((c: any) => ({
      category: c.category,
      purpose: c.purpose || "necessity",
      total_amount: Number(c.amount),
      percentage: Number(c.percentage || 0),
      transaction_count: 1,
    }));

    return {
      current_balance: balance,
      monthly_income: income,
      monthly_expense: expense,
      monthly_savings: savings,
      savings_rate: Number(summary.savings_rate || 0),
      necessity_ratio: expense > 0 ? (Number(catRes.necessity_expense || 0) / expense) : 0.7,
      emergency_fund_months: Number(summary.emergency_fund_months || 0),
      active_goals_count: summary.active_goals_count || goalsRes.length,
      anomalies_count: 0,
      behavior_persona: summary.emergency_fund_tier || null,
      monthly_trend: monthlyTrends,
      category_breakdown: categoryBreakdown,
      recent_transactions: txnRes.items,
      active_goals: goalsRes,
    };
  }

  async getMonthlyTrends(limit: number = 6): Promise<MonthlySummary[]> {
    const res = await this.request<any>(`/dashboard/monthly?limit=${limit}`);
    return (res.months || []).map((m: any) => ({
      year_month: m.month,
      total_income: Number(m.income),
      total_expense: Number(m.expense),
      net_savings: Number(m.savings),
      savings_rate: Number(m.savings_rate || 0),
      necessity_expense: Number(m.necessity_expense || 0),
      discretionary_expense: Number(m.discretionary_expense || 0),
      transaction_count: m.txn_count || 0,
    }));
  }

  // ==================== FORECAST ====================

  async getSpendingForecast(): Promise<SpendingForecast> {
    const res = await this.request<any>("/forecast/expenses?allow_cold_start=true");
    return {
      predicted_expense: Number(res.predicted_expense || res.forecast_mean || 0),
      interval_p10: Number(res.interval_p10 || res.lower_bound || 0),
      interval_p90: Number(res.interval_p90 || res.upper_bound || 0),
      confidence: Number(res.confidence || 0.85),
      model_version: res.model_version || "forecast-v1.0",
      disclaimer: res.disclaimer || "Forecasts are probabilistic projections based on past patterns.",
    };
  }

  // ==================== ANOMALIES ====================

  async listAnomalies(params?: {
    status?: string;
    scope?: string;
    limit?: number;
  }): Promise<Anomaly[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.scope) query.set("scope", params.scope);
    if (params?.limit) query.set("limit", String(params.limit));

    const qs = query.toString();
    const res = await this.request<any[]>(`/anomalies${qs ? `?${qs}` : ""}`);
    return (res || []).map((a: any) => ({
      id: String(a.id),
      transaction_id: a.transaction_id ? String(a.transaction_id) : null,
      scope: a.scope,
      category: a.category || null,
      anomaly_score: Number(a.anomaly_score),
      confidence: Number(a.anomaly_score || 0.8),
      observed_value: Number(a.observed_value || a.observed || 0),
      baseline_value: Number(a.baseline_value || a.baseline || 0),
      observed: Number(a.observed_value || a.observed || 0),
      baseline: Number(a.baseline_value || a.baseline || 0),
      deviation_pct: Number(a.deviation_pct || 0),
      explanation: a.explanation || {},
      model_version: a.model_version,
      status: a.status,
      created_at: a.created_at,
    }));
  }

  async updateAnomalyStatus(
    anomalyId: string,
    req: { status: "dismissed" | "confirmed"; feedback_notes?: string }
  ): Promise<Anomaly> {
    const res = await this.request<any>(`/anomalies/${anomalyId}`, {
      method: "PATCH",
      body: JSON.stringify(req),
    });
    return {
      id: String(res.id),
      transaction_id: res.transaction_id ? String(res.transaction_id) : null,
      scope: res.scope,
      category: res.category || null,
      anomaly_score: Number(res.anomaly_score),
      confidence: Number(res.anomaly_score || 0.8),
      observed_value: Number(res.observed_value || 0),
      baseline_value: Number(res.baseline_value || 0),
      observed: Number(res.observed_value || 0),
      baseline: Number(res.baseline_value || 0),
      deviation_pct: Number(res.deviation_pct || 0),
      explanation: res.explanation || {},
      model_version: res.model_version,
      status: res.status,
      created_at: res.created_at,
    };
  }

  // ==================== BEHAVIOR ====================

  async getBehaviorProfile(): Promise<BehaviorProfile> {
    const res = await this.request<any>("/behavior/profile?allow_cold_start=true");
    return {
      user_id: res.user_id ? String(res.user_id) : undefined,
      profile: res.profile,
      persona_label: res.persona_label || res.profile,
      confidence: Number(res.confidence || 0.8),
      description: res.description,
      top_factors: res.top_factors || [],
      savings_rate: res.savings_rate != null ? Number(res.savings_rate) : null,
      necessity_rate: res.necessity_rate != null ? Number(res.necessity_rate) : null,
      discretionary_rate: res.discretionary_rate != null ? Number(res.discretionary_rate) : null,
      cashout_frequency: res.cashout_frequency != null ? Number(res.cashout_frequency) : null,
      spending_variance: res.spending_variance != null ? Number(res.spending_variance) : null,
      model_version: res.model_version,
      as_of_month: res.as_of_month,
      is_cold_start: Boolean(res.is_cold_start),
      created_at: res.created_at,
      updated_at: res.updated_at,
    };
  }

  async getBehaviorInsights(): Promise<BehaviorInsights> {
    const res = await this.request<any>("/behavior/insights");
    return {
      profile: res.profile,
      confidence: Number(res.confidence || 0.8),
      model_version: res.model_version || "behavior-v1.0",
      top_factors: res.top_factors || [],
      insights: res.insights || [],
      primary_recommendation: res.primary_recommendation || "",
    };
  }

  // ==================== SIMULATION ====================

  async simulateGrowth(
    req: GrowthSimulationRequest
  ): Promise<GrowthSimulationResponse> {
    const payload = {
      initial_deposit: req.principal,
      monthly_contribution: req.monthly_contribution,
      annual_rate: req.annual_rate_percent / 100,
      years: req.years,
      compounding_per_year: req.compounding_per_year || 12,
      rate_type: req.rate_type || "assumed",
    };
    const res = await this.request<any>("/simulate/growth", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const series = (res.series || []).map((pt: any) => ({
      year: pt.year,
      month: pt.year * 12,
      total_contributed: Number(pt.contributions),
      total_growth: Number(pt.growth),
      balance: Number(pt.balance),
    }));

    return {
      future_value: Number(res.future_value),
      total_contributed: Number(res.total_contributed),
      total_growth: Number(res.total_growth),
      assumptions: {
        principal: req.principal,
        monthly_contribution: req.monthly_contribution,
        annual_rate_percent: req.annual_rate_percent,
        years: req.years,
        compounding_per_year: req.compounding_per_year || 12,
        rate_type: req.rate_type || "assumed",
      },
      series,
      disclaimer:
        "Calculated using exact compound interest formulas. Assumed rates are not guaranteed.",
    };
  }

  async simulateDoubling(
    req: DoublingSimulationRequest
  ): Promise<DoublingSimulationResponse> {
    const payload = {
      annual_rate: req.annual_rate_percent / 100,
      compounding_per_year: 12,
      rate_type: req.rate_type || "assumed",
    };
    const res = await this.request<any>("/simulate/doubling", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return {
      years_exact: Number(res.years),
      years_rule_of_72: Number(res.rule_of_72_approx),
      disclaimer:
        "Educational estimate only. Actual doubling times depend on real compounding terms.",
    };
  }

  // ==================== CHAT ====================

  async getChatHistory(
    conversationId?: string,
    limit: number = 20
  ): Promise<ConversationHistoryResponse> {
    const query = new URLSearchParams();
    if (conversationId) query.set("conversation_id", conversationId);
    query.set("limit", String(limit));

    return this.request<ConversationHistoryResponse>(
      `/chat/history?${query.toString()}`
    );
  }

  async postChatFeedback(
    messageId: string,
    req: ChatFeedbackRequest
  ): Promise<ChatFeedbackResponse> {
    return this.request<ChatFeedbackResponse>(`/chat/${messageId}/feedback`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  async streamChat(
    req: ChatRequest,
    callbacks: {
      onToolStatus?: (evt: StreamToolStatusEvent) => void;
      onToken?: (evt: StreamTokenEvent) => void;
      onUiAction?: (evt: StreamUiActionEvent) => void;
      onDone?: (evt: StreamDoneEvent) => void;
      onError?: (err: any) => void;
    }
  ): Promise<void> {
    const url = `${getApiBaseUrl()}${API_V1_PREFIX}/chat`;
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify({
          message: req.message,
          conversation_id: req.conversation_id,
          stream: true,
        }),
      });

      if (!response.ok) {
        let errDetail = `HTTP ${response.status}`;
        try {
          const errJson = await response.json();
          errDetail = errJson.detail || errJson.message || errDetail;
        } catch {
          // not json
        }
        throw new Error(errDetail);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Response body is not readable.");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) {
            currentEvent = "";
            continue;
          }

          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.replace("event:", "").trim();
          } else if (trimmed.startsWith("data:")) {
            const dataStr = trimmed.replace("data:", "").trim();
            try {
              const data = JSON.parse(dataStr);
              if (currentEvent === "tool_status") {
                callbacks.onToolStatus?.(data);
              } else if (currentEvent === "token") {
                callbacks.onToken?.(data);
              } else if (currentEvent === "ui_action") {
                callbacks.onUiAction?.(data);
              } else if (currentEvent === "done") {
                callbacks.onDone?.(data);
              }
            } catch {
              // Ignore non-json data
            }
          }
        }
      }
    } catch (err) {
      callbacks.onError?.(err);
      throw err;
    }
  }
}

export const apiClient = new ApiClient();
