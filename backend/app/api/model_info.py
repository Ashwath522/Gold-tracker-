from fastapi import APIRouter
from ..analysis.weights import DEFAULT_WEIGHTS, RECOMMENDATION_TIERS

router = APIRouter(prefix="/model", tags=["Model Explanation"])

@router.get("/explanation")
def get_model_explanation():
    return {
        "title": "Gold Daily Accumulation Valuation Model",
        "philosophy": (
            "The model accumulates more gold when the price is relatively LOW compared to recent history. "
            "It NEVER invests more simply because the price is rising. "
            "This is NOT a trading bot, NOT a price forecaster, and never attempts to predict market direction. "
            "The fixed daily investment of ₹35 is ALWAYS preserved regardless of market conditions."
        ),
        "weights": [
            {
                "factor": "Price vs 90D Range",
                "weight": DEFAULT_WEIGHTS.price_vs_90d_range,
                "description": "Compares current price to the 90-day high/low range. Near 90-day low scores near 100 points; near 90-day high scores near 0 points."
            },
            {
                "factor": "Price vs Moving Averages (30/60/90D)",
                "weight": DEFAULT_WEIGHTS.price_vs_moving_averages,
                "description": "Measures mean distance from 30, 60, and 90-day simple moving averages. Prices below the averages receive higher points; prices far above averages receive lower points."
            },
            {
                "factor": "Anti-Spike Momentum (30/60/90D ROC)",
                "weight": DEFAULT_WEIGHTS.momentum_30_60_90,
                "description": "Rate of change. Sharp rallies/spikes are explicitly penalized with lower points. Pullbacks stabilizing after a drop receive higher points."
            },
            {
                "factor": "Recent Drawdown from 90D High",
                "weight": DEFAULT_WEIGHTS.recent_drawdown,
                "description": "Calculates percentage discount from the 90-day peak. Deeper pullbacks offer higher margin of safety and higher score."
            },
            {
                "factor": "Relative Lows (Percentile Rank)",
                "weight": DEFAULT_WEIGHTS.relative_lows,
                "description": "Percentage of historical trading days in the window that closed above current price. More days above current price = higher percentile score."
            },
            {
                "factor": "Volatility / Risk",
                "weight": DEFAULT_WEIGHTS.volatility_risk,
                "description": "Annualized standard deviation of daily returns. Calm, orderly price action scores higher for systematic accumulation."
            }
        ],
        "recommendation_tiers": [
            {
                "score_range": f"{t.min_score:.0f} - {t.max_score:.0f}",
                "category": t.label,
                "is_cheap": t.is_cheap_label,
                "fixed_amount": t.fixed_amount,
                "extra_amount": t.extra_amount,
                "total_amount": t.total_amount
            }
            for t in RECOMMENDATION_TIERS
        ],
        "disclaimer": "Current price appears relatively cheap/expensive compared with its recent history only. Relatively cheap prices can get cheaper; past performance does not guarantee future results."
    }
