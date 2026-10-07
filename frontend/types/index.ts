export interface LatestPrice {
  price_24k_inr: number;
  price_22k_inr: number | null;
  price_24k_10g_inr: number;
  price_22k_10g_inr: number | null;
  source: string;
  source_timestamp: string;
  is_converted: boolean;
  fetched_at: string;
  benchmark_status: string;
  is_stale: boolean;
  notes: string | null;
}

export interface WindowMetric {
  window_days: number;
  actual_days: number;
  high: number;
  low: number;
  average: number;
  pct_change: number;
  range_position: number;
  percentile_rank: number;
  drawdown_pct: number;
  distance_from_sma_pct: number;
  is_partial: boolean;
}

export interface SubScore {
  name: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  description: string;
}

export interface ScoreReport {
  total_score: number;
  category: string;
  is_cheap: "YES" | "NO" | "NORMAL";
  fixed_amount: number;
  extra_amount: number;
  total_amount: number;
  why_explanation: string;
  disclaimer: string;
  sub_scores: Record<string, SubScore>;
}

export interface AnalysisPayload {
  latest_price: LatestPrice;
  analysis: {
    current_price: number;
    total_data_points: number;
    data_degraded: boolean;
    degraded_reason: string | null;
    volatility: {
      daily_std_dev: number;
      annualized_volatility_pct: number;
      label: "Low" | "Medium" | "High";
    };
    momentum: {
      roc_10d_pct: number | null;
      roc_30d_pct: number | null;
      roc_60d_pct: number | null;
      roc_90d_pct: number | null;
    };
    windows: {
      "30": WindowMetric;
      "60": WindowMetric;
      "90": WindowMetric;
    };
  };
  score_report: ScoreReport;
}

export interface PricePoint {
  id?: number;
  date: string;
  price_24k_inr: number;
  price_22k_inr: number | null;
  source: string;
  is_converted: boolean;
}

export interface InvestmentItem {
  id: number;
  date: string;
  time_ist: string;
  market_price: number;
  model_score: number | null;
  model_rec_fixed: number;
  model_rec_extra: number;
  model_rec_total: number;
  actual_amount: number;
  gst_paid: number | null;
  actual_grams: number;
  is_estimated_grams: boolean;
  avg_purchase_price: number;
  notes: string | null;
}

export interface PortfolioSummary {
  total_invested: number;
  total_grams: number;
  current_market_price: number;
  current_nominal_value: number;
  estimated_net_selling_value: number;
  sell_spread_pct: number;
  unrealized_pnl: number;
  return_pct: number;
  avg_purchase_price: number;
  investment_days: number;
  avg_daily_investment: number;
  total_fixed_amount: number;
  total_extra_amount: number;
  followed_rec_days: number;
  diverged_rec_days: number;
}

export interface StrategyMetrics {
  name: string;
  total_invested: number;
  total_grams: number;
  avg_cost_per_gram: number;
  final_value: number;
  return_pct: number;
  max_drawdown_pct: number;
}

export interface BacktestPayload {
  days_tested: number;
  start_date: string;
  end_date: string;
  sample_warning: string | null;
  disclaimer: string;
  extra_money_deployed: number;
  cost_difference_per_gram: number;
  cost_improvement_pct: number;
  model_lowered_cost: boolean;
  strategy_a: StrategyMetrics;
  strategy_b: StrategyMetrics;
  strategy_scaled: StrategyMetrics;
  signal_counts: Record<string, number>;
  daily_history: Array<{
    date: string;
    price: number;
    score: number;
    category: string;
    extra_amount: number;
    strat_a_amount: number;
    strat_b_amount: number;
    scaled_amount: number;
  }>;
}
