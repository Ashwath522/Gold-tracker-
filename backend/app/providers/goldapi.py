import httpx
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional
import zoneinfo
from .base import GoldPriceProvider, ProviderPrice

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

class GoldAPIProvider(GoldPriceProvider):
    """
    Provider implementation for GoldAPI.io.
    Provides 24k and 22k gold prices directly in INR per gram.
    Free tier allows 100 calls/month.
    """
    BASE_URL = "https://www.goldapi.io/api"

    def __init__(self, api_key: str):
        self.api_key = api_key.strip() if api_key else ""

    async def get_latest(self) -> ProviderPrice:
        if not self.api_key:
            raise ValueError(
                "GoldAPI.io key is not configured. Please set GOLDAPI_KEY in your .env file."
            )

        headers = {
            "x-access-token": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "GoldDailyAnalysis/1.0"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.BASE_URL}/XAU/INR", headers=headers)
            
            if resp.status_code == 401 or resp.status_code == 403:
                raise ValueError("GoldAPI.io authentication failed: Invalid or expired API Key.")
            if resp.status_code == 429:
                raise ValueError("GoldAPI.io rate limit exceeded (100 requests/month quota reached).")
            if resp.status_code != 200:
                raise RuntimeError(f"GoldAPI.io request failed with status {resp.status_code}: {resp.text}")

            data = resp.json()

        # Extract 24k and 22k prices per gram
        price_24k = data.get("price_gram_24k")
        if price_24k is None:
            # Fallback to total price / 31.1034768 if price_gram_24k is missing
            raw_price = data.get("price")
            if raw_price is not None:
                price_24k = raw_price / 31.1034768
            else:
                raise ValueError("GoldAPI.io response did not contain valid 24k price.")

        price_22k = data.get("price_gram_22k")
        raw_ts = data.get("timestamp")
        if raw_ts:
            dt_ist = datetime.fromtimestamp(raw_ts, tz=timezone.utc).astimezone(IST)
            source_ts = dt_ist.strftime("%Y-%m-%d %H:%M:%S IST")
            price_date = dt_ist.date()
        else:
            now_ist = datetime.now(IST)
            source_ts = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
            price_date = now_ist.date()

        return ProviderPrice(
            date=price_date,
            price_24k_inr=round(float(price_24k), 2),
            price_22k_inr=round(float(price_22k), 2) if price_22k is not None else None,
            source="GoldAPI.io (Live INR Spot)",
            source_timestamp=source_ts,
            is_converted=False,
            notes="Direct INR rate from GoldAPI.io"
        )

    async def get_history(self, days: int) -> List[ProviderPrice]:
        """
        GoldAPI.io requires querying one date per call (/api/XAU/INR/YYYYMMDD).
        Note: Daily historical calls count against monthly quota (100 calls/month).
        """
        if not self.api_key:
            raise ValueError(
                "GoldAPI.io key is not configured. Please set GOLDAPI_KEY in your .env file."
            )

        headers = {
            "x-access-token": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "GoldDailyAnalysis/1.0"
        }

        results: List[ProviderPrice] = []
        today = datetime.now(IST).date()

        async with httpx.AsyncClient(timeout=15.0) as client:
            for i in range(days, 0, -1):
                target_date = today - timedelta(days=i)
                date_str = target_date.strftime("%Y%m%d")
                url = f"{self.BASE_URL}/XAU/INR/{date_str}"
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    p24 = data.get("price_gram_24k") or (data.get("price", 0) / 31.1034768)
                    p22 = data.get("price_gram_22k")
                    raw_ts = data.get("timestamp")
                    ts_str = (
                        datetime.fromtimestamp(raw_ts, tz=timezone.utc).astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")
                        if raw_ts else f"{target_date.isoformat()} 00:00:00 IST"
                    )
                    results.append(
                        ProviderPrice(
                            date=target_date,
                            price_24k_inr=round(float(p24), 2),
                            price_22k_inr=round(float(p22), 2) if p22 else None,
                            source="GoldAPI.io (Historical)",
                            source_timestamp=ts_str,
                            is_converted=False
                        )
                    )
                elif resp.status_code == 429:
                    raise ValueError("GoldAPI.io rate limit reached while fetching history.")
                # We skip missing days / weekends without inventing data

        return results
