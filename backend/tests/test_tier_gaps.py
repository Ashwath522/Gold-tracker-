import pytest
from app.analysis.scorer import match_tier


@pytest.mark.parametrize("score,label,extra", [
    (0.0, "Very expensive", 0.0),
    (30.0, "Very expensive", 0.0),
    (30.5, "Very expensive", 0.0),
    (30.99, "Very expensive", 0.0),
    (31.0, "Expensive", 10.0),
    (45.5, "Expensive", 10.0),
    (46.0, "Normal", 25.0),
    (60.5, "Normal", 25.0),
    (61.0, "Cheap", 40.0),
    (80.5, "Cheap", 40.0),
    (81.0, "Very cheap", 65.0),
    (100.0, "Very cheap", 65.0),
])
def test_no_gaps_between_tiers(score, label, extra):
    t = match_tier(score)
    assert t.label == label
    assert t.extra_amount == extra
