from datetime import datetime, timezone, timedelta, date
from typing import Optional, List
import zoneinfo
import asyncio
import concurrent.futures
from sqlalchemy.orm import Session
from ..config import settings
from ..models import GoldPrice, PriceCache
from ..schemas import LatestPriceResponse
from ..providers.base import GoldPriceProvider, ProviderPrice

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

def get_ist_now() -> datetime:
    return datetime.now(IST)

def compute_benchmark_status(dt_ist: Optional[datetime] = None) -> str:
    """
    11:30 AM IST handling: treat it as a benchmark/update reference only.
    Before 11:30 AM IST: 'Preliminary (latest available price)'
    After 11:30 AM IST: 'Updated (includes today's benchmark if available)'
    """
    if dt_ist is None:
        dt_ist = get_ist_now()
    
    if dt_ist.hour < 11 or (dt_ist.hour == 11 and dt_ist.minute < 30):
        return "Preliminary (latest available price)"
    else:
        return "Updated (includes today's benchmark if available)"

def _run_async(coro):
    """Safely run an async coroutine from synchronous code across Python 3.10-3.14."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)

class PriceService:
    def __init__(self, db: Session, provider: GoldPriceProvider):
        self.db = db
        self.provider = provider

    def get_latest_price(self, force_refresh: bool = False) -> LatestPriceResponse:
        """
        Fetches latest price using cache TTL (default 30 min).
        Only calls provider API when cache is older than TTL or missing.
        Never interpolates or fabricates data.
        If provider call fails, returns cached stale price with is_stale=True if available.
        """
        now_utc = datetime.now(timezone.utc)
        ist_now = get_ist_now()
        benchmark_status = compute_benchmark_status(ist_now)

        cache_entry = self.db.query(PriceCache).filter(PriceCache.cache_key == "latest").first()
        ttl_seconds = settings.CACHE_TTL_MINUTES * 60

        is_fresh = False
        if cache_entry and not force_refresh:
            fetched_at = cache_entry.fetched_at
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
            cache_age = (now_utc - fetched_at).total_seconds()
            if cache_age < ttl_seconds:
                is_fresh = True

        if is_fresh and cache_entry:
            return LatestPriceResponse(
                price_24k_inr=cache_entry.price_24k_inr,
                price_22k_inr=cache_entry.price_22k_inr,
                price_24k_10g_inr=round(cache_entry.price_24k_inr * 10, 2),
                price_22k_10g_inr=round(cache_entry.price_22k_inr * 10, 2) if cache_entry.price_22k_inr else None,
                source=cache_entry.source,
                source_timestamp=cache_entry.source_timestamp,
                is_converted=cache_entry.is_converted,
                fetched_at=cache_entry.fetched_at,
                benchmark_status=benchmark_status,
                is_stale=False,
                notes="Served from cache"
            )

        # Cache expired or absent: fetch from provider
        try:
            price_data: ProviderPrice = _run_async(self.provider.get_latest())
        except Exception as e:
            # If provider fails and we have a cached price, serve it with stale flag
            if cache_entry:
                return LatestPriceResponse(
                    price_24k_inr=cache_entry.price_24k_inr,
                    price_22k_inr=cache_entry.price_22k_inr,
                    price_24k_10g_inr=round(cache_entry.price_24k_inr * 10, 2),
                    price_22k_10g_inr=round(cache_entry.price_22k_inr * 10, 2) if cache_entry.price_22k_inr else None,
                    source=cache_entry.source,
                    source_timestamp=cache_entry.source_timestamp,
                    is_converted=cache_entry.is_converted,
                    fetched_at=cache_entry.fetched_at,
                    benchmark_status=benchmark_status,
                    is_stale=True,
                    notes=f"Stale data (provider failed: {str(e)})"
                )
            raise RuntimeError(f"Could not fetch latest gold price from provider: {e}")

        # Update cache in database
        if not cache_entry:
            cache_entry = PriceCache(
                cache_key="latest",
                price_24k_inr=price_data.price_24k_inr,
                price_22k_inr=price_data.price_22k_inr,
                source=price_data.source,
                source_timestamp=price_data.source_timestamp,
                is_converted=price_data.is_converted,
                fetched_at=now_utc,
                benchmark_status=benchmark_status,
                raw_payload=price_data.notes
            )
            self.db.add(cache_entry)
        else:
            cache_entry.price_24k_inr = price_data.price_24k_inr
            cache_entry.price_22k_inr = price_data.price_22k_inr
            cache_entry.source = price_data.source
            cache_entry.source_timestamp = price_data.source_timestamp
            cache_entry.is_converted = price_data.is_converted
            cache_entry.fetched_at = now_utc
            cache_entry.benchmark_status = benchmark_status
            cache_entry.raw_payload = price_data.notes

        # Also upsert into gold_prices daily records
        daily_record = self.db.query(GoldPrice).filter(GoldPrice.date == price_data.date).first()
        if not daily_record:
            daily_record = GoldPrice(
                date=price_data.date,
                price_24k_inr=price_data.price_24k_inr,
                price_22k_inr=price_data.price_22k_inr,
                source=price_data.source,
                source_timestamp=price_data.source_timestamp,
                is_converted=price_data.is_converted,
                notes=price_data.notes
            )
            self.db.add(daily_record)
        else:
            daily_record.price_24k_inr = price_data.price_24k_inr
            daily_record.price_22k_inr = price_data.price_22k_inr
            daily_record.source = price_data.source
            daily_record.source_timestamp = price_data.source_timestamp
            daily_record.is_converted = price_data.is_converted
            daily_record.notes = price_data.notes

        self.db.commit()

        return LatestPriceResponse(
            price_24k_inr=price_data.price_24k_inr,
            price_22k_inr=price_data.price_22k_inr,
            price_24k_10g_inr=round(price_data.price_24k_inr * 10, 2),
            price_22k_10g_inr=round(price_data.price_22k_inr * 10, 2) if price_data.price_22k_inr else None,
            source=price_data.source,
            source_timestamp=price_data.source_timestamp,
            is_converted=price_data.is_converted,
            fetched_at=now_utc,
            benchmark_status=benchmark_status,
            is_stale=False,
            notes=price_data.notes
        )

    def get_history_from_db(self, days: int = 90) -> List[GoldPrice]:
        """
        Fetch historical records stored in the DB, ordered chronologically ascending.
        """
        cutoff_date = get_ist_now().date() - timedelta(days=days)
        records = (
            self.db.query(GoldPrice)
            .filter(GoldPrice.date >= cutoff_date)
            .order_by(GoldPrice.date.asc())
            .all()
        )
        return records

    def sync_history(self, days: int = 365) -> int:
        """
        Fetches historical days from the provider and saves only missing days into DB.
        Returns the number of new records inserted.
        """
        history_data: List[ProviderPrice] = _run_async(self.provider.get_history(days))

        inserted_count = 0
        for item in history_data:
            existing = self.db.query(GoldPrice).filter(GoldPrice.date == item.date).first()
            if not existing:
                rec = GoldPrice(
                    date=item.date,
                    price_24k_inr=item.price_24k_inr,
                    price_22k_inr=item.price_22k_inr,
                    source=item.source,
                    source_timestamp=item.source_timestamp,
                    is_converted=item.is_converted,
                    notes=item.notes
                )
                self.db.add(rec)
                inserted_count += 1
            else:
                existing.price_24k_inr = item.price_24k_inr
                existing.price_22k_inr = item.price_22k_inr
                existing.source = item.source
                existing.source_timestamp = item.source_timestamp
                existing.is_converted = item.is_converted
                existing.notes = item.notes

        self.db.commit()
        return inserted_count
