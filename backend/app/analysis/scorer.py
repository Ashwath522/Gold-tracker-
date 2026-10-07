from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from .engine import AnalysisResult
from .weights import ScoreWeights, DEFAULT_WEIGHTS, RECOMMENDATION_TIERS, RecommendationTier

@dataclass
class SubScoreDetail:
    name: str
    weight: float
    raw_score: float  # 0 to 100
    weighted_score: float  # (raw_score * weight) / total_weight
    description: str

@dataclass
class ScoreReport:
    total_score: float  # 0 to 100
    sub_scores: Dict[str, SubScoreDetail]
    category: str  # "Very expensive", "Expensive", "Normal", "Cheap", "Very cheap"
    is_cheap: str  # "YES", "NO", "NORMAL"
    fixed_amount: float
    extra_amount: float
    total_amount: float
    why_explanation: str
    disclaimer: str

DISCLAIMER_TEXT = "Disclaimer: Current price appears relatively cheap/expensive based on recent history only. Relatively cheap prices can get cheaper; this is not a price predictor or financial advice."

def compute_sub_scores(analysis: AnalysisResult, weights: ScoreWeights) -> Dict[str, SubScoreDetail]:
    """
    Computes transparent 0–100 sub-scores for each factor.
    Higher score = cheaper = more attractive for extra accumulation.
    """
    total_w = weights.total_weight
    sub_scores: Dict[str, SubScoreDetail] = {}

    # 1. Price vs 90D range (weight: 25)
    # Range position: 0% = at low (score 100), 100% = at high (score 0)
    w90 = analysis.windows.get(90) or analysis.windows.get(30)
    rp_90 = w90.range_position if w90 else 50.0
    raw_range_90 = float(np.clip(100.0 - rp_90, 0.0, 100.0))
    sub_scores["price_vs_90d_range"] = SubScoreDetail(
        name="Price vs 90D Range",
        weight=weights.price_vs_90d_range,
        raw_score=round(raw_range_90, 1),
        weighted_score=round((raw_range_90 * weights.price_vs_90d_range) / total_w, 2),
        description=f"At {rp_90:.1f}% of the 90-day price range ({'near lows' if rp_90 < 35 else 'near highs' if rp_90 > 65 else 'mid-range'})"
    )

    # 2. Price vs Moving Averages (30/60/90) (weight: 20)
    # Below SMA = cheaper = higher score. Above SMA = lower score.
    # 5% below average maps to ~100; 5% above average maps to ~0.
    distances = [
        analysis.windows[w].distance_from_sma_pct
        for w in [30, 60, 90]
        if w in analysis.windows and not analysis.windows[w].is_partial or analysis.windows[w].actual_days > 0
    ]
    avg_dist = float(np.mean(distances)) if distances else 0.0
    raw_sma = float(np.clip(50.0 - (avg_dist * 10.0), 0.0, 100.0))
    sub_scores["price_vs_moving_averages"] = SubScoreDetail(
        name="Price vs Moving Averages",
        weight=weights.price_vs_moving_averages,
        raw_score=round(raw_sma, 1),
        weighted_score=round((raw_sma * weights.price_vs_moving_averages) / total_w, 2),
        description=f"Trading {abs(avg_dist):.1f}% {'below' if avg_dist < 0 else 'above'} 30/60/90-day moving averages"
    )

    # 3. Momentum 30/60/90 (weight: 15)
    # Must NOT reward rising prices! Sharp spikes score lower; sharp drops stabilizing score higher.
    rocs = [
        val for val in [
            analysis.momentum.roc_30d_pct,
            analysis.momentum.roc_60d_pct,
            analysis.momentum.roc_90d_pct
        ] if val is not None
    ]
    avg_roc = float(np.mean(rocs)) if rocs else (analysis.momentum.roc_10d_pct or 0.0)
    raw_momentum = float(np.clip(50.0 - (avg_roc * 5.0), 0.0, 100.0))
    sub_scores["momentum_30_60_90"] = SubScoreDetail(
        name="Momentum (Anti-Spike)",
        weight=weights.momentum_30_60_90,
        raw_score=round(raw_momentum, 1),
        weighted_score=round((raw_momentum * weights.momentum_30_60_90) / total_w, 2),
        description=f"Average rate of change is {avg_roc:+.1f}% ({'pulling back / cool' if avg_roc <= 0 else 'rallying / heated'})"
    )

    # 4. Recent Drawdown from 90D High (weight: 15)
    # Drawdown is <= 0. Deep drawdown = bigger discount = higher score.
    dd = w90.drawdown_pct if w90 else 0.0
    abs_dd = abs(min(0.0, dd))
    raw_dd = float(np.clip(abs_dd * 10.0, 0.0, 100.0))
    sub_scores["recent_drawdown"] = SubScoreDetail(
        name="Recent Drawdown",
        weight=weights.recent_drawdown,
        raw_score=round(raw_dd, 1),
        weighted_score=round((raw_dd * weights.recent_drawdown) / total_w, 2),
        description=f"{abs_dd:.1f}% discount from recent 90-day high"
    )

    # 5. Relative Lows (Range Position + Percentile across windows) (weight: 15)
    # Lower percentile = cheaper compared to history
    percentiles = [
        analysis.windows[w].percentile_rank
        for w in [30, 60, 90]
        if w in analysis.windows and analysis.windows[w].actual_days > 0
    ]
    avg_pctl = float(np.mean(percentiles)) if percentiles else 50.0
    raw_rel_lows = float(np.clip(100.0 - avg_pctl, 0.0, 100.0))
    sub_scores["relative_lows"] = SubScoreDetail(
        name="Relative Lows (Percentile)",
        weight=weights.relative_lows,
        raw_score=round(raw_rel_lows, 1),
        weighted_score=round((raw_rel_lows * weights.relative_lows) / total_w, 2),
        description=f"Price is lower than {100.0 - avg_pctl:.1f}% of historical daily closes across windows"
    )

    # 6. Volatility / Risk (weight: 10)
    # Calm / normal volatility encourages regular accumulation
    ann_vol = analysis.volatility.annualized_volatility_pct
    if analysis.volatility.label == "Low":
        raw_vol = 95.0
    elif analysis.volatility.label == "Medium":
        raw_vol = 75.0
    else:
        raw_vol = 40.0
    sub_scores["volatility_risk"] = SubScoreDetail(
        name="Volatility / Risk",
        weight=weights.volatility_risk,
        raw_score=round(raw_vol, 1),
        weighted_score=round((raw_vol * weights.volatility_risk) / total_w, 2),
        description=f"{analysis.volatility.label} volatility ({ann_vol:.1f}% annualized)"
    )

    return sub_scores

