"use client";

import React from "react";
import { ScoreReport } from "@/types";
import { Sliders, HelpCircle } from "lucide-react";

interface Props {
  scoreReport: ScoreReport;
}

export default function ValuationBreakdown({ scoreReport }: Props) {
  const subScoresList = Object.entries(scoreReport.sub_scores);

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
            Transparent Valuation Engine Breakdown
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Composite 0–100 score formed from 6 transparent, rule-based sub-scores (Higher = Cheaper)
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", background: "var(--bg-surface)", padding: "0.4rem 0.8rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)" }}>
          <Sliders size={16} color="var(--gold-bright)" />
          <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--gold-bright)" }}>
            Total Score: {scoreReport.total_score} / 100
          </span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
        {subScoresList.map(([key, item]) => {
          return (
            <div
              key={key}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border)",
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                display: "flex",
                flexDirection: "column",
                gap: "0.4rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-main)" }}>
                  {item.name}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontWeight: 600 }}>
                  Weight: {item.weight}%
                </span>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: "0.2rem" }}>
                <span style={{ fontSize: "1.2rem", fontWeight: 800, color: item.raw_score >= 60 ? "var(--emerald)" : item.raw_score <= 40 ? "var(--rose)" : "var(--amber)" }}>
                  {item.raw_score} <span style={{ fontSize: "0.75rem", fontWeight: 500, color: "var(--text-dim)" }}>/ 100</span>
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Contribution: +{item.weighted_score.toFixed(1)} pts
                </span>
              </div>

              <div className="score-progress-track">
                <div
                  className="score-progress-bar"
                  style={{
                    width: `${Math.max(0, Math.min(100, item.raw_score))}%`,
                    background: item.raw_score >= 60 ? "linear-gradient(90deg, #10b981, #34d399)" : item.raw_score <= 40 ? "linear-gradient(90deg, #f43f5e, #fb7185)" : "linear-gradient(90deg, #f59e0b, #fbbf24)"
                  }}
                />
              </div>

              <span style={{ fontSize: "0.775rem", color: "var(--text-dim)", marginTop: "0.3rem", lineHeight: 1.4 }}>
                {item.description}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
