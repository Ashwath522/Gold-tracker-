from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ScoreWeights:
    price_vs_90d_range: float = 25.0
    price_vs_moving_averages: float = 20.0
    momentum_30_60_90: float = 15.0
    recent_drawdown: float = 15.0
    relative_lows: float = 15.0
    volatility_risk: float = 10.0

    @property
    def total_weight(self) -> float:
        return (
            self.price_vs_90d_range
            + self.price_vs_moving_averages
            + self.momentum_30_60_90
            + self.recent_drawdown
            + self.relative_lows
            + self.volatility_risk
        )

@dataclass
class RecommendationTier:
    min_score: float
    max_score: float
    label: str
    is_cheap_label: str  # "NO", "NORMAL", "YES"
    extra_amount: float
    fixed_amount: float = 35.0

    @property
    def total_amount(self) -> float:
        return self.fixed_amount + self.extra_amount

# Default recommendation tiers as configured in spec
RECOMMENDATION_TIERS: List[RecommendationTier] = [
    RecommendationTier(min_score=0.0, max_score=30.0, label="Very expensive", is_cheap_label="NO", extra_amount=0.0),
    RecommendationTier(min_score=31.0, max_score=45.0, label="Expensive", is_cheap_label="NO", extra_amount=10.0),
    RecommendationTier(min_score=46.0, max_score=60.0, label="Normal", is_cheap_label="NORMAL", extra_amount=25.0),
    RecommendationTier(min_score=61.0, max_score=80.0, label="Cheap", is_cheap_label="YES", extra_amount=40.0),
    RecommendationTier(min_score=81.0, max_score=100.0, label="Very cheap", is_cheap_label="YES", extra_amount=65.0),
]

DEFAULT_WEIGHTS = ScoreWeights()
