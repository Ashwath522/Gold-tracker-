from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..providers.factory import get_gold_provider
from ..services.price_service import PriceService
from ..models import GoldPrice
from ..analysis.engine import run_analysis
from ..analysis.scorer import evaluate_model
from ..analysis.weights import DEFAULT_WEIGHTS

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.get("")
def get_daily_analysis(
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Computes 30/60/90D technical ranges, anti-spike momentum, volatility,
    0-100 score, tier recommendation, and honest plain-language explanation.
    """
    try:
        provider = get_gold_provider()
        service = PriceService(db=db, provider=provider)
        latest = service.get_latest_price(force_refresh=force_refresh)

        # Get historical prices from database
        history_records = service.get_history_from_db(days=120)
        
        # If DB history has fewer than 10 days, attempt auto-sync
        if len(history_records) < 10:
            service.sync_history(days=120)
            history_records = service.get_history_from_db(days=120)

        price_series = [r.price_24k_inr for r in history_records]

        # If today is not in history yet, append or evaluate
        analysis = run_analysis(
            historical_prices=price_series if price_series else [latest.price_24k_inr],
            current_price=latest.price_24k_inr
        )
        report = evaluate_model(analysis, weights=DEFAULT_WEIGHTS, fixed_amount=35.0)

        return {
            "latest_price": latest.model_dump(),
            "analysis": {
                "current_price": analysis.current_price,
                "total_data_points": analysis.total_data_points,
                "data_degraded": analysis.data_degraded,
                "degraded_reason": analysis.degraded_reason,
                "volatility": {
                    "daily_std_dev": analysis.volatility.daily_std_dev,
                    "annualized_volatility_pct": analysis.volatility.annualized_volatility_pct,
                    "label": analysis.volatility.label
                },
                "momentum": {
                    "roc_10d_pct": analysis.momentum.roc_10d_pct,
                    "roc_30d_pct": analysis.momentum.roc_30d_pct,
                    "roc_60d_pct": analysis.momentum.roc_60d_pct,
                    "roc_90d_pct": analysis.momentum.roc_90d_pct
                },
                "windows": {
                    str(w): {
                        "window_days": m.window_days,
                        "actual_days": m.actual_days,
                        "high": m.high,
                        "low": m.low,
                        "average": m.average,
                        "pct_change": m.pct_change,
                        "range_position": m.range_position,
                        "percentile_rank": m.percentile_rank,
                        "drawdown_pct": m.drawdown_pct,
                        "distance_from_sma_pct": m.distance_from_sma_pct,
                        "is_partial": m.is_partial
                    }
                    for w, m in analysis.windows.items()
                }
            },
            "score_report": {
                "total_score": report.total_score,
                "category": report.category,
                "is_cheap": report.is_cheap,
                "fixed_amount": report.fixed_amount,
                "extra_amount": report.extra_amount,
                "total_amount": report.total_amount,
                "why_explanation": report.why_explanation,
                "disclaimer": report.disclaimer,
                "sub_scores": {
                    k: {
                        "name": v.name,
                        "weight": v.weight,
                        "raw_score": v.raw_score,
                        "weighted_score": v.weighted_score,
                        "description": v.description
                    }
                    for k, v in report.sub_scores.items()
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
