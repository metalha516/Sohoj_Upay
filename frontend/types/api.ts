/**
 * TypeScript API interfaces matching FastAPI OpenAPI contracts for Sohoj.
 */

export type Purpose = "necessity" | "savings_goal" | "discretionary" | "other";

export type TransactionType = "cash_in" | "cash_out" | "send_money" | "payment" | "transfer";

export type MFSProvider = "bkash" | "nagad" | "rocket" | "upay" | "bank" | "other";

export type GoalStatus = "in_progress" | "achieved" | "paused" | "abandoned";

export interface ProblemDetails {
  type?: string;
  title?: string;
  status: number;
  detail: string;
  instance?: string;
  code?: string;
  guidance?: string;
  errors?: Array<{ loc: string[]; msg: string; type: string }>;
}

export interface User {
  id: string;
  email: string;
  phone_number: string;
  full_name: string;
  occupation: string;
  monthly_income: number | null;
  starting_balance: number;
  consent_ai: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  phone_number: string;
  full_name: string;
  occupation: string;
  monthly_income?: number | null;
  starting_balance?: number;
  consent_ai?: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserUpdateRequest {
  full_name?: string;
  occupation?: string;
  monthly_income?: number | null;
  consent_ai?: boolean;
}

export interface Transaction {
  id: string;
  user_id: string;
  timestamp: string;
  amount: number;
  transaction_type: TransactionType;
  purpose: Purpose;
  category: string;
  mfs_provider: MFSProvider;
  counterparty?: string | null;
  merchant?: string | null;
  description?: string | null;
  is_flagged_anomaly: boolean;
  created_at: string;
}

export interface TransactionCreateRequest {
  timestamp?: string;
  amount: number;
  transaction_type: TransactionType;
  purpose: Purpose;
  category: string;
  mfs_provider?: MFSProvider;
  counterparty?: string | null;
  merchant?: string | null;
  description?: string | null;
  idempotency_key?: string;
}

export interface CashOutCreateRequest {
  amount: number;
  purpose: Purpose;
  category: string;
  mfs_provider?: MFSProvider;
  merchant?: string | null;
  description?: string | null;
  timestamp?: string;
  idempotency_key?: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  next_cursor?: string | null;
  has_more: boolean;
  total_count?: number;
}

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  category?: string;
  status: GoalStatus;
  progress_pct: number;
  shortfall: number;
  required_monthly_saving: number;
  estimated_completion_date?: string | null;
  is_feasible: boolean;
  feasibility_status: string;
  created_at: string;
  updated_at: string;
}

export interface GoalCreateRequest {
  title: string;
  target_amount: number;
  target_date: string;
  category?: string;
  current_amount?: number;
}

export interface GoalUpdateRequest {
  title?: string;
  target_amount?: number;
  target_date?: string;
  status?: GoalStatus;
}

export interface GoalContributionRequest {
  amount: number;
  note?: string;
}

export interface GoalContributionResponse {
  id: string;
  goal_id: string;
  amount: number;
  progress_pct: number;
  new_current_amount: number;
  shortfall: number;
  created_at: string;
}

export interface MonthlySummary {
  year_month: string;
  total_income: number;
  total_expense: number;
  net_savings: number;
  savings_rate: number;
  necessity_expense: number;
  discretionary_expense: number;
  transaction_count: number;
}

export interface CategoryBreakdown {
  category: string;
  purpose: Purpose;
  total_amount: number;
  percentage: number;
  transaction_count: number;
}

export interface DashboardOverview {
  current_balance: number;
  monthly_income: number;
  monthly_expense: number;
  monthly_savings: number;
  savings_rate: number;
  necessity_ratio: number;
  emergency_fund_months: number;
  active_goals_count: number;
  anomalies_count: number;
  behavior_persona?: string | null;
  monthly_trend: MonthlySummary[];
  category_breakdown: CategoryBreakdown[];
  recent_transactions: Transaction[];
  active_goals: Goal[];
}

export interface GrowthSimulationRequest {
  principal: number;
  monthly_contribution: number;
  annual_rate_percent: number;
  years: number;
  compounding_per_year?: number;
  rate_type?: "assumed" | "historical" | "contractual";
}

export interface GrowthSeriesPoint {
  year: number;
  month: number;
  total_contributed: number;
  total_growth: number;
  balance: number;
}

export interface GrowthSimulationResponse {
  future_value: number;
  total_contributed: number;
  total_growth: number;
  assumptions: {
    principal: number;
    monthly_contribution: number;
    annual_rate_percent: number;
    years: number;
    compounding_per_year: number;
    rate_type: string;
  };
  series: GrowthSeriesPoint[];
  disclaimer: string;
}

