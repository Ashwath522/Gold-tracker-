"use client";

import React, { useState, useEffect } from "react";
import { PortfolioSummary } from "@/types";
import { Wallet, PieChart, ArrowUpRight, ArrowDownRight, Award, DollarSign } from "lucide-react";

interface Props {
  refreshTrigger: number;
}

export default function PortfolioView({ refreshTrigger }: Props) {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/investments/portfolio");
      if (res.ok) {
        const data = await res.json();
        setPortfolio(data);
      }
    } catch (err) {
      console.error("Failed to fetch portfolio", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, [refreshTrigger]);

  if (!portfolio) {
    return <div className="card" style={{ padding: "2rem", textAlign: "center" }}>Loading portfolio summary...</div>;
  }

  const isProfit = portfolio.unrealized_pnl >= 0;

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
            Aggregated Portfolio & Performance View
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Real metrics computed from actual PhonePe purchase history and current live rates
          </p>
        </div>
        <div style={{ fontSize: "0.8rem", color: "var(--text-dim)", background: "var(--bg-surface)", padding: "0.4rem 0.8rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)" }}>
          Estimated Sell-Spread: <strong>{portfolio.sell_spread_pct}%</strong>
        </div>
      </div>

      {/* Grid of Key Portfolio Tiles */}
      <div className="metrics-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="metric-tile" style={{ borderLeft: "3px solid var(--gold-primary)" }}>
          <span className="metric-tile-title">Total Invested</span>
          <span className="metric-tile-val" style={{ color: "var(--text-main)" }}>
            ₹{portfolio.total_invested.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
            Over {portfolio.investment_days} investment days (Avg ₹{portfolio.avg_daily_investment.toFixed(0)}/day)
          </span>
        </div>

        <div className="metric-tile" style={{ borderLeft: "3px solid var(--gold-bright)" }}>
          <span className="metric-tile-title">Total Gold Accumulated</span>
          <span className="metric-tile-val" style={{ color: "var(--gold-bright)" }}>
            {portfolio.total_grams.toFixed(4)} <span style={{ fontSize: "0.85rem" }}>grams</span>
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
            24K (999 purity equivalent)
          </span>
        </div>

        <div className="metric-tile" style={{ borderLeft: isProfit ? "3px solid var(--emerald)" : "3px solid var(--rose)" }}>
          <span className="metric-tile-title">Net Liquidation Value</span>
          <span className="metric-tile-val">
            ₹{portfolio.estimated_net_selling_value.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </span>
          <span style={{ fontSize: "0.75rem", color: isProfit ? "var(--emerald)" : "var(--rose)", display: "flex", alignItems: "center", gap: "2px" }}>
            {isProfit ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
            {isProfit ? "+" : ""}₹{portfolio.unrealized_pnl.toFixed(2)} ({portfolio.return_pct > 0 ? "+" : ""}{portfolio.return_pct}%)
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-title">Average Cost / Gram</span>
          <span className="metric-tile-val" style={{ color: "var(--gold-primary)" }}>
            ₹{portfolio.avg_purchase_price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
            vs Current Market: ₹{portfolio.current_market_price.toLocaleString("en-IN")}
          </span>
        </div>
      </div>

      {/* Breakdown: Fixed vs Extra & Model Adherence */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem", marginTop: "1rem" }}>
        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", padding: "1.25rem", borderRadius: "var(--radius-md)" }}>
          <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
            Rupee Deployment Breakdown
          </h4>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", fontSize: "0.85rem" }}>
            <span style={{ color: "var(--text-muted)" }}>Total Fixed Base (₹35/day):</span>
            <strong>₹{portfolio.total_fixed_amount.toLocaleString("en-IN")}</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem", fontSize: "0.85rem" }}>
            <span style={{ color: "var(--text-muted)" }}>Total Model Extra Deployed:</span>
            <strong style={{ color: "var(--gold-bright)" }}>₹{portfolio.total_extra_amount.toLocaleString("en-IN")}</strong>
          </div>
          <div className="score-progress-track">
            <div
              className="score-progress-bar"
              style={{
                width: `${portfolio.total_invested > 0 ? (portfolio.total_extra_amount / portfolio.total_invested) * 100 : 0}%`,
              }}
            />
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)", display: "block", marginTop: "0.4rem" }}>
            {portfolio.total_invested > 0
              ? `${((portfolio.total_extra_amount / portfolio.total_invested) * 100).toFixed(1)}% extra opportunistically deployed on dips`
              : "No deployment yet"}
          </span>
        </div>

        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", padding: "1.25rem", borderRadius: "var(--radius-md)" }}>
          <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
            Model Recommendation Adherence
          </h4>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", fontSize: "0.85rem" }}>
            <span style={{ color: "var(--text-muted)" }}>Days Followed Recommendation:</span>
            <strong style={{ color: "var(--emerald)" }}>{portfolio.followed_rec_days} days</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem", fontSize: "0.85rem" }}>
            <span style={{ color: "var(--text-muted)" }}>Days Diverged / Custom Amount:</span>
            <strong style={{ color: "var(--amber)" }}>{portfolio.diverged_rec_days} days</strong>
          </div>
          <div className="score-progress-track">
            <div
              className="score-progress-bar"
              style={{
                width: `${portfolio.investment_days > 0 ? (portfolio.followed_rec_days / portfolio.investment_days) * 100 : 0}%`,
                background: "linear-gradient(90deg, #10b981, #34d399)",
              }}
            />
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)", display: "block", marginTop: "0.4rem" }}>
            {portfolio.investment_days > 0
              ? `${((portfolio.followed_rec_days / portfolio.investment_days) * 100).toFixed(0)}% discipline score`
              : "Ready to log first day"}
          </span>
        </div>
      </div>
    </div>
  );
}
