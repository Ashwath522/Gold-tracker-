"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, ShieldAlert, Award } from "lucide-react";

export default function ModelExplanationTab() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch("/api/model/explanation")
      .then((res) => res.json())
      .then((d) => setData(d))
      .catch((err) => console.error("Failed to load explanation", err));
  }, []);

  if (!data) return <div className="card" style={{ padding: "2rem" }}>Loading model explanation...</div>;

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.25rem" }}>
        <BookOpen size={22} color="var(--gold-bright)" />
        <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
          {data.title}
        </h3>
      </div>

      <div style={{ background: "rgba(230, 175, 46, 0.05)", border: "1px solid var(--border-gold)", padding: "1rem 1.25rem", borderRadius: "var(--radius-md)", marginBottom: "1.5rem", fontSize: "0.875rem", lineHeight: 1.6, color: "var(--text-main)" }}>
        <strong>Core Philosophy:</strong> {data.philosophy}
      </div>

      <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
        Sub-Score Factors & Weights (Total = 100)
      </h4>
      <div className="table-wrapper" style={{ marginBottom: "1.5rem" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Factor</th>
              <th>Weight</th>
              <th>Formula Rationale & Logic</th>
            </tr>
          </thead>
          <tbody>
            {data.weights.map((w: any) => (
              <tr key={w.factor}>
                <td><strong>{w.factor}</strong></td>
                <td style={{ color: "var(--gold-bright)", fontWeight: 700 }}>{w.weight}%</td>
                <td style={{ fontSize: "0.825rem", color: "var(--text-muted)", whiteSpace: "normal" }}>
                  {w.description}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
        Score to Recommendation Tier Mapping
      </h4>
      <div className="table-wrapper" style={{ marginBottom: "1.5rem" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Model Score</th>
              <th>Category</th>
              <th>Is Cheap?</th>
              <th>Fixed Amount</th>
              <th>Model Extra</th>
              <th>Total Daily Invest</th>
            </tr>
          </thead>
          <tbody>
            {data.recommendation_tiers.map((t: any) => (
              <tr key={t.score_range}>
                <td><strong>{t.score_range}</strong></td>
                <td>{t.category}</td>
                <td>
                  <span
                    className={`status-pill ${
                      t.is_cheap === "YES" ? "status-pill-yes" : t.is_cheap === "NO" ? "status-pill-no" : "status-pill-normal"
                    }`}
                    style={{ fontSize: "0.7rem", padding: "2px 8px" }}
                  >
                    {t.is_cheap}
                  </span>
                </td>
                <td>₹{t.fixed_amount}</td>
                <td style={{ color: t.extra_amount > 0 ? "var(--emerald)" : "var(--text-dim)", fontWeight: 700 }}>
                  +₹{t.extra_amount}
                </td>
                <td style={{ color: "var(--gold-bright)", fontWeight: 800 }}>₹{t.total_amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="disclaimer-box">
        <strong>Mandatory Disclaimer:</strong> {data.disclaimer}
      </div>
    </div>
  );
}