def match_tier(score: float, fixed_amount: float = 35.0) -> RecommendationTier:
    """
    Finds the tier for a score. Boundaries are half-open (a tier runs up to the
    next tier's min_score), so fractional scores such as 30.5 never fall in a gap.
    """
    clamped_score = float(np.clip(score, 0.0, 100.0))
    for i, tier in enumerate(RECOMMENDATION_TIERS):
        is_last = i == len(RECOMMENDATION_TIERS) - 1
        upper = float("inf") if is_last else RECOMMENDATION_TIERS[i + 1].min_score
        if clamped_score < upper:
            return tier
    return RECOMMENDATION_TIERS[-1]

def generate_why_sentence(
    score: float,
    tier: RecommendationTier,
    analysis: AnalysisResult,
    sub_scores: Dict[str, SubScoreDetail]
) -> str:
    """
    Generates an honest, plain-language 'Why?' sentence derived from actual sub-scores.
    Strictly follows spec:
    - Never says 'gold will rise'.
    - Formatted as: 'Current price appears relatively cheap/expensive compared with its recent history, so the model recommends X'.
    """
    w90 = analysis.windows.get(90) or analysis.windows.get(30)
    rp = w90.range_position if w90 else 50.0
    avg_dist = analysis.windows[30].distance_from_sma_pct if 30 in analysis.windows else 0.0

    position_text = (
        f"in the lower {rp:.0f}% of its 90-day range"
        if rp < 50
        else f"in the upper {rp:.0f}% of its 90-day range"
    )
    sma_text = (
        f"{abs(avg_dist):.1f}% below its 30-day average"
        if avg_dist < 0
        else f"{avg_dist:.1f}% above its 30-day average"
    )

    sentiment = "relatively cheap" if score >= 61 else "relatively expensive" if score <= 45 else "at a neutral valuation"
    action = f"an extra ₹{int(tier.extra_amount)} accumulation (total ₹{int(tier.total_amount)})" if tier.extra_amount > 0 else f"fixed ₹{int(tier.fixed_amount)} only"

    return (
        f"Current price appears {sentiment} compared with its recent history "
        f"({position_text} and {sma_text}), so the model recommends {action}."
    )

def evaluate_model(
    analysis: AnalysisResult,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    fixed_amount: float = 35.0
) -> ScoreReport:
    """
    Computes composite score (0-100), maps recommendation, and generates plain-language explanation.
    """
    sub_scores = compute_sub_scores(analysis, weights)
    total_score = sum(s.weighted_score for s in sub_scores.values())
    total_score = float(np.clip(total_score, 0.0, 100.0))

    tier = match_tier(total_score, fixed_amount=fixed_amount)
    why_text = generate_why_sentence(total_score, tier, analysis, sub_scores)

    return ScoreReport(
        total_score=round(total_score, 1),
        sub_scores=sub_scores,
        category=tier.label,
        is_cheap=tier.is_cheap_label,
        fixed_amount=fixed_amount,
        extra_amount=tier.extra_amount,
        total_amount=fixed_amount + tier.extra_amount,
        why_explanation=why_text,
        disclaimer=DISCLAIMER_TEXT
    )
