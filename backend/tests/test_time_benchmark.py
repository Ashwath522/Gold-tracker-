from datetime import datetime
import zoneinfo
from app.services.price_service import compute_benchmark_status

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

def test_benchmark_status_before_1130_am():
    # 08:00 AM IST
    dt = datetime(2026, 10, 7, 8, 0, 0, tzinfo=IST)
    assert compute_benchmark_status(dt) == "Preliminary (latest available price)"

    # 11:29 AM IST (edge case right before 11:30)
    dt = datetime(2026, 10, 7, 11, 29, 59, tzinfo=IST)
    assert compute_benchmark_status(dt) == "Preliminary (latest available price)"

def test_benchmark_status_at_and_after_1130_am():
    # Exactly 11:30 AM IST
    dt = datetime(2026, 10, 7, 11, 30, 0, tzinfo=IST)
    assert compute_benchmark_status(dt) == "Updated (includes today's benchmark if available)"

    # 02:00 PM IST
    dt = datetime(2026, 10, 7, 14, 0, 0, tzinfo=IST)
    assert compute_benchmark_status(dt) == "Updated (includes today's benchmark if available)"

    # 08:45 PM IST
    dt = datetime(2026, 10, 7, 20, 45, 0, tzinfo=IST)
    assert compute_benchmark_status(dt) == "Updated (includes today's benchmark if available)"

def test_benchmark_status_midnight():
    # 00:01 AM IST
    dt = datetime(2026, 10, 7, 0, 1, 0, tzinfo=IST)
    assert compute_benchmark_status(dt) == "Preliminary (latest available price)"
