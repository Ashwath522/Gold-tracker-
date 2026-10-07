#!/usr/bin/env python3
"""
Rescale stored gold price history to Indian retail levels (import duty + premium).

Why: rows saved before the India adjustment existed are on the raw international
scale (~19% lower). If they sit next to adjusted rows, the model sees a fake
price spike and scores today as "very expensive".

Usage (run from the repo root, same place you start uvicorn):
  python backend/scripts/rescale_history.py --before 2026-10-07          # dry run
  python backend/scripts/rescale_history.py --before 2026-10-07 --apply  # write

--before: only rows dated strictly before this day are scaled (use the first day
the adjusted code was running). Rows already tagged "India adj" are skipped, so
running it twice is safe.
"""
import sys
import os
import argparse
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models import GoldPrice
from app.config import settings

TAG = "India adj"


def main():
    ap = argparse.ArgumentParser(description="Rescale old price rows by the India multiplier")
    ap.add_argument("--before", required=True, help="YYYY-MM-DD; scale rows dated before this")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    cutoff = date.fromisoformat(args.before)
    m = settings.price_multiplier
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        rows = db.query(GoldPrice).filter(GoldPrice.date < cutoff).order_by(GoldPrice.date).all()
        todo = [r for r in rows if not (r.notes and TAG in r.notes)]
        print(f"multiplier x{m:.5f} | rows before {cutoff}: {len(rows)} | to rescale: {len(todo)}")
        if todo:
            a, b = todo[0], todo[-1]
            print(f"  first {a.date}: {a.price_24k_inr} -> {round(a.price_24k_inr * m, 2)}")
            print(f"  last  {b.date}: {b.price_24k_inr} -> {round(b.price_24k_inr * m, 2)}")
        if not args.apply:
            print("Dry run only. Re-run with --apply to write.")
            return
        for r in todo:
            r.price_24k_inr = round(r.price_24k_inr * m, 2)
            if r.price_22k_inr is not None:
                r.price_22k_inr = round(r.price_22k_inr * m, 2)
            r.notes = f"{r.notes} | {TAG} x{m:.4f} (rescaled)" if r.notes else f"{TAG} x{m:.4f} (rescaled)"
        db.commit()
        print(f"Rescaled {len(todo)} rows.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
