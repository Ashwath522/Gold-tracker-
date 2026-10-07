import pytest
from datetime import date, timedelta
from app.analysis.backtester import run_backtest, compute_portfolio_drawdown

def test_portfolio_drawdown_calculation():
    # Value goes: 100 -> 120 -> 90 -> 110. Peak is 120, trough is 90. Drawdown = (90-120)/120 = -25.0%
    values = [100.0, 120.0, 90.0, 110.0]
    dd = compute_portfolio_drawdown(values)
    assert dd == -25.0

def test_backtest_equal_total_spend_baseline():
    # Generate 80 days of prices
    base_date = date(2026, 1, 1)
    dates = [base_date + timedelta(days=i) for i in range(80)]
    # Sinusoidal price cycle around 7500
    import math
    prices = [7500.0 + math.sin(i / 5.0) * 300.0 for i in range(80)]

    result = run_backtest(dates, prices, min_warmup_days=30)

    assert result.days_tested == 50  # 80 - 30 warmup
    assert result.strategy_a.total_invested == 50 * 35.0  # Exactly 1750

    # Total spend of Strategy B and Strategy Scaled must match exactly!
    b_spend = result.strategy_b.total_invested
    s_spend = result.strategy_scaled.total_invested
    assert abs(b_spend - s_spend) <= 1.0  # within rounding

    # Extra money deployed must match
    assert result.extra_money_deployed == round(b_spend - (50 * 35.0), 2)
    assert result.strategy_b.total_grams > 0
    assert result.strategy_a.total_grams > 0

    # Signals must sum to 50
    total_signals = sum(result.signal_counts.values())
    assert total_signals == 50

def test_backtest_insufficient_data_error():
    base_date = date(2026, 1, 1)
    dates = [base_date + timedelta(days=i) for i in range(25)]
    prices = [7500.0] * 25
    with pytest.raises(ValueError, match="Insufficient data"):
        run_backtest(dates, prices, min_warmup_days=30)
