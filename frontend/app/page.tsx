"use client";

import React, { useState, useEffect } from "react";
import { AnalysisPayload, PricePoint } from "@/types";
import TopSection from "@/components/TopSection";
import ChartsSection from "@/components/ChartsSection";
import ValuationBreakdown from "@/components/ValuationBreakdown";
import InvestmentTracker from "@/components/InvestmentTracker";
import PortfolioView from "@/components/PortfolioView";
import BacktestView from "@/components/BacktestView";
import ModelExplanationTab from "@/components/ModelExplanationTab";
import {
  Coins,
  LineChart as ChartIcon,
  Sliders,
  Wallet,
  BookOpen,
  PieChart,
  RefreshCw,
  Layers
} from "lucide-react";

export default function HomePage() {
  const [data, setData] = useState<AnalysisPayload | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"charts" | "valuation" | "tracker" | "portfolio" | "backtest" | "explanation">("charts");
  const [portfolioTrigger, setPortfolioTrigger] = useState(0);

  const fetchAnalysisData = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) setRefreshing(true);
      else setLoading(true);

      setError(null);
      const url = forceRefresh ? "/api/analysis?force_refresh=true" : "/api/analysis";
      const [resAnalysis, resHistory] = await Promise.all([
        fetch(url),
        fetch("/api/prices/history?days=120"),
      ]);

      if (resAnalysis.ok) {
        const analysisJson = await resAnalysis.json();
        setData(analysisJson);
      } else {
        const responseText = await resAnalysis.text();
        let detail: { detail?: string } | null = null;
        try {
          detail = JSON.parse(responseText);
        } catch {
          // Keep the first part of non-JSON proxy errors visible to make deployment issues diagnosable.
        }
        const fallback = responseText.replace(/<[^>]*>/g, " ").trim().slice(0, 200);
        const hint = responseText.trim().startsWith("<")
          ? " Check BACKEND_URL and the backend deployment health endpoint."
          : "";
        setError(
          detail?.detail ||
            (fallback
              ? `Analysis request failed (${resAnalysis.status}): ${fallback}${hint}`
              : `Analysis request failed (${resAnalysis.status}).${hint}`),
        );
      }
      if (resHistory.ok) {
        const historyJson = await resHistory.json();
        setHistory(historyJson);
      }
    } catch (err) {
      console.error("Failed to load dashboard data", err);
      setError("Cannot reach the backend. Is it running on port 8000?");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalysisData(false);
  }, []);

  const handleRefresh = () => {
    fetchAnalysisData(true);
  };

  const handleInvestmentChanged = () => {
    setPortfolioTrigger((prev) => prev + 1);
  };

  if (!loading && !data) {
    return (
      <div className="container" style={{ textAlign: "center", paddingTop: "6rem" }}>
        <h2 style={{ fontSize: "1.25rem", color: "var(--rose)", fontWeight: 700 }}>
          Could not load dashboard
        </h2>
        <p style={{ color: "var(--text-dim)", fontSize: "0.85rem", margin: "0.75rem 0 1.25rem" }}>
          {error || "Unknown error"}
        </p>
        <button className="btn btn-primary btn-sm" onClick={() => fetchAnalysisData(false)}>
          Retry
        </button>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="container" style={{ textAlign: "center", paddingTop: "6rem" }}>
        <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
          <div className="brand-icon" style={{ width: 56, height: 56 }}>
            <Coins size={32} color="#0b0d13" />
          </div>
          <h2 style={{ fontSize: "1.25rem", color: "var(--gold-bright)", fontWeight: 700 }}>
            Analyzing Gold Valuation Engine...
          </h2>
          <p style={{ color: "var(--text-dim)", fontSize: "0.85rem" }}>
            Evaluating recent 30/60/90D ranges and technical momentum
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* App Header */}
      <header className="app-header">
        <div className="brand-wrapper">
          <div className="brand-icon">
            <Coins size={24} color="#0b0d13" />
          </div>
          <div>
            <h1 className="brand-title">Gold Daily Analysis</h1>
            <p className="brand-subtitle">
              Disciplined Daily Accumulation System • ₹35 Base + Opportunistic Dip Sizing
            </p>
          </div>
        </div>

        <div className="header-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={14} className={refreshing ? "spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh Feed"}
          </button>
        </div>
      </header>

      {/* Main Top Section */}
      <TopSection
        latest={data.latest_price}
        scoreReport={data.score_report}
        onRefresh={handleRefresh}
        refreshing={refreshing}
      />

      {/* Navigation Tabs */}
      <nav className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === "charts" ? "active" : ""}`}
          onClick={() => setActiveTab("charts")}
        >
          <ChartIcon size={16} /> Price Charts
        </button>
        <button
          className={`tab-btn ${activeTab === "valuation" ? "active" : ""}`}
          onClick={() => setActiveTab("valuation")}
        >
          <Sliders size={16} /> Valuation Breakdown
        </button>
        <button
          className={`tab-btn ${activeTab === "tracker" ? "active" : ""}`}
          onClick={() => setActiveTab("tracker")}
        >
          <Wallet size={16} /> Investment Tracker
        </button>
        <button
          className={`tab-btn ${activeTab === "portfolio" ? "active" : ""}`}
          onClick={() => setActiveTab("portfolio")}
        >
          <PieChart size={16} /> Portfolio View
        </button>
        <button
          className={`tab-btn ${activeTab === "backtest" ? "active" : ""}`}
          onClick={() => setActiveTab("backtest")}
        >
          <Layers size={16} /> Backtest Simulator
        </button>
        <button
          className={`tab-btn ${activeTab === "explanation" ? "active" : ""}`}
          onClick={() => setActiveTab("explanation")}
        >
          <BookOpen size={16} /> Model Explanation
        </button>
      </nav>

      {/* Tab Panels */}
      {activeTab === "charts" && (
        <ChartsSection analysisData={data} historyPoints={history} />
      )}

      {activeTab === "valuation" && (
        <ValuationBreakdown scoreReport={data.score_report} />
      )}

      {activeTab === "tracker" && (
        <InvestmentTracker
          latestPrice={data.latest_price}
          scoreReport={data.score_report}
          onInvestmentChanged={handleInvestmentChanged}
        />
      )}

      {activeTab === "portfolio" && (
        <PortfolioView refreshTrigger={portfolioTrigger} />
      )}

      {activeTab === "backtest" && (
        <BacktestView />
      )}

      {activeTab === "explanation" && (
        <ModelExplanationTab />
      )}
    </div>
  );
}
