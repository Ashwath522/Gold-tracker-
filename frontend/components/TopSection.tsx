"use client";

import React, { useState } from "react";
import { LatestPrice, ScoreReport } from "@/types";
import { RefreshCw, AlertTriangle, Clock, ShieldCheck, Sparkles, Database } from "lucide-react";

interface Props {
  latest: LatestPrice;
  scoreReport: ScoreReport;
  onRefresh: () => void;
  refreshing: boolean;
}

export default function TopSection({ latest, scoreReport, onRefresh, refreshing }: Props) {
  const [karat, setKarat] = useState<"24k" | "22k">("24k");

  const currentPriceGram = karat === "24k" 
    ? latest.price_24k_inr 
    : (latest.price_22k_inr || latest.price_24k_inr * (22 / 24));
  
  const currentPrice10g = currentPriceGram * 10;

  // Status pill styling
  const pillClass = scoreReport.is_cheap === "YES" 
    ? "status-pill-yes" 
    : scoreReport.is_cheap === "NO" 
    ? "status-pill-no" 
    : "status-pill-normal";

  return (
    <div>
      {/* Stale Warning Banner if applicable */}
      {latest.is_stale && (
        <div className="banner banner-stale">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <AlertTriangle size={18} />
            <span>
              <strong>Stale Data Warning:</strong> Could not connect to live provider feed. Displaying cached rate from {latest.source_timestamp}.
            </span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onRefresh} disabled={refreshing}>
            <RefreshCw size={14} className={refreshing ? "spin" : ""} /> Retry Fetch
          </button>
        </div>
      )}

      {/* Benchmark Reference Banner */}
      <div className="banner banner-benchmark">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Clock size={16} />
          <span>
            <strong>Benchmark Status (11:30 AM IST):</strong> {latest.benchmark_status}
          </span>
        </div>
        <span style={{ fontSize: "0.75rem", opacity: 0.8 }}>
          Fetched: {new Date(latest.fetched_at).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" })} IST
        </span>
      </div>

      {/* Top Hero Grid */}
      <div className="hero-grid">
        {/* Left: Gold Price Today Card */}
        <div className="card card-gold-highlight price-display-box">
          <div className="price-header">
            <div>
              <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-dim)", fontWeight: 700 }}>
                Digital Gold Today
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginTop: "0.2rem" }}>
                <span className={`status-pill ${pillClass}`}>
                  Is It Cheap? {scoreReport.is_cheap}
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  ({scoreReport.category})
                </span>
              </div>
            </div>

            {/* 24K / 22K Toggle */}
            <div className="karat-toggle">
              <button
                className={`karat-btn ${karat === "24k" ? "active" : ""}`}
                onClick={() => setKarat("24k")}
              >
                24K (999)
              </button>
              <button
                className={`karat-btn ${karat === "22k" ? "active" : ""}`}
                onClick={() => setKarat("22k")}
              >
                22K (916)
              </button>
            </div>
          </div>

          <div className="price-main">
            <span className="price-large">₹{currentPriceGram.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            <span className="price-unit">/ gram</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
            <div className="price-10g">
              10 Grams: <strong>₹{currentPrice10g.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem", color: "var(--text-dim)" }}>
              <Database size={14} />
              <span>{latest.source}</span>
            </div>
          </div>

          <div className="meta-footer">
            <span>Provider Timestamp: <strong>{latest.source_timestamp}</strong></span>
            {latest.is_converted && (
              <span style={{ color: "var(--amber)", fontSize: "0.725rem" }}>
                * Converted international price, may differ from PhonePe
              </span>
            )}
          </div>
        </div>

        {/* Right: Model Recommendation Card */}
        <div className="card rec-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-dim)", fontWeight: 700 }}>
                Today&apos;s Recommendation
              </span>
              <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginTop: "0.2rem" }}>
                <span style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--gold-bright)" }}>
                  {scoreReport.total_score}
                </span>
                <span style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>/ 100 Model Score</span>
              </div>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              onClick={onRefresh}
              disabled={refreshing}
              title="Refresh live rate and model valuation"
            >
              <RefreshCw size={14} className={refreshing ? "spin" : ""} />
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {/* Investment Amounts Split */}
          <div className="amounts-row">
            <div className="amount-col">
              <span className="amount-label">Daily Fixed</span>
              <span className="amount-val">₹{scoreReport.fixed_amount}</span>
            </div>
            <div className="amount-col">
              <span className="amount-label">Model Extra</span>
              <span className="amount-val" style={{ color: scoreReport.extra_amount > 0 ? "var(--emerald)" : "var(--text-muted)" }}>
                +₹{scoreReport.extra_amount}
              </span>
            </div>
            <div className="amount-col" style={{ borderLeft: "1px solid var(--border)", paddingLeft: "0.75rem" }}>
              <span className="amount-label">Today&apos;s Total</span>
              <span className="amount-val-total">₹{scoreReport.total_amount}</span>
            </div>
          </div>

          {/* Plain-Language Why Sentence */}
          <div className="why-sentence">
            <strong>Why:</strong> {scoreReport.why_explanation}
          </div>
        </div>
      </div>
    </div>
  );
}
