from datetime import date, datetime
from typing import List, Optional, Tuple, Dict, Any
import io
import csv
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models import Investment, utc_now
from ..schemas import InvestmentCreate, InvestmentUpdate, InvestmentOut, PortfolioSummary
from ..config import settings

class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def add_investment(self, data: InvestmentCreate) -> Investment:
        """
        Record a new manual investment (e.g. from PhonePe).
        If actual grams is not provided, estimate: (amount / (1 + GST)) / market_price.
        Real average purchase price = actual_amount / actual_grams.
        """
        gst_rate = settings.GST_RATE
        is_estimated = False
        actual_grams = data.actual_grams

        # Calculate GST paid if not explicitly provided
        gst_paid = data.gst_paid
        if gst_paid is None:
            # e.g., 100 invested with 3% GST -> net 97.087, gst 2.913
            net_amount = data.actual_amount / (1.0 + gst_rate)
            gst_paid = round(data.actual_amount - net_amount, 2)

        if actual_grams is None or actual_grams <= 0:
            is_estimated = True
            net_amount = data.actual_amount - gst_paid
            actual_grams = round(net_amount / data.market_price, 6)
        else:
            actual_grams = round(actual_grams, 6)

        avg_price = round(data.actual_amount / actual_grams, 2) if actual_grams > 0 else data.market_price

        inv = Investment(
            date=data.date,
            time_ist=data.time_ist,
            market_price=round(data.market_price, 2),
            model_score=data.model_score,
            model_rec_fixed=data.model_rec_fixed,
            model_rec_extra=data.model_rec_extra,
            model_rec_total=data.model_rec_total,
            actual_amount=round(data.actual_amount, 2),
            gst_paid=round(gst_paid, 2) if gst_paid is not None else None,
            actual_grams=actual_grams,
            is_estimated_grams=is_estimated,
            avg_purchase_price=avg_price,
            notes=data.notes
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def update_investment(self, inv_id: int, data: InvestmentUpdate) -> Optional[Investment]:
        inv = self.db.query(Investment).filter(Investment.id == inv_id).first()
        if not inv:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(inv, key, val)

        # Recalculate average purchase price if amount or grams changed
        if inv.actual_grams > 0:
            inv.avg_purchase_price = round(inv.actual_amount / inv.actual_grams, 2)

        inv.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def delete_investment(self, inv_id: int) -> bool:
        inv = self.db.query(Investment).filter(Investment.id == inv_id).first()
        if not inv:
            return False
        self.db.delete(inv)
        self.db.commit()
        return True

    def list_investments(self) -> List[Investment]:
        return self.db.query(Investment).order_by(desc(Investment.date), desc(Investment.time_ist)).all()

    def get_portfolio_summary(self, current_market_price: float) -> PortfolioSummary:
        investments = self.db.query(Investment).all()
        if not investments:
            return PortfolioSummary(
                total_invested=0.0,
                total_grams=0.0,
                current_market_price=current_market_price,
                current_nominal_value=0.0,
                estimated_net_selling_value=0.0,
                sell_spread_pct=round(settings.SELL_SPREAD_PCT * 100, 2),
                unrealized_pnl=0.0,
                return_pct=0.0,
                avg_purchase_price=0.0,
                investment_days=0,
                avg_daily_investment=0.0,
                total_fixed_amount=0.0,
                total_extra_amount=0.0,
                followed_rec_days=0,
                diverged_rec_days=0
            )

        total_invested = sum(inv.actual_amount for inv in investments)
        total_grams = sum(inv.actual_grams for inv in investments)
        current_nominal_value = total_grams * current_market_price
        
        # Real selling price considers spread (e.g. 3%)
        estimated_net_selling_value = current_nominal_value * (1.0 - settings.SELL_SPREAD_PCT)
        unrealized_pnl = estimated_net_selling_value - total_invested
        return_pct = (unrealized_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
        avg_purchase_price = (total_invested / total_grams) if total_grams > 0 else 0.0

        investment_days = len(set(inv.date for inv in investments))
        avg_daily_invest = total_invested / investment_days if investment_days > 0 else 0.0

        total_fixed = sum(inv.model_rec_fixed for inv in investments)
        total_extra = sum(max(0.0, inv.actual_amount - inv.model_rec_fixed) for inv in investments)

        followed = 0
        diverged = 0
        for inv in investments:
            if abs(inv.actual_amount - inv.model_rec_total) < 2.0:
                followed += 1
            else:
                diverged += 1

        return PortfolioSummary(
            total_invested=round(total_invested, 2),
            total_grams=round(total_grams, 4),
            current_market_price=round(current_market_price, 2),
            current_nominal_value=round(current_nominal_value, 2),
            estimated_net_selling_value=round(estimated_net_selling_value, 2),
            sell_spread_pct=round(settings.SELL_SPREAD_PCT * 100, 2),
            unrealized_pnl=round(unrealized_pnl, 2),
            return_pct=round(return_pct, 2),
            avg_purchase_price=round(avg_purchase_price, 2),
            investment_days=investment_days,
            avg_daily_investment=round(avg_daily_invest, 2),
            total_fixed_amount=round(total_fixed, 2),
            total_extra_amount=round(total_extra, 2),
            followed_rec_days=followed,
            diverged_rec_days=diverged
        )

    def export_csv(self) -> str:
        investments = self.list_investments()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "date", "time_ist", "market_price", "model_score",
            "model_rec_fixed", "model_rec_extra", "model_rec_total",
            "actual_amount", "gst_paid", "actual_grams",
            "is_estimated_grams", "avg_purchase_price", "notes"
        ])
        for inv in investments:
            writer.writerow([
                inv.date.isoformat(),
                inv.time_ist,
                inv.market_price,
                inv.model_score or "",
                inv.model_rec_fixed,
                inv.model_rec_extra,
                inv.model_rec_total,
                inv.actual_amount,
                inv.gst_paid or "",
                f"{inv.actual_grams:.6f}",
                inv.is_estimated_grams,
                inv.avg_purchase_price,
                inv.notes or ""
            ])
        return output.getvalue()

    def import_csv(self, csv_content: str) -> int:
        reader = csv.DictReader(io.StringIO(csv_content))
        count = 0
        for row in reader:
            d = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
            amount = float(row["actual_amount"])
            market_p = float(row["market_price"])
            grams = float(row["actual_grams"]) if row.get("actual_grams") else None
            gst = float(row["gst_paid"]) if row.get("gst_paid") else None
            
            data = InvestmentCreate(
                date=d,
                time_ist=row.get("time_ist", "12:00:00").strip(),
                market_price=market_p,
                model_score=float(row["model_score"]) if row.get("model_score") else None,
                model_rec_fixed=float(row.get("model_rec_fixed", 35.0)),
                model_rec_extra=float(row.get("model_rec_extra", 0.0)),
                model_rec_total=float(row.get("model_rec_total", 35.0)),
                actual_amount=amount,
                gst_paid=gst,
                actual_grams=grams,
                notes=row.get("notes")
            )
            self.add_investment(data)
            count += 1
        return count
