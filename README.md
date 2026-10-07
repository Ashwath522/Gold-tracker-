# Gold Daily Analysis (Gold-tracker-)

A personal, single-user digital gold accumulation advisory and tracking web application.

---

## 1. Purpose & Philosophy

I invest **₹35 EVERY day** in digital gold via PhonePe. The app decides **ONLY the EXTRA amount** on top of ₹35, based on how cheap gold is relative to its recent history.

$$\text{Total Daily Investment} = ₹35\text{ fixed} + \text{model extra}$$

- **Core Principle:** Accumulate more gold when the price is relatively **LOW**. Never invest more just because the price is rising.
- **Not a Trading Bot:** This is **NOT** a trading bot, **NOT** a trend-following system, and **NOT** a price predictor. It never outputs speculative claims like *"gold will rise"*.
- **Wording Standard:** Output is always framed as: *"Current price appears relatively cheap/expensive compared with its recent history, so the model recommends X"*.
- **The ₹35 Base:** The ₹35 base is **never removed**, even when gold is at all-time highs.

---

## 2. Architecture & Tech Stack

- **Frontend:** Next.js (App Router, TypeScript), Recharts, Lucide Icons, and Vanilla CSS luxury dark gold design system.
- **Backend:** Python FastAPI, pandas, NumPy, SQLAlchemy, Pydantic v2.
- **Database:** SQLite for local development (`gold_analysis.db`), with schema fully compatible with PostgreSQL and Supabase for cloud deployment.
- **Timezone:** `Asia/Kolkata` (IST) across all operations.

---

## 3. Data Providers (No Fake Data)

All price feeds implement the `GoldPriceProvider` abstraction (`get_latest()` and `get_history(days)`):

1. **`GoldAPI.io` (`GOLD_PRICE_PROVIDER=goldapi`):**
   - Connects to `https://www.goldapi.io/api/XAU/INR`.
   - Returns real live 24K and 22K per-gram prices in INR with the provider's exact timestamp.
   - Requires API key in `.env` (Free tier: 100 requests/month).
2. **`Yahoo Finance` (`GOLD_PRICE_PROVIDER=yahoo`):**
   - Converts COMEX continuous gold (`GC=F`) and USD/INR (`INR=X`) to INR per gram (`price / 31.1034768`).
   - Labeled clearly: *"Yahoo Finance (converted international price, may differ from PhonePe)"*.
   - Free, requires no API key, and provides 365+ days of daily history for deep backtesting without quota limits.
3. **`MockGoldProvider`:**
   - Isolated in `backend/tests/mocks.py` for automated unit tests only (never imported or used at runtime).

---

## 4. Multi-Factor Valuation Score (0–100)

Higher Score = Cheaper = More Attractive for Extra Accumulation.

| Factor | Weight | Rule & Logic |
| :--- | :--- | :--- |
| **Price vs 90D Range** | **25%** | $100 - \text{Range Position}$. Near 90-day low scores near 100 pts; near high scores near 0 pts. |
| **Price vs Moving Averages** | **20%** | Mean distance from 30/60/90D SMAs. Trading below SMAs yields high points; far above averages penalizes score. |
| **Anti-Spike Momentum** | **15%** | 30/60/90D Rate of Change. Sharp rallies are penalized (anti-spike rule); stabilizing pullbacks score higher. |
| **Recent Drawdown from 90D High** | **15%** | Discount from recent peak. Deeper pullbacks offer higher margin of safety and higher score. |
| **Relative Lows (Percentile Rank)** | **15%** | Percentage of trading days closing above current price across windows. |
| **Volatility / Risk** | **10%** | Annualized standard deviation of daily returns. Calm, orderly price action scores higher for systematic accumulation. |

### Recommendation Mapping

| Score Range | Category | Cheap Status | Fixed | Model Extra | Total Daily Investment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0 – 30** | Very expensive | **NO** | ₹35 | ₹0 | **₹35** |
| **31 – 45** | Expensive | **NO** | ₹35 | ₹10 | **₹45** |
| **46 – 60** | Normal | **NORMAL** | ₹35 | ₹25 | **₹60** |
| **61 – 80** | Cheap | **YES** | ₹35 | ₹40 | **₹75** |
| **81 – 100** | Very cheap | **YES** | ₹35 | ₹65 | **₹100** |

---

## 5. Investment Tracker (PhonePe Actuals)

PhonePe digital gold charges 3% GST and has a buy/sell spread, so your real purchase price is higher than the raw spot price.

- **Actual Grams Received:** Enter the exact grams PhonePe credited to your account.
- **True Cost Per Gram:** Auto-computed as $\frac{\text{Actual Rupees Invested}}{\text{Actual Grams Received}}$.
- **Auto-Estimation:** If grams are omitted, estimated as $\frac{\text{Amount} / (1 + \text{GST})}{\text{Market Rate}}$ and marked `(est.)`.
- **CSV Support:** Full CSV import and export for backup and spreadsheet analysis.

---

## 6. Honest Day-by-Day Backtesting

Simulates day by day using strictly the data available up to that day (zero lookahead bias), incorporating 3% GST:
- **Strategy A:** ₹35 every day.
- **Strategy B:** ₹35 + model recommended extra amount.
- **Equal-Spend Baseline:** Strategy A scaled to spend the identical total rupees as Strategy B, distributed evenly across days.

> **Efficacy Standard:** The model only counts as useful if it lowers the **average cost per gram** compared to the equal-spend baseline, rather than merely deploying more money in an uptrend.

---

## 7. Setup & Run Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ (tested on Node v22)

### Quick Start

1. **Clone & Configure Environment:**
   ```bash
   cp .env.example .env
   # Add your GoldAPI.io key if using goldapi, or set GOLD_PRICE_PROVIDER=yahoo
   ```

2. **Backend Setup:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Backfill Historical Data (One-Time):**
   ```bash
   source .venv/bin/activate
   python backend/scripts/backfill.py --days 90
   ```

4. **Start Backend Server:**
   ```bash
   source .venv/bin/activate
   PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Frontend Setup & Start:**
   ```bash
   cd frontend
   npm install
   npm run dev -p 3000
   ```

6. Open your browser at **[http://localhost:3000](http://localhost:3000)**.

### Running Automated Tests
```bash
source .venv/bin/activate
PYTHONPATH=backend pytest backend/tests/ -v
```
All 25 unit tests verify providers, caching TTL, 11:30 AM IST benchmark logic, analysis pure functions, scoring rules, anti-spike momentum, and backtest simulations.
