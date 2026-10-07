from datetime import date as dt_date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class GoldPriceItem(BaseModel):
    date: dt_date
    price_24k_inr: float
    price_22k_inr: Optional[float] = None
    source: str
    source_timestamp: str
    is_converted: bool = False
    notes: Optional[str] = None

class LatestPriceResponse(BaseModel):
    price_24k_inr: float
    price_22k_inr: Optional[float] = None
    price_24k_10g_inr: float
    price_22k_10g_inr: Optional[float] = None
    source: str
    source_timestamp: str
    is_converted: bool = False
    fetched_at: datetime
    benchmark_status: str
    is_stale: bool = False
    notes: Optional[str] = None

class InvestmentCreate(BaseModel):
    date: dt_date
    time_ist: str
    market_price: float
    model_score: Optional[float] = None
    model_rec_fixed: float = 35.0
    model_rec_extra: float = 0.0
    model_rec_total: float = 35.0
    actual_amount: float
    gst_paid: Optional[float] = None
    actual_grams: Optional[float] = None  # If omitted, calculated using market_price and GST
    notes: Optional[str] = None

class InvestmentUpdate(BaseModel):
    date: Optional[dt_date] = None
    time_ist: Optional[str] = None
    market_price: Optional[float] = None
    model_score: Optional[float] = None
    model_rec_fixed: Optional[float] = None
    model_rec_extra: Optional[float] = None
    model_rec_total: Optional[float] = None
    actual_amount: Optional[float] = None
    gst_paid: Optional[float] = None
    actual_grams: Optional[float] = None
    notes: Optional[str] = None

class InvestmentOut(BaseModel):
    id: int
    date: dt_date
    time_ist: str
    market_price: float
    model_score: Optional[float] = None
    model_rec_fixed: float
    model_rec_extra: float
    model_rec_total: float
    actual_amount: float
    gst_paid: Optional[float] = None
    actual_grams: float
    is_estimated_grams: bool
    avg_purchase_price: float
    notes: Optional[str] = None

class PortfolioSummary(BaseModel):
    total_invested: float
    total_grams: float
    current_market_price: float
    current_nominal_value: float
    estimated_net_selling_value: float
    sell_spread_pct: float
    unrealized_pnl: float
    return_pct: float
    avg_purchase_price: float
    investment_days: int
    avg_daily_investment: float
    total_fixed_amount: float
    total_extra_amount: float
    followed_rec_days: int
    diverged_rec_days: int
