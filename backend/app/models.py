from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Date, Text, Index
from .database import Base

def utc_now():
    return datetime.now(timezone.utc)

class GoldPrice(Base):
    """
    Stores historical and daily settlement/closing gold prices in INR per gram.
    Schema designed to be PostgreSQL/Supabase compatible.
    """
    __tablename__ = "gold_prices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    price_24k_inr = Column(Float, nullable=False)
    price_22k_inr = Column(Float, nullable=True)
    source = Column(String(100), nullable=False)
    source_timestamp = Column(String(60), nullable=False)
    is_converted = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "price_24k_inr": self.price_24k_inr,
            "price_22k_inr": self.price_22k_inr,
            "source": self.source,
            "source_timestamp": self.source_timestamp,
            "is_converted": self.is_converted,
            "notes": self.notes,
        }

class PriceCache(Base):
    """
    Stores latest fetched live gold price with TTL and benchmark update state.
    """
    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(50), unique=True, index=True, default="latest")
    price_24k_inr = Column(Float, nullable=False)
    price_22k_inr = Column(Float, nullable=True)
    source = Column(String(100), nullable=False)
    source_timestamp = Column(String(60), nullable=False)
    is_converted = Column(Boolean, default=False, nullable=False)
    fetched_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    benchmark_status = Column(String(100), nullable=False)
    raw_payload = Column(Text, nullable=True)

class Investment(Base):
    """
    User's real investments log (e.g. via PhonePe).
    Stores real amount, actual grams received, and calculated real cost per gram.
    """
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    time_ist = Column(String(20), nullable=False)
    market_price = Column(Float, nullable=False)  # Market price at time of purchase
    model_score = Column(Float, nullable=True)
    model_rec_fixed = Column(Float, default=35.0, nullable=False)
    model_rec_extra = Column(Float, default=0.0, nullable=False)
    model_rec_total = Column(Float, default=35.0, nullable=False)
    actual_amount = Column(Float, nullable=False)
    gst_paid = Column(Float, nullable=True)
    actual_grams = Column(Float, nullable=False)
    is_estimated_grams = Column(Boolean, default=False, nullable=False)
    avg_purchase_price = Column(Float, nullable=False)  # actual_amount / actual_grams
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "time_ist": self.time_ist,
            "market_price": self.market_price,
            "model_score": self.model_score,
            "model_rec_fixed": self.model_rec_fixed,
            "model_rec_extra": self.model_rec_extra,
            "model_rec_total": self.model_rec_total,
            "actual_amount": self.actual_amount,
            "gst_paid": self.gst_paid,
            "actual_grams": round(self.actual_grams, 4),
            "is_estimated_grams": self.is_estimated_grams,
            "avg_purchase_price": round(self.avg_purchase_price, 2),
            "notes": self.notes,
        }
