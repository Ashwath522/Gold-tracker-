from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Any
import numpy as np
from .engine import run_analysis
from .scorer import evaluate_model
from .weights import ScoreWeights, DEFAULT_WEIGHTS
from ..config import settings

@dataclass
class DailySimRecord:
    date: str
    price: float
    score: float
    category: str
    extra_amount: float
    strat_a_amount: float
    strat_a_grams: float
    strat_b_amount: float
    strat_b_grams: float
    scaled_amount: float
    scaled_grams: float

@dataclass
class StrategyMetrics:
    name: str
    total_invested: float
    total_grams: float
    avg_cost_per_gram: float
    final_value: float
    return_pct: float
    max_drawdown_pct: float

@dataclass
class BacktestResult:
    days_tested: int
    start_date: str
    end_date: str
    strategy_a: StrategyMetrics  # Fixed ₹35
    strategy_b: StrategyMetrics  # Fixed ₹35 + Model Extra
    strategy_scaled: StrategyMetrics  # Equal-Total-Spend Baseline
    extra_money_deployed: float
    cost_difference_per_gram: float  # scaled_avg_cost - strat_b_avg_cost (positive = model lowered cost)
    cost_improvement_pct: float
    model_lowered_cost: bool
    signal_counts: Dict[str, int]
    daily_history: List[DailySimRecord]
    sample_warning: Optional[str] = None
    disclaimer: str = "Past simulated performance is not an indicator of future results. Models can underperform in protracted bull runs."

def compute_portfolio_drawdown(daily_values: List[float]) -> float:
    """Computes peak-to-trough max drawdown of portfolio balance."""
    if not daily_values:
        return 0.0
    arr = np.array(daily_values)
    peaks = np.maximum.accumulate(arr)
    drawdowns = (arr - peaks) / peaks * 100.0
    return round(float(np.min(drawdowns)), 2)