export interface DoublingSimulationRequest {
  annual_rate_percent: number;
  rate_type?: "assumed" | "historical" | "contractual";
}

export interface DoublingSimulationResponse {
  years_exact: number;
  years_rule_of_72: number;
  disclaimer: string;
}

export interface GoalSimulationRequest {
  target_amount: number;
  current_amount: number;
  years: number;
  annual_rate_percent: number;
  rate_type?: "assumed" | "historical" | "contractual";
}

export interface GoalSimulationResponse {
  required_monthly_saving: number;
  target_amount: number;
  total_contributed: number;
  total_interest: number;
  disclaimer: string;
}

export interface ScenarioSimulationRequest {
  base_income: number;
  base_expenses: number;
  income_shock_pct?: number;
  expense_shock_pct?: number;
  current_savings: number;
}

export interface ScenarioSimulationResponse {
  projected_income: number;
  projected_expenses: number;
  projected_monthly_savings: number;
  new_savings_rate: number;
  emergency_runway_months: number;
  is_sustainable: boolean;
  disclaimer: string;
}

export interface SpendingForecast {
  predicted_expense: number;
  interval_p10: number;
  interval_p90: number;
  confidence: number;
  model_version: string;
  disclaimer: string;
}

export interface SavingsForecast {
  predicted_savings: number;
  predicted_savings_rate: number;
  confidence: number;
  model_version: string;
  disclaimer: string;
}

export interface Anomaly {
  id: string;
  transaction_id?: string | null;
  scope: string;
  category?: string | null;
  anomaly_score: number;
  confidence: number;
  observed_value?: number;
  baseline_value?: number;
  observed?: number;
  baseline?: number;
  deviation_pct: number;
  explanation: Record<string, any> | string;
  model_version?: string;
  status: "open" | "dismissed" | "confirmed" | "pending";
  created_at: string;
}

export interface AnomalyFeedbackRequest {
  status: "dismissed" | "confirmed";
  feedback_notes?: string;
}

export interface BehaviorProfile {
  user_id?: string;
  profile: string;
  persona_label?: string;
  confidence: number;
  description?: string;
  top_factors: Array<Record<string, any>> | Record<string, any>;
  savings_rate?: number | null;
  necessity_rate?: number | null;
  discretionary_rate?: number | null;
  cashout_frequency?: number | null;
  spending_variance?: number | null;
  model_version?: string;
  as_of_month?: string;
  is_cold_start?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AIInsight {
  id: string;
  title: string;
  recommendation_text: string;
  priority: "low" | "medium" | "high";
  source_refs: string[];
  created_at: string;
}

export interface BehaviorInsightItem {
  id: string;
  type: string;
  title: string;
  content: string;
  priority: number;
  source_refs?: Record<string, any> | null;
  created_at: string;
}

export interface BehaviorInsights {
  profile: string;
  confidence: number;
  model_version: string;
  top_factors: Array<Record<string, any>> | Record<string, any>;
  insights: BehaviorInsightItem[];
  primary_recommendation?: string;
}

// ==================== CHAT API TYPES ====================

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  stream?: boolean;
}

export interface ChatResponse {
  message_id: string;
  conversation_id: string;
  role: string;
  content: string;
  ui_action?: string | null;
  ui_action_payload?: Record<string, any> | null;
  tokens_in: number;
  tokens_out: number;
  latency_ms: number;
  prompt_version: string;
  is_fallback: boolean;
  is_grounded: boolean;
}

export interface ChatMessageItem {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  feedback?: number | null;
  created_at: string;
  tool_calls?: Record<string, any> | null;
}

export interface ConversationItem {
  id: string;
  title?: string | null;
  created_at: string;
  message_count: number;
  messages: ChatMessageItem[];
}

export interface ConversationHistoryResponse {
  conversations: ConversationItem[];
}

export interface ChatFeedbackRequest {
  feedback: number;
}

export interface ChatFeedbackResponse {
  message_id: string;
}

export interface StreamToolStatusEvent {
  tool: string;
  status: "running" | "completed";
  call_index: number;
}

export interface StreamTokenEvent {
  text: string;
}

export interface StreamUiActionEvent {
  ui_action: string;
  payload?: Record<string, any> | null;
}

export interface StreamDoneEvent {
  message_id: string;
  conversation_id: string;
  content: string;
  is_fallback: boolean;
  is_grounded: boolean;
  tokens_in?: number;
  tokens_out?: number;
  latency_ms?: number;
}


