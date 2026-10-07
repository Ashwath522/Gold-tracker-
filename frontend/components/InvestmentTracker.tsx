"use client";

import React, { useState, useEffect, useRef } from "react";
import { InvestmentItem, ScoreReport, LatestPrice } from "@/types";
import { PlusCircle, Download, Upload, Trash2, Edit2, Check, X, Info } from "lucide-react";

interface Props {
  latestPrice: LatestPrice;
  scoreReport: ScoreReport;
  onInvestmentChanged: () => void;
}

export default function InvestmentTracker({ latestPrice, scoreReport, onInvestmentChanged }: Props) {
  const [investments, setInvestments] = useState<InvestmentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  // Form states prefilled with model recommendation
  const [formData, setFormData] = useState({
    date: new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" }),
    time_ist: new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false }),
    market_price: latestPrice.price_24k_inr,
    model_score: scoreReport.total_score,
    model_rec_fixed: scoreReport.fixed_amount,
    model_rec_extra: scoreReport.extra_amount,
    model_rec_total: scoreReport.total_amount,
    actual_amount: scoreReport.total_amount,
    gst_paid: Number((scoreReport.total_amount - scoreReport.total_amount / 1.03).toFixed(2)),
    actual_grams: "",
    notes: "PhonePe digital gold",
  });

  const [editingId, setEditingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchInvestments = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/investments");
      if (res.ok) {
        const data = await res.json();
        setInvestments(data);
      }
    } catch (err) {
      console.error("Failed to load investments", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvestments();
  }, []);

  const handleAmountChange = (val: number) => {
    const gst = Number((val - val / 1.03).toFixed(2));
    setFormData((prev) => ({
      ...prev,
      actual_amount: val,
      gst_paid: gst,
    }));
  };

  const handleSaveInvestment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        date: formData.date,
        time_ist: formData.time_ist,
        market_price: formData.market_price,
        model_score: formData.model_score,
        model_rec_fixed: formData.model_rec_fixed,
        model_rec_extra: formData.model_rec_extra,
        model_rec_total: formData.model_rec_total,
        actual_amount: Number(formData.actual_amount),
        gst_paid: formData.gst_paid ? Number(formData.gst_paid) : null,
        actual_grams: formData.actual_grams ? Number(formData.actual_grams) : null,
        notes: formData.notes || null,
      };

      if (editingId) {
        const res = await fetch(`/api/investments/${editingId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          setEditingId(null);
          setFormOpen(false);
          await fetchInvestments();
          onInvestmentChanged();
        }
      } else {
        const res = await fetch("/api/investments", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          setFormOpen(false);
          await fetchInvestments();
          onInvestmentChanged();
        }
      }
    } catch (err) {
      console.error("Error saving investment", err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this investment record?")) return;
    try {
      const res = await fetch(`/api/investments/${id}`, { method: "DELETE" });
      if (res.ok) {
        await fetchInvestments();
        onInvestmentChanged();
      }
    } catch (err) {
      console.error("Failed to delete investment", err);
    }
  };

  const handleEdit = (item: InvestmentItem) => {
    setEditingId(item.id);
    setFormData({
      date: item.date,
      time_ist: item.time_ist,
      market_price: item.market_price,
      model_score: item.model_score ?? scoreReport.total_score,
      model_rec_fixed: item.model_rec_fixed,
      model_rec_extra: item.model_rec_extra,
      model_rec_total: item.model_rec_total,
      actual_amount: item.actual_amount,
      gst_paid: item.gst_paid ?? Number((item.actual_amount - item.actual_amount / 1.03).toFixed(2)),
      actual_grams: item.is_estimated_grams ? "" : String(item.actual_grams),
      notes: item.notes || "",
    });
    setFormOpen(true);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    try {
      const res = await fetch("/api/investments/import-csv", {
        method: "POST",
        body,
      });
      if (res.ok) {
        const result = await res.json();
        alert(`Successfully imported ${result.imported_count} investment entries!`);
        await fetchInvestments();
        onInvestmentChanged();
      } else {
        alert("Failed to import CSV");
      }
    } catch (err) {
      console.error(err);
      alert("Error importing CSV file");
    }
  };

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "0.75rem" }}>
        <div>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
            Daily Investment Log (PhonePe Actuals)
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Record actual rupees invested and precise grams received from PhonePe (auto-computes true average purchase price including GST)
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => {
              setEditingId(null);
              setFormData({
                date: new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" }),
                time_ist: new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false }),
                market_price: latestPrice.price_24k_inr,
                model_score: scoreReport.total_score,
                model_rec_fixed: scoreReport.fixed_amount,
                model_rec_extra: scoreReport.extra_amount,
                model_rec_total: scoreReport.total_amount,
                actual_amount: scoreReport.total_amount,
                gst_paid: Number((scoreReport.total_amount - scoreReport.total_amount / 1.03).toFixed(2)),
                actual_grams: "",
                notes: "PhonePe digital gold",
              });
              setFormOpen(!formOpen);
            }}
          >
            <PlusCircle size={15} />
            {formOpen ? "Close Form" : "Log Today's Investment"}
          </button>

          <a href="/api/investments/export-csv" className="btn btn-secondary btn-sm" download>
            <Download size={14} /> Export CSV
          </a>

          <button className="btn btn-secondary btn-sm" onClick={() => fileInputRef.current?.click()}>
            <Upload size={14} /> Import CSV
          </button>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".csv"
            onChange={handleFileUpload}
          />
        </div>
      </div>

      {/* Form Drawer / Box */}
      {formOpen && (
        <form onSubmit={handleSaveInvestment} style={{ background: "var(--bg-surface)", border: "1px solid var(--border-gold)", padding: "1.25rem", borderRadius: "var(--radius-md)", marginBottom: "1.5rem" }}>
          <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--gold-bright)", marginBottom: "1rem" }}>
            {editingId ? "Edit Investment Entry" : "Record New Investment (Prefilled with Model Amount)"}
          </h4>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Date (YYYY-MM-DD)</label>
              <input
                type="date"
                className="form-input"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Time IST</label>
              <input
                type="text"
                className="form-input"
                value={formData.time_ist}
                onChange={(e) => setFormData({ ...formData, time_ist: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Market Rate at Purchase (₹/g)</label>
              <input
                type="number"
                step="0.01"
                className="form-input"
                value={formData.market_price}
                onChange={(e) => setFormData({ ...formData, market_price: Number(e.target.value) })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Actual Amount Invested (₹)</label>
              <input
                type="number"
                step="1"
                className="form-input"
                value={formData.actual_amount}
                onChange={(e) => handleAmountChange(Number(e.target.value))}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">3% GST Paid (₹)</label>
              <input
                type="number"
                step="0.01"
                className="form-input"
                value={formData.gst_paid || ""}
                onChange={(e) => setFormData({ ...formData, gst_paid: Number(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Actual Grams Received (From PhonePe)</label>
              <input
                type="number"
                step="0.0001"
                className="form-input"
                placeholder="Leave blank to auto-estimate"
                value={formData.actual_grams}
                onChange={(e) => setFormData({ ...formData, actual_grams: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: "1rem" }}>
            <label className="form-label">Notes</label>
            <input
              type="text"
              className="form-input"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" className="btn btn-primary btn-sm">
              <Check size={14} /> {editingId ? "Update Record" : "Save Investment"}
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setFormOpen(false);
                setEditingId(null);
              }}
            >
              <X size={14} /> Cancel
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Market Price</th>
              <th>Score</th>
              <th>Recommended</th>
              <th>Actual Invested</th>
              <th>GST</th>
              <th>Actual Grams</th>
              <th>True Cost / Gram</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {investments.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: "center", color: "var(--text-dim)", padding: "2rem" }}>
                  No investments recorded yet. Click &quot;Log Today&apos;s Investment&quot; to add your first PhonePe purchase.
                </td>
              </tr>
            ) : (
              investments.map((inv) => (
                <tr key={inv.id}>
                  <td>
                    <div><strong>{inv.date}</strong></div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>{inv.time_ist}</div>
                  </td>
                  <td>₹{inv.market_price.toLocaleString("en-IN")}</td>
                  <td>
                    {inv.model_score ? (
                      <span style={{ color: "var(--gold-bright)", fontWeight: 700 }}>
                        {inv.model_score}
                      </span>
                    ) : "—"}
                  </td>
                  <td>
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                      ₹{inv.model_rec_fixed} + ₹{inv.model_rec_extra} = 
                    </span>{" "}
                    <strong>₹{inv.model_rec_total}</strong>
                  </td>
                  <td style={{ fontWeight: 700, color: "var(--text-main)" }}>
                    ₹{inv.actual_amount}
                  </td>
                  <td style={{ color: "var(--text-dim)" }}>
                    {inv.gst_paid ? `₹${inv.gst_paid}` : "—"}
                  </td>
                  <td>
                    <strong>{inv.actual_grams.toFixed(4)}g</strong>
                    {inv.is_estimated_grams && (
                      <span style={{ fontSize: "0.7rem", color: "var(--amber)", marginLeft: "0.3rem" }}>
                        (est.)
                      </span>
                    )}
                  </td>
                  <td style={{ color: "var(--gold-bright)", fontWeight: 700 }}>
                    ₹{inv.avg_purchase_price.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>{inv.notes || "—"}</td>
                  <td>
                    <div style={{ display: "flex", gap: "0.4rem" }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ padding: "4px 8px" }}
                        onClick={() => handleEdit(inv)}
                        title="Edit"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ padding: "4px 8px", color: "var(--rose)" }}
                        onClick={() => handleDelete(inv.id)}
                        title="Delete"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
