from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GoldPrice
from ..analysis.backtester import run_backtest
from ..analysis.weights import DEFAULT_WEIGHTS
from ..config import settings

router = APIRouter(prefix="/backtest", tags=["Backtest"])

@router.post("")
def execute_backtest(
    min_warmup: int = Query(30, ge=15, le=60),
    db: Session = Depends(get_db)
):
    records = db.query(GoldPrice).order_by(GoldPrice.date.asc()).all()
    if len(records) <= min_warmup + 5:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {min_warmup + 5} days of history for backtesting. Currently found {len(records)} days in database. Run sync first."
        )

    dates = [r.date for r in records]
    prices = [r.price_24k_inr for r in records]

    try:
        res = run_backtest(
            dates=dates,
            prices=prices,
            weights=DEFAULT_WEIGHTS,
            gst_rate=settings.GST_RATE,
            min_warmup_days=min_warmup
        )
        return {
            "days_tested": res.days_tested,
            "start_date": res.start_date,
            "end_date": res.end_date,
            "sample_warning": res.sample_warning,
            "disclaimer": res.disclaimer,
            "extra_money_deployed": res.extra_money_deployed,
            "cost_difference_per_gram": res.cost_difference_per_gram,
            "cost_improvement_pct": res.cost_improvement_pct,
            "model_lowered_cost": res.model_lowered_cost,
            "strategy_a": {
                "name": res.strategy_a.name,
                "total_invested": res.strategy_a.total_invested,
                "total_grams": res.strategy_a.total_grams,
                "avg_cost_per_gram": res.strategy_a.avg_cost_per_gram,
                "final_value": res.strategy_a.final_value,
                "return_pct": res.strategy_a.return_pct,
                "max_drawdown_pct": res.strategy_a.max_drawdown_pct
            },
            "strategy_b": {
                "name": res.strategy_b.name,
                "total_invested": res.strategy_b.total_invested,
                "total_grams": res.strategy_b.total_grams,
                "avg_cost_per_gram": res.strategy_b.avg_cost_per_gram,
                "final_value": res.strategy_b.final_value,
                "return_pct": res.strategy_b.return_pct,
                "max_drawdown_pct": res.strategy_b.max_drawdown_pct
            },
            "strategy_scaled": {
                "name": res.strategy_scaled.name,
                "total_invested": res.strategy_scaled.total_invested,
                "total_grams": res.strategy_scaled.total_grams,
                "avg_cost_per_gram": res.strategy_scaled.avg_cost_per_gram,
                "final_value": res.strategy_scaled.final_value,
                "return_pct": res.strategy_scaled.return_pct,
                "max_drawdown_pct": res.strategy_scaled.max_drawdown_pct
            },
            "signal_counts": res.signal_counts,
            "daily_history": [
                {
                    "date": r.date,
                    "price": r.price,
                    "score": r.score,
                    "category": r.category,
                    "extra_amount": r.extra_amount,
                    "strat_a_amount": r.strat_a_amount,
                    "strat_b_amount": r.strat_b_amount,
                    "scaled_amount": r.scaled_amount
                }
                for r in res.daily_history[-120:]  # Limit payload to last 120 simulation points for fast rendering
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