def run_backtest(
    dates: List[date],
    prices: List[float],
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    gst_rate: float = 0.03,
    min_warmup_days: int = 30
) -> BacktestResult:
    """
    Honest day-by-day simulation using strictly data available up to each day (no lookahead).
    Compares:
    1. Strategy A: ₹35 fixed every day
    2. Strategy B: ₹35 fixed + model recommended extra
    3. Strategy Scaled: Equal total spend baseline evenly distributed
    """
    n = len(prices)
    if n <= min_warmup_days:
        raise ValueError(
            f"Insufficient data for backtesting. Found {n} days; minimum warmup requires {min_warmup_days + 5} days."
        )

    sim_records: List[DailySimRecord] = []
    signal_counts = {
        "Very cheap (extra ₹65)": 0,
        "Cheap (extra ₹40)": 0,
        "Normal (extra ₹25)": 0,
        "Expensive (extra ₹10)": 0,
        "Very expensive (extra ₹0)": 0
    }

    # Pass 1: Run Strategy A and Strategy B day by day
    for i in range(min_warmup_days, n):
        # Strict zero-lookahead slice: history up to yesterday
        hist_slice = prices[:i]
        curr_price = prices[i]
        curr_date = dates[i].isoformat()

        analysis = run_analysis(hist_slice, current_price=curr_price)
        report = evaluate_model(analysis, weights=weights, fixed_amount=35.0)

        extra = report.extra_amount
        cat = report.category
        if cat in ["Very cheap", "Cheap", "Normal", "Expensive", "Very expensive"]:
            key = f"{cat} (extra ₹{int(extra)})"
            signal_counts[key] = signal_counts.get(key, 0) + 1

        # Strategy A (Fixed ₹35)
        amt_a = 35.0
        net_a = amt_a / (1.0 + gst_rate)
        grams_a = net_a / curr_price

        # Strategy B (₹35 + extra)
        amt_b = 35.0 + extra
        net_b = amt_b / (1.0 + gst_rate)
        grams_b = net_b / curr_price

        sim_records.append(
            DailySimRecord(
                date=curr_date,
                price=round(curr_price, 2),
                score=report.total_score,
                category=cat,
                extra_amount=extra,
                strat_a_amount=amt_a,
                strat_a_grams=grams_a,
                strat_b_amount=amt_b,
                strat_b_grams=grams_b,
                scaled_amount=0.0,
                scaled_grams=0.0
            )
        )

    # Pass 2: Calculate Equal-Total-Spend Baseline
    sim_days = len(sim_records)
    total_invested_b = sum(r.strat_b_amount for r in sim_records)
    daily_scaled_amount = total_invested_b / sim_days if sim_days > 0 else 35.0

    for r in sim_records:
        r.scaled_amount = round(daily_scaled_amount, 2)
        net_s = daily_scaled_amount / (1.0 + gst_rate)
        r.scaled_grams = net_s / r.price

    # Compute aggregate metrics
    final_price = prices[-1]

    # Strat A
    total_inv_a = sum(r.strat_a_amount for r in sim_records)
    total_grams_a = sum(r.strat_a_grams for r in sim_records)
    avg_cost_a = total_inv_a / total_grams_a if total_grams_a > 0 else 0.0
    val_a = total_grams_a * final_price
    ret_a = ((val_a - total_inv_a) / total_inv_a * 100.0) if total_inv_a > 0 else 0.0

    # Strat B
    total_grams_b = sum(r.strat_b_grams for r in sim_records)
    avg_cost_b = total_invested_b / total_grams_b if total_grams_b > 0 else 0.0
    val_b = total_grams_b * final_price
    ret_b = ((val_b - total_invested_b) / total_invested_b * 100.0) if total_invested_b > 0 else 0.0

    # Scaled Baseline
    total_inv_scaled = sum(r.scaled_amount for r in sim_records)
    total_grams_scaled = sum(r.scaled_grams for r in sim_records)
    avg_cost_scaled = total_inv_scaled / total_grams_scaled if total_grams_scaled > 0 else 0.0
    val_scaled = total_grams_scaled * final_price
    ret_scaled = ((val_scaled - total_inv_scaled) / total_inv_scaled * 100.0) if total_inv_scaled > 0 else 0.0

    # Track portfolio trajectory for max drawdown
    cum_grams_a, cum_grams_b, cum_grams_s = 0.0, 0.0, 0.0
    vals_a, vals_b, vals_s = [], [], []
    for r in sim_records:
        cum_grams_a += r.strat_a_grams
        cum_grams_b += r.strat_b_grams
        cum_grams_s += r.scaled_grams
        vals_a.append(cum_grams_a * r.price)
        vals_b.append(cum_grams_b * r.price)
        vals_s.append(cum_grams_s * r.price)

    dd_a = compute_portfolio_drawdown(vals_a)
    dd_b = compute_portfolio_drawdown(vals_b)
    dd_s = compute_portfolio_drawdown(vals_s)

    # Cost improvement vs scaled baseline
    cost_diff = avg_cost_scaled - avg_cost_b
    cost_improv_pct = (cost_diff / avg_cost_scaled * 100.0) if avg_cost_scaled > 0 else 0.0
    model_lowered = cost_diff > 0.0

    warning = None
    if sim_days < 180:
        warning = f"Sample size is only {sim_days} days. Backtest results on short horizons are indicative only and do not guarantee future performance."

    return BacktestResult(
        days_tested=sim_days,
        start_date=sim_records[0].date,
        end_date=sim_records[-1].date,
        strategy_a=StrategyMetrics(
            name="Strategy A (₹35 Fixed)",
            total_invested=round(total_inv_a, 2),
            total_grams=round(total_grams_a, 4),
            avg_cost_per_gram=round(avg_cost_a, 2),
            final_value=round(val_a, 2),
            return_pct=round(ret_a, 2),
            max_drawdown_pct=dd_a
        ),
        strategy_b=StrategyMetrics(
            name="Strategy B (₹35 + Model Extra)",
            total_invested=round(total_invested_b, 2),
            total_grams=round(total_grams_b, 4),
            avg_cost_per_gram=round(avg_cost_b, 2),
            final_value=round(val_b, 2),
            return_pct=round(ret_b, 2),
            max_drawdown_pct=dd_b
        ),
        strategy_scaled=StrategyMetrics(
            name="Equal-Spend Baseline (Strategy A Scaled)",
            total_invested=round(total_inv_scaled, 2),
            total_grams=round(total_grams_scaled, 4),
            avg_cost_per_gram=round(avg_cost_scaled, 2),
            final_value=round(val_scaled, 2),
            return_pct=round(ret_scaled, 2),
            max_drawdown_pct=dd_s
        ),
        extra_money_deployed=round(total_invested_b - total_inv_a, 2),
        cost_difference_per_gram=round(cost_diff, 2),
        cost_improvement_pct=round(cost_improv_pct, 2),
        model_lowered_cost=model_lowered,
        signal_counts=signal_counts,
        daily_history=sim_records,
        sample_warning=warning
    )
