"use client";

import React, { useState } from "react";
import { AnalysisPayload, PricePoint } from "@/types";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid
} from "recharts";
import { TrendingUp, Activity, BarChart2, ShieldAlert } from "lucide-react";

interface Props {
  analysisData: AnalysisPayload;
  historyPoints: PricePoint[];
}

export default function ChartsSection({ analysisData, historyPoints }: Props) {
  const [selectedWindow, setSelectedWindow] = useState<"30" | "60" | "90">("90");

  const windowDays = parseInt(selectedWindow, 10);
  const metrics = analysisData.analysis.windows[selectedWindow];
  const volatility = analysisData.analysis.volatility;
  const momentum = analysisData.analysis.momentum;

  // Filter history points to window length
  const chartSlice = historyPoints.slice(-windowDays).map((pt) => ({
    date: pt.date.slice(5), // MM-DD
    price: pt.price_24k_inr,
  }));

  // Append latest price point if not already present
  const latestDate = analysisData.latest_price.source_timestamp.slice(5, 10);
  if (chartSlice.length > 0 && chartSlice[chartSlice.length - 1].date !== latestDate) {
    chartSlice.push({
      date: "Today",
      price: analysisData.latest_price.price_24k_inr,
    });
  }

  // Rate of change for selected window
  const roc = selectedWindow === "30" 
    ? momentum.roc_30d_pct 
    : selectedWindow === "60" 
    ? momentum.roc_60d_pct 
    : momentum.roc_90d_pct;

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
            Price Trajectory & Range Analysis
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Tracking current price relative to {selectedWindow}-day highs, lows, and moving averages
          </p>
        </div>

        {/* Window Selector Tabs */}
        <div className="karat-toggle">
          <button
            className={`karat-btn ${selectedWindow === "30" ? "active" : ""}`}
            onClick={() => setSelectedWindow("30")}
          >
            30 Days
          </button>
          <button
            className={`karat-btn ${selectedWindow === "60" ? "active" : ""}`}
            onClick={() => setSelectedWindow("60")}
          >
            60 Days
          </button>
          <button
            className={`karat-btn ${selectedWindow === "90" ? "active" : ""}`}
            onClick={() => setSelectedWindow("90")}
          >
            90 Days
          </button>
        </div>
      </div>

      {metrics?.is_partial && (
        <div style={{ fontSize: "0.775rem", color: "var(--amber)", marginBottom: "1rem" }}>
          * Notice: Window includes {metrics.actual_days} available trading days. Metrics adapted gracefully.
        </div>
      )}

      {/* Visual Range Position Bar */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", color: "var(--text-muted)" }}>
          <span>90D Low: <strong>₹{metrics?.low?.toLocaleString("en-IN")}</strong></span>
          <span style={{ color: "var(--gold-bright)", fontWeight: 700 }}>
            Range Position: {metrics?.range_position}% ({metrics?.range_position < 35 ? "Lower Range (Attractive)" : metrics?.range_position > 65 ? "Upper Range (Heated)" : "Mid Range"})
          </span>
          <span>90D High: <strong>₹{metrics?.high?.toLocaleString("en-IN")}</strong></span>
        </div>
        <div className="range-bar-track">
          <div className="range-bar-fill" style={{ width: "100%" }} />
          <div
            className="range-bar-pin"
            style={{ left: `${Math.max(0, Math.min(100, metrics?.range_position || 50))}%` }}
          />
        </div>
      </div>

      {/* Chart */}
      <div style={{ width: "100%", height: 320, marginTop: "1rem" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartSlice} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#232a3a" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis
              domain={["dataMin - 100", "dataMax + 100"]}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => `₹${Math.round(v)}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#171d2b",
                borderColor: "#2e374c",
                borderRadius: "8px",
                color: "#f8fafc",
                fontSize: "12px",
                boxShadow: "0 4px 15px rgba(0,0,0,0.5)"
              }}
              formatter={(value: any) => [`₹${Number(value).toFixed(2)}/g`, "Price"]}
            />
            {metrics?.average && (
              <ReferenceLine
                y={metrics.average}
                stroke="#38bdf8"
                strokeDasharray="4 4"
                label={{ value: `SMA: ₹${metrics.average}`, fill: "#38bdf8", fontSize: 10, position: "insideBottomRight" }}
              />
            )}
            {metrics?.high && (
              <ReferenceLine
                y={metrics.high}
                stroke="#f43f5e"
                strokeDasharray="2 2"
                label={{ value: `High: ₹${metrics.high}`, fill: "#f43f5e", fontSize: 10, position: "insideTopRight" }}
              />
            )}
            {metrics?.low && (
              <ReferenceLine
                y={metrics.low}
                stroke="#10b981"
                strokeDasharray="2 2"
                label={{ value: `Low: ₹${metrics.low}`, fill: "#10b981", fontSize: 10, position: "insideBottomLeft" }}
              />
            )}
            <Line
              type="monotone"
              dataKey="price"
              stroke="#e6af2e"
              strokeWidth={2.5}
              dot={{ r: 2, fill: "#e6af2e" }}
              activeDot={{ r: 5, fill: "#ffd15c" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics Summary Grid */}
      <div className="metrics-grid">
        <div className="metric-tile">
          <span className="metric-tile-title">Window Average (SMA)</span>
          <span className="metric-tile-val">₹{metrics?.average?.toLocaleString("en-IN")}</span>
          <span style={{ fontSize: "0.75rem", color: metrics?.distance_from_sma_pct < 0 ? "var(--emerald)" : "var(--rose)" }}>
            {metrics?.distance_from_sma_pct > 0 ? "+" : ""}{metrics?.distance_from_sma_pct}% from SMA
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-title">Drawdown From High</span>
          <span className="metric-tile-val" style={{ color: "var(--rose)" }}>
            {metrics?.drawdown_pct}%
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
            Peak was ₹{metrics?.high?.toLocaleString("en-IN")}
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-title">Percentile Rank</span>
          <span className="metric-tile-val" style={{ color: "var(--gold-bright)" }}>
            {metrics?.percentile_rank}%
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
            Cheaper than {100 - (metrics?.percentile_rank || 0)}% of days
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-title">Rate Of Change (ROC)</span>
          <span className="metric-tile-val" style={{ color: (roc || 0) <= 0 ? "var(--emerald)" : "var(--amber)" }}>
            {roc !== null && roc !== undefined ? `${roc > 0 ? "+" : ""}${roc}%` : "N/A"}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
            Anti-spike momentum
          </span>
        </div>

        <div className="metric-tile">
          <span className="metric-tile-title">Volatility Classification</span>
          <span className="metric-tile-val" style={{ color: volatility.label === "Low" ? "var(--emerald)" : volatility.label === "Medium" ? "var(--amber)" : "var(--rose)" }}>
            {volatility.label}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
            {volatility.annualized_volatility_pct}% Annualized
          </span>
        </div>
      </div>
    </div>
  );
}
