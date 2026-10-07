import pytest
import numpy as np
from app.analysis.engine import run_analysis
from app.analysis.scorer import evaluate_model, match_tier, ScoreWeights

def test_fixed_35_is_never_removed():
    # Regardless of score from 0 to 100, fixed amount must always be 35
    for s in [0, 15, 30, 45, 55, 75, 95, 100]:
        tier = match_tier(s, fixed_amount=35.0)
        assert tier.fixed_amount == 35.0
        assert tier.total_amount >= 35.0

def test_cheap_price_scores_high_recommendation():
    # Price dropped to bottom of 90-day range
    history = [7500.0 + i * 10 for i in range(90)]  # 7500 up to 8390
    current_dip_price = 7400.0  # Below 90-day low!
    analysis = run_analysis(history, current_price=current_dip_price)
    report = evaluate_model(analysis)

    assert report.total_score >= 70.0
    assert report.is_cheap == "YES"
    assert report.extra_amount >= 40.0
    assert report.total_amount >= 75.0
    assert "Current price appears relatively cheap compared with its recent history" in report.why_explanation
    assert "gold will rise" not in report.why_explanation.lower()

def test_expensive_spike_scores_low_recommendation():
    # Price spiked to all-time 90-day high
    history = [7000.0 + i * 5 for i in range(90)]
    current_spike_price = 7800.0  # High spike above range
    analysis = run_analysis(history, current_price=current_spike_price)
    report = evaluate_model(analysis)

    assert report.total_score <= 40.0
    assert report.is_cheap == "NO"
    assert report.extra_amount <= 10.0
    assert report.total_amount <= 45.0
    assert "relatively expensive" in report.why_explanation
    assert "gold will rise" not in report.why_explanation.lower()

def test_momentum_does_not_reward_rising_prices():
    # Compare two situations with identical range position, but one has a sharp upward spike
    # Case A: Cool / declining prices
    history_cool = [7500.0] * 60 + [7400.0] * 30
    analysis_cool = run_analysis(history_cool, current_price=7350.0)
    report_cool = evaluate_model(analysis_cool)

    # Case B: Sharp upward rally
    history_rally = [7000.0] * 60 + [7500.0] * 30
    analysis_rally = run_analysis(history_rally, current_price=7600.0)
    report_rally = evaluate_model(analysis_rally)

    # Cool/pulling-back momentum sub-score must be higher than rallying spike
    cool_mom = report_cool.sub_scores["momentum_30_60_90"].raw_score
    rally_mom = report_rally.sub_scores["momentum_30_60_90"].raw_score
    assert cool_mom > rally_mom

def test_tier_mapping_boundaries():
    t_very_exp = match_tier(25.0)
    assert t_very_exp.label == "Very expensive"
    assert t_very_exp.extra_amount == 0.0

    t_exp = match_tier(35.0)
    assert t_exp.label == "Expensive"
    assert t_exp.extra_amount == 10.0

    t_norm = match_tier(50.0)
    assert t_norm.label == "Normal"
    assert t_norm.extra_amount == 25.0

    t_cheap = match_tier(70.0)
    assert t_cheap.label == "Cheap"
    assert t_cheap.extra_amount == 40.0

    t_very_cheap = match_tier(90.0)
    assert t_very_cheap.label == "Very cheap"
    assert t_very_cheap.extra_amount == 65.0
