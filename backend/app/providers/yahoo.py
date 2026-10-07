import httpx
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional
import zoneinfo
from .base import GoldPriceProvider, ProviderPrice

IST = zoneinfo.ZoneInfo("Asia/Kolkata")
TROY_OZ_TO_GRAM = 31.1034768

class YahooGoldProvider(GoldPriceProvider):
    """
    Gold price provider using Yahoo Finance market data (GC=F Gold Spot/Futures and INR=X USD/INR).
    Requires NO API KEY and supports fetching 90 days to 1+ years of real daily closing prices.
    Spec compliance: Clearly marked as is_converted=True and labeled:
    'converted international price, may differ from PhonePe'.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    }

    async def _fetch_usd_inr_rate(self, client: httpx.AsyncClient) -> float:
        """Fetch current USD to INR exchange rate."""
        url = "https://query1.finance.yahoo.com/v8/finance/chart/INR=X?range=1d&interval=1d"
        resp = await client.get(url, headers=self.HEADERS)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch USD/INR rate from Yahoo Finance: {resp.status_code}")
        data = resp.json()
        try:
            rate = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(rate)
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"Invalid USD/INR response format from Yahoo Finance: {e}")

    async def get_latest(self) -> ProviderPrice:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Fetch USD/INR
            usd_inr = await self._fetch_usd_inr_rate(client)

            # 2. Fetch GC=F latest price
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=1d"
            resp = await client.get(url, headers=self.HEADERS)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch Gold price from Yahoo Finance: {resp.status_code}")
            data = resp.json()
            try:
                result = data["chart"]["result"][0]
                meta = result["meta"]
                market_price_usd = float(meta["regularMarketPrice"])
                raw_ts = int(meta.get("regularMarketTime", datetime.now().timestamp()))
            except (KeyError, IndexError, TypeError) as e:
                raise RuntimeError(f"Invalid Gold response format from Yahoo Finance: {e}")

        # Convert USD per troy ounce to INR per gram
        price_per_gram_24k = (market_price_usd * usd_inr) / TROY_OZ_TO_GRAM
        # Estimate 22k as 22/24 of 24k
        price_per_gram_22k = price_per_gram_24k * (22.0 / 24.0)

        dt_ist = datetime.fromtimestamp(raw_ts, tz=timezone.utc).astimezone(IST)
        source_ts = dt_ist.strftime("%Y-%m-%d %H:%M:%S IST")

        return ProviderPrice(
            date=dt_ist.date(),
            price_24k_inr=round(price_per_gram_24k, 2),
            price_22k_inr=round(price_per_gram_22k, 2),
            source="Yahoo Finance (converted international price, may differ from PhonePe)",
            source_timestamp=source_ts,
            is_converted=True,
            notes=f"Converted: ${market_price_usd:.2f}/oz @ ₹{usd_inr:.2f}/$"
        )

    async def get_history(self, days: int) -> List[ProviderPrice]:
        # Determine range string for Yahoo Finance chart API
        if days <= 30:
            range_str = "1mo"
        elif days <= 90:
            range_str = "3mo"
        elif days <= 180:
            range_str = "6mo"
        elif days <= 365:
            range_str = "1y"
        elif days <= 730:
            range_str = "2y"
        else:
            range_str = "5y"

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Fetch Gold history
            gold_url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range={range_str}&interval=1d"
            gold_resp = await client.get(gold_url, headers=self.HEADERS)
            if gold_resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch Gold history from Yahoo: {gold_resp.status_code}")
            gold_data = gold_resp.json()

            # Fetch USD/INR history
            inr_url = f"https://query1.finance.yahoo.com/v8/finance/chart/INR=X?range={range_str}&interval=1d"
            inr_resp = await client.get(inr_url, headers=self.HEADERS)
            if inr_resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch USD/INR history from Yahoo: {inr_resp.status_code}")
            inr_data = inr_resp.json()

        try:
            g_res = gold_data["chart"]["result"][0]
            g_timestamps = g_res.get("timestamp", [])
            g_closes = g_res["indicators"]["quote"][0].get("close", [])

            i_res = inr_data["chart"]["result"][0]
            i_timestamps = i_res.get("timestamp", [])
            i_closes = i_res["indicators"]["quote"][0].get("close", [])
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Corrupt chart payload from Yahoo Finance: {e}")

        # Build date -> USD/INR close mapping (using IST dates)
        inr_map = {}
        for ts, close in zip(i_timestamps, i_closes):
            if close is not None:
                d = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(IST).date()
                inr_map[d] = float(close)

        # Fallback latest INR rate in case of weekend/holiday mismatch
        latest_inr_rate = list(inr_map.values())[-1] if inr_map else 86.0

        daily_prices = {}
        for ts, close in zip(g_timestamps, g_closes):
            if close is None:
                continue
            d = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(IST).date()
            rate = inr_map.get(d, latest_inr_rate)
            price_24k = (float(close) * rate) / TROY_OZ_TO_GRAM
            price_22k = price_24k * (22.0 / 24.0)
            ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")
            daily_prices[d] = ProviderPrice(
                date=d,
                price_24k_inr=round(price_24k, 2),
                price_22k_inr=round(price_22k, 2),
                source="Yahoo Finance (converted international price, may differ from PhonePe)",
                source_timestamp=ts_str,
                is_converted=True,
                notes=f"Converted: ${close:.2f}/oz @ ₹{rate:.2f}/$"
            )

        # Sort chronologically ascending and limit to requested days
        sorted_items = sorted(daily_prices.values(), key=lambda p: p.date)
        return sorted_items[-days:] if len(sorted_items) > days else sorted_items
