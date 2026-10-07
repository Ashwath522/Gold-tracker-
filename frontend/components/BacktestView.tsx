"use client";

import React, { useState, useEffect } from "react";
import { BacktestPayload } from "@/types";
import { Play, AlertCircle, CheckCircle, TrendingDown, Layers, Zap } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from "recharts";

export default function BacktestView() {
  const [backtest, setBacktest] = useState<BacktestPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/backtest", { method: "POST" });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Backtest failed");
      }
      const data = await res.json();
      setBacktest(data);
    } catch (err: any) {
      setError(err.message || "Failed to execute backtest");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, []);

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "0.75rem" }}>
        <div>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
            Honest Day-By-Day Backtesting Simulator
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Simulates strictly on historical information available up to that day (zero lookahead bias, with 3% GST included)
          </p>
        </div>

        <button className="btn btn-primary btn-sm" onClick={runSimulation} disabled={loading}>
          <Play size={14} /> {loading ? "Simulating..." : "Re-run Simulation"}
        </button>
      </div>

      {error && (
        <div className="banner banner-stale" style={{ color: "var(--rose)", borderColor: "rgba(244,63,94,0.3)" }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {backtest && (
        <>
          {/* Sample Size Warning */}
          {backtest.sample_warning && (
            <div className="banner banner-stale">
              <AlertCircle size={16} />
              <span>{backtest.sample_warning}</span>
            </div>
          )}

          {/* Model Efficacy Banner */}
          <div
            style={{
              padding: "1rem 1.25rem",
              borderRadius: "var(--radius-md)",
              marginBottom: "1.5rem",
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              background: backtest.model_lowered_cost ? "rgba(16, 185, 129, 0.12)" : "rgba(244, 63, 94, 0.12)",
              border: `1px solid ${backtest.model_lowered_cost ? "rgba(16, 185, 129, 0.3)" : "rgba(244, 63, 94, 0.3)"}`
            }}
          >
            {backtest.model_lowered_cost ? (
              <CheckCircle size={22} color="var(--emerald)" />
            ) : (
              <AlertCircle size={22} color="var(--rose)" />
            )}
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.95rem", color: backtest.model_lowered_cost ? "var(--emerald)" : "var(--rose)" }}>
                {backtest.model_lowered_cost
                  ? `Model Successfully Lowered Cost by ₹${backtest.cost_difference_per_gram.toFixed(2)}/g (${backtest.cost_improvement_pct.toFixed(2)}%) vs Equal-Spend Baseline!`
                  : `Model Did Not Lower Average Cost in this Period (${backtest.cost_difference_per_gram.toFixed(2)} ₹/g difference).`}
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Fair Test Principle: Strategy B spent an extra ₹{backtest.extra_money_deployed.toLocaleString("en-IN")}. The equal-spend baseline tests if investing that same total sum evenly would have beaten or lagged the model.
              </div>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="table-wrapper" style={{ marginBottom: "1.5rem" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Total Invested (₹)</th>
                  <th>Total Gold (g)</th>
                  <th>Average Cost / Gram</th>
                  <th>Portfolio Final Value</th>
                  <th>Net Return %</th>
                  <th>Max Portfolio Drawdown</th>
                </tr>
              </thead>
              <tbody>
                {/* Strategy A */}
                <tr>
                  <td><strong>Strategy A (₹35 Fixed)</strong></td>
                  <td>₹{backtest.strategy_a.total_invested.toLocaleString("en-IN")}</td>
                  <td>{backtest.strategy_a.total_grams.toFixed(4)}g</td>
                  <td>₹{backtest.strategy_a.avg_cost_per_gram.toLocaleString("en-IN")}</td>
                  <td>₹{backtest.strategy_a.final_value.toLocaleString("en-IN")}</td>
                  <td style={{ color: backtest.strategy_a.return_pct >= 0 ? "var(--emerald)" : "var(--rose)", fontWeight: 700 }}>
                    {backtest.strategy_a.return_pct > 0 ? "+" : ""}{backtest.strategy_a.return_pct}%
                  </td>
                  <td style={{ color: "var(--rose)" }}>{backtest.strategy_a.max_drawdown_pct}%</td>
                </tr>

                {/* Strategy Scaled Baseline */}
                <tr style={{ background: "rgba(255, 255, 255, 0.02)" }}>
                  <td>
                    <strong>Equal-Spend Baseline</strong>
                    <div style={{ fontSize: "0.725rem", color: "var(--text-dim)" }}>Strategy A scaled to identical spend</div>
                  </td>
                  <td>₹{backtest.strategy_scaled.total_invested.toLocaleString("en-IN")}</td>
                  <td>{backtest.strategy_scaled.total_grams.toFixed(4)}g</td>
                  <td style={{ color: "var(--amber)", fontWeight: 700 }}>
                    ₹{backtest.strategy_scaled.avg_cost_per_gram.toLocaleString("en-IN")}
                  </td>
                  <td>₹{backtest.strategy_scaled.final_value.toLocaleString("en-IN")}</td>
                  <td style={{ color: backtest.strategy_scaled.return_pct >= 0 ? "var(--emerald)" : "var(--rose)", fontWeight: 700 }}>
                    {backtest.strategy_scaled.return_pct > 0 ? "+" : ""}{backtest.strategy_scaled.return_pct}%
                  </td>
                  <td style={{ color: "var(--rose)" }}>{backtest.strategy_scaled.max_drawdown_pct}%</td>
                </tr>

                {/* Strategy B */}
                <tr style={{ background: "rgba(230, 175, 46, 0.05)", borderLeft: "3px solid var(--gold-primary)" }}>
                  <td>
                    <strong style={{ color: "var(--gold-bright)" }}>Strategy B (₹35 + Model Extra)</strong>
                    <div style={{ fontSize: "0.725rem", color: "var(--gold-primary)" }}>Opportunistic Dip Accumulation</div>
                  </td>
                  <td>₹{backtest.strategy_b.total_invested.toLocaleString("en-IN")}</td>
                  <td><strong>{backtest.strategy_b.total_grams.toFixed(4)}g</strong></td>
                  <td style={{ color: "var(--emerald)", fontWeight: 800, fontSize: "0.95rem" }}>
                    ₹{backtest.strategy_b.avg_cost_per_gram.toLocaleString("en-IN")}
                  </td>
                  <td>₹{backtest.strategy_b.final_value.toLocaleString("en-IN")}</td>
                  <td style={{ color: backtest.strategy_b.return_pct >= 0 ? "var(--emerald)" : "var(--rose)", fontWeight: 700 }}>
                    {backtest.strategy_b.return_pct > 0 ? "+" : ""}{backtest.strategy_b.return_pct}%
                  </td>
                  <td style={{ color: "var(--rose)" }}>{backtest.strategy_b.max_drawdown_pct}%</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Signal Distribution Breakdown */}
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", padding: "1.25rem", borderRadius: "var(--radius-md)", marginBottom: "1rem" }}>
            <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
              Simulation Signal Distribution across {backtest.days_tested} Days ({backtest.start_date} to {backtest.end_date})
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem" }}>
              {Object.entries(backtest.signal_counts).map(([label, count]) => (
                <div key={label} style={{ background: "var(--bg-card)", border: "1px solid var(--border-light)", padding: "0.75rem", borderRadius: "var(--radius-sm)" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--gold-bright)", marginTop: "2px" }}>
                    {count} days
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>
                    {((count / backtest.days_tested) * 100).toFixed(0)}% of tested period
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ fontSize: "0.775rem", color: "var(--text-dim)", lineHeight: 1.5, marginTop: "0.5rem" }}>
            {backtest.disclaimer}
          </div>
        </>
      )}
    </div>
  );
}
