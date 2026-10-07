from dataclasses import replace
from typing import List
from .base import GoldPriceProvider, ProviderPrice


class IndiaAdjustedProvider(GoldPriceProvider):
    """
    Wraps any provider and scales its INR/gram prices by a constant multiplier
    (import duty + local premium) so values reflect Indian retail levels.

    A constant multiplier does not change any score: range position, percentile,
    drawdown, SMA distance, ROC and volatility are all scale-invariant. It only
    fixes displayed prices and the gram estimates in the investment tracker.
    """

    def __init__(self, inner: GoldPriceProvider, multiplier: float):
        self.inner = inner
        self.multiplier = multiplier

    def _adjust(self, p: ProviderPrice) -> ProviderPrice:
        m = self.multiplier
        note = f"India adj x{m:.4f} (duty + premium)"
        return replace(
            p,
            price_24k_inr=round(p.price_24k_inr * m, 2),
            price_22k_inr=round(p.price_22k_inr * m, 2) if p.price_22k_inr is not None else None,
            notes=f"{p.notes} | {note}" if p.notes else note,
        )

    async def get_latest(self) -> ProviderPrice:
        return self._adjust(await self.inner.get_latest())

    async def get_history(self, days: int) -> List[ProviderPrice]:
        return [self._adjust(p) for p in await self.inner.get_history(days)]
