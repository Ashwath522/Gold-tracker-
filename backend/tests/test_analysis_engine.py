import pytest
import numpy as np
from app.analysis.engine import (
    compute_window_metrics,
    compute_volatility,
    compute_momentum,
    run_analysis
)

def test_edge_case_high_equals_low():
    # Constant prices
    prices = np.array([7000.0] * 30)
    metrics = compute_window_metrics(prices, current_price=7000.0, window_days=30)
    assert metrics.high == 7000.0
    assert metrics.low == 7000.0
    assert metrics.average == 7000.0
    # Range position should be 50% without ZeroDivisionError
    assert metrics.range_position == 50.0
    assert metrics.percentile_rank == 100.0
    assert metrics.drawdown_pct == 0.0
    assert metrics.distance_from_sma_pct == 0.0

def test_window_metrics_exact_values():
    # Linear price increase: 7000, 7100, 7200, 7300, 7400
    prices = np.array([7000.0, 7100.0, 7200.0, 7300.0, 7400.0])
    current_price = 7200.0  # Median
    metrics = compute_window_metrics(prices, current_price=current_price, window_days=5)

    assert metrics.high == 7400.0
    assert metrics.low == 7000.0
    assert metrics.average == 7200.0
    # Range position: (7200 - 7000) / (7400 - 7000) = 200 / 400 = 50%
    assert metrics.range_position == 50.0
    # 7000, 7100, 7200 <= 7200 (3 out of 5) = 60%
    assert metrics.percentile_rank == 60.0
    # Drawdown from high: (7200 - 7400) / 7400 = -2.7%
    assert metrics.drawdown_pct == -2.7
    # Distance from SMA: (7200 - 7200) / 7200 = 0%
    assert metrics.distance_from_sma_pct == 0.0

def test_degraded_data_under_90_days():
    # Only 25 days of data
    prices = [7200.0 + i * 10.0 for i in range(25)]
    res = run_analysis(prices, current_price=7450.0)

    assert res.data_degraded is True
    assert "Only 25 days" in res.degraded_reason
    assert res.windows[30].is_partial is True
    assert res.windows[60].is_partial is True
    assert res.windows[90].is_partial is True
    assert res.windows[90].actual_days == 25

def test_volatility_labels():
    # Stable prices -> Low volatility
    stable_prices = np.array([7000.0 + (i % 2) * 5 for i in range(50)])
    vol_low = compute_volatility(stable_prices)
    assert vol_low.label == "Low"
    assert vol_low.annualized_volatility_pct < 12.0

    # Wild swings -> High volatility
    wild_prices = np.array([7000.0 * (1.10 if i % 2 == 0 else 0.90) for i in range(50)])
    vol_high = compute_volatility(wild_prices)
    assert vol_high.label == "High"
    assert vol_high.annualized_volatility_pct > 20.0

def test_momentum_roc_calculations():
    prices = np.array([7000.0] * 35)
    prices[-10] = 6800.0
    prices[-30] = 6500.0
    current_price = 7140.0

    mom = compute_momentum(prices, current_price)
    # 10d ROC: (7140 - 6800) / 6800 = 5.0%
    assert mom.roc_10d_pct == 5.0
    # 30d ROC: (7140 - 6500) / 6500 = 9.85%
    assert mom.roc_30d_pct == 9.85
    # 60d ROC should be None because len(prices) is 35
    assert mom.roc_60d_pct is None
