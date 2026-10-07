from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

@dataclass
class WindowMetrics:
    window_days: int
    actual_days: int
    high: float
    low: float
    average: float  # Simple Moving Average
    pct_change: float
    range_position: float  # 0 to 100%
    percentile_rank: float  # 0 to 100%
    drawdown_pct: float  # % below window high (negative or 0)
    distance_from_sma_pct: float  # % above or below SMA
    is_partial: bool = False

@dataclass
class VolatilityMetrics:
    daily_std_dev: float
    annualized_volatility_pct: float
    label: str  # "Low", "Medium", "High"

@dataclass
class MomentumMetrics:
    roc_10d_pct: Optional[float]
    roc_30d_pct: Optional[float]
    roc_60d_pct: Optional[float]
    roc_90d_pct: Optional[float]

@dataclass
class AnalysisResult:
    current_price: float
    windows: Dict[int, WindowMetrics]
    volatility: VolatilityMetrics
    momentum: MomentumMetrics
    total_data_points: int
    data_degraded: bool
    degraded_reason: Optional[str] = None

def compute_window_metrics(
    prices: np.ndarray,
    current_price: float,
    window_days: int
) -> WindowMetrics:
    """
    Pure function computing metrics for a given historical price window.
    Handles edge cases: high == low, fewer available data points than window size.
    """
    actual_len = len(prices)
    if actual_len == 0:
        return WindowMetrics(
            window_days=window_days,
            actual_days=0,
            high=current_price,
            low=current_price,
            average=current_price,
            pct_change=0.0,
            range_position=50.0,
            percentile_rank=50.0,
            drawdown_pct=0.0,
            distance_from_sma_pct=0.0,
            is_partial=True
        )

    w_prices = prices[-window_days:]
    actual_days = len(w_prices)
    is_partial = actual_days < window_days

    high_val = float(np.max(w_prices))
    low_val = float(np.min(w_prices))
    avg_val = float(np.mean(w_prices))
    start_val = float(w_prices[0])

    # Percentage change across the window
    pct_change = ((current_price - start_val) / start_val) * 100.0 if start_val > 0 else 0.0

    # Range position: (current - low) / (high - low) * 100
    # Edge case: high == low (e.g. constant prices or single data point)
    if high_val == low_val:
        range_pos = 50.0
    else:
        raw_pos = ((current_price - low_val) / (high_val - low_val)) * 100.0
        range_pos = float(np.clip(raw_pos, 0.0, 100.0))

    # Percentile rank: % of window observations <= current_price
    percentile_rank = float((np.sum(w_prices <= current_price) / actual_days) * 100.0)

    # Drawdown from window high
    if high_val > 0:
        drawdown_pct = ((current_price - high_val) / high_val) * 100.0
    else:
        drawdown_pct = 0.0

    # Distance from SMA
    if avg_val > 0:
        dist_sma = ((current_price - avg_val) / avg_val) * 100.0
    else:
        dist_sma = 0.0

    return WindowMetrics(
        window_days=window_days,
        actual_days=actual_days,
        high=round(high_val, 2),
        low=round(low_val, 2),
        average=round(avg_val, 2),
        pct_change=round(pct_change, 2),
        range_position=round(range_pos, 2),
        percentile_rank=round(percentile_rank, 2),
        drawdown_pct=round(drawdown_pct, 2),
        distance_from_sma_pct=round(dist_sma, 2),
        is_partial=is_partial
    )

def compute_volatility(prices: np.ndarray) -> VolatilityMetrics:
    """
    Computes daily returns standard deviation and annualized volatility.
    Categorizes into Low / Medium / High based on historical thresholds.
    """
    if len(prices) < 2:
        return VolatilityMetrics(daily_std_dev=0.0, annualized_volatility_pct=0.0, label="Low")

    # Percentage returns: (P_t - P_{t-1}) / P_{t-1}
    returns = np.diff(prices) / prices[:-1]
    daily_std = float(np.std(returns))
    # Annualized volatility: daily_std * sqrt(252 trading days) * 100
    ann_vol = daily_std * np.sqrt(252) * 100.0

    if ann_vol < 12.0:
        label = "Low"
    elif ann_vol <= 20.0:
        label = "Medium"
    else:
        label = "High"

    return VolatilityMetrics(
        daily_std_dev=round(daily_std, 4),
        annualized_volatility_pct=round(ann_vol, 2),
        label=label
    )

def compute_momentum(prices: np.ndarray, current_price: float) -> MomentumMetrics:
    """
    Computes Rate of Change (ROC) momentum for 10, 30, 60, and 90 days.
    ROC = ((Current - Past) / Past) * 100
    """
    n = len(prices)
    def roc_for_lag(lag: int) -> Optional[float]:
        if n >= lag and prices[-lag] > 0:
            return round(float(((current_price - prices[-lag]) / prices[-lag]) * 100.0), 2)
        return None

    return MomentumMetrics(
        roc_10d_pct=roc_for_lag(10),
        roc_30d_pct=roc_for_lag(30),
        roc_60d_pct=roc_for_lag(60),
        roc_90d_pct=roc_for_lag(90)
    )

def run_analysis(
    historical_prices: List[float],
    current_price: float
) -> AnalysisResult:
    """
    Main analysis engine function.
    Accepts chronological list of historical prices (24k INR/g) and current price.
    Returns complete window metrics (30/60/90D), momentum, and volatility.
    """
    arr = np.array(historical_prices, dtype=float)
    total_points = len(arr)

    data_degraded = False
    degraded_reason = None
    if total_points < 90:
        data_degraded = True
        degraded_reason = f"Only {total_points} days of historical data available. 90-day window metrics degraded gracefully."

    windows = {
        30: compute_window_metrics(arr, current_price, 30),
        60: compute_window_metrics(arr, current_price, 60),
        90: compute_window_metrics(arr, current_price, 90),
    }

    volatility = compute_volatility(arr[-90:] if total_points >= 90 else arr)
    momentum = compute_momentum(arr, current_price)

    return AnalysisResult(
        current_price=round(current_price, 2),
        windows=windows,
        volatility=volatility,
        momentum=momentum,
        total_data_points=total_points,
        data_degraded=data_degraded,
        degraded_reason=degraded_reason
    )
