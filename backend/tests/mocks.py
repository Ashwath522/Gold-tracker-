from datetime import date, timedelta
from typing import List, Optional
from app.providers.base import GoldPriceProvider, ProviderPrice

class MockGoldProvider(GoldPriceProvider):
    """
    Mock provider strictly used for unit testing.
    Never used in runtime or production code.
    Generates deterministic price histories and can simulate provider failures.
    """

    def __init__(
        self,
        base_price: float = 7500.0,
        days: int = 120,
        should_fail: bool = False,
        failure_msg: str = "Mock API connection error"
    ):
        self.base_price = base_price
        self.days = days
        self.should_fail = should_fail
        self.failure_msg = failure_msg
        self._history: List[ProviderPrice] = []
        self._generate_mock_history()

    def _generate_mock_history(self):
        end_date = date(2026, 10, 7)
        # Create realistic deterministic price oscillations
        import math
        self._history = []
        for i in range(self.days, 0, -1):
            d = end_date - timedelta(days=i)
            # sinusoidal oscillation around base_price
            price_variation = math.sin(i / 10.0) * 150.0 + (i * 0.5)
            p24 = round(self.base_price + price_variation, 2)
            p22 = round(p24 * (22.0 / 24.0), 2)
            self._history.append(
                ProviderPrice(
                    date=d,
                    price_24k_inr=p24,
                    price_22k_inr=p22,
                    source="Mock Provider (Unit Test Only)",
                    source_timestamp=f"{d.isoformat()} 11:30:00 IST",
                    is_converted=False,
                    notes="Deterministic test data"
                )
            )

    async def get_latest(self) -> ProviderPrice:
        if self.should_fail:
            raise RuntimeError(self.failure_msg)
        
        last = self._history[-1] if self._history else None
        today = date(2026, 10, 7)
        price_24k = (last.price_24k_inr - 20.0) if last else self.base_price
        return ProviderPrice(
            date=today,
            price_24k_inr=round(price_24k, 2),
            price_22k_inr=round(price_24k * (22.0 / 24.0), 2),
            source="Mock Provider (Unit Test Only)",
            source_timestamp=f"{today.isoformat()} 12:00:00 IST",
            is_converted=False,
            notes="Mock latest"
        )

    async def get_history(self, days: int) -> List[ProviderPrice]:
        if self.should_fail:
            raise RuntimeError(self.failure_msg)
        return self._history[-days:] if len(self._history) > days else self._history
