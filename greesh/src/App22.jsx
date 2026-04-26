import { useState, useCallback } from "react";
import axios from "axios";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";

const API_URL = "http://localhost:8000";

// ── Helpers ────────────────────────────────────────────────────────────────

function parseInsight(text) {
  const [label, ...rest] = text.split(": ");
  return { label, value: rest.join(": ") };
}

function monthlyToChartData(monthly) {
  return Object.entries(monthly)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, revenue]) => ({ month: month.replace("-", " "), revenue }));
}

const fmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

// ── Icon components ────────────────────────────────────────────────────────

function Icon({ name, size = 16 }) {
  const icons = {
    alert: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    ),
    trend_down: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>
      </svg>
    ),
    trend_up: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
      </svg>
    ),
    marketing: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    ),
    lightbulb: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/>
        <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
      </svg>
    ),
    target: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
      </svg>
    ),
    star: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
    ),
    zap: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
      </svg>
    ),
  };
  return <span className="icon">{icons[name] || null}</span>;
}

// Anomaly type → icon + colour class
function anomalyMeta(type) {
  switch (type) {
    case "Revenue Drop":     return { icon: "trend_down", cls: "anom-red" };
    case "Revenue Spike":    return { icon: "trend_up",   cls: "anom-amber" };
    case "Marketing Spike":  return { icon: "marketing",  cls: "anom-orange" };
    default:                 return { icon: "alert",      cls: "anom-red" };
  }
}

function recMeta(type) {
  switch (type) {
    case "Marketing Investment": return { icon: "zap",       cls: "rec-blue" };
    case "Campaign Efficiency":  return { icon: "target",    cls: "rec-purple" };
    case "Region Strategy":      return { icon: "lightbulb", cls: "rec-teal" };
    case "Scale Success":        return { icon: "star",      cls: "rec-green" };
    case "Revenue Trend":        return { icon: "trend_down",cls: "rec-amber" };
    default:                     return { icon: "lightbulb", cls: "rec-blue" };
  }
}

// ── Sub-components ──────────────────────────────────────────────────────────

function UploadZone({ onFile, loading }) {
  const [dragging, setDragging] = useState(false);
  const handleDrop = useCallback((e) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }, [onFile]);

  return (
    <div
      className={`upload-zone ${dragging ? "dragging" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      {loading ? (
        <div className="upload-loading">
          <div className="spinner" />
          <span>Running analysis + anomaly detection…</span>
        </div>
      ) : (
        <>
          <div className="upload-icon">📊</div>
          <p className="upload-title">Drop your CSV here</p>
          <p className="upload-sub">or click to browse</p>
          <label className="upload-btn">
            Choose File
            <input type="file" accept=".csv" hidden onChange={(e) => e.target.files[0] && onFile(e.target.files[0])} />
          </label>
          <p className="upload-hint">Required columns: Date · Region · Product · Revenue · Cost · Marketing</p>
        </>
      )}
    </div>
  );
}

function InsightCard({ label, value, accent }) {
  return (
    <div className="insight-card" style={{ "--accent": accent }}>
      <span className="insight-label">{label}</span>
      <span className="insight-value">{value}</span>
    </div>
  );
}

function AnomalyCard({ anomaly }) {
  const { icon, cls } = anomalyMeta(anomaly.type);
  return (
    <div className={`signal-card ${cls}`}>
      <div className="signal-header">
        <span className={`signal-icon ${cls}-icon`}><Icon name={icon} size={14} /></span>
        <span className="signal-type">{anomaly.type}</span>
        <span className={`signal-badge severity-${anomaly.severity}`}>{anomaly.severity}</span>
        {anomaly.region !== "All Regions" && <span className="signal-region">{anomaly.region}</span>}
      </div>
      <p className="signal-desc">{anomaly.description}</p>
      <div className="signal-meta">
        <span className="meta-pill">{anomaly.period}</span>
        {anomaly.value && <span className="meta-pill">${Number(anomaly.value).toLocaleString()}</span>}
        <span className="meta-pill">z={anomaly.z_score}</span>
      </div>
    </div>
  );
}

function RecommendationCard({ rec }) {
  const { icon, cls } = recMeta(rec.type);
  return (
    <div className={`signal-card ${cls}`}>
      <div className="signal-header">
        <span className={`signal-icon ${cls}-icon`}><Icon name={icon} size={14} /></span>
        <span className="signal-type">{rec.type}</span>
        <span className={`signal-badge priority-${rec.priority}`}>{rec.priority}</span>
        {rec.region !== "All Regions" && <span className="signal-region">{rec.region}</span>}
      </div>
      <p className="signal-title-text">{rec.title}</p>
      <p className="signal-desc">{rec.description}</p>
      <div className="signal-action">
        <span className="action-arrow">→</span> {rec.action}
      </div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      <p className="tooltip-value">{fmt.format(payload[0].value)}</p>
    </div>
  );
}

function SectionHeader({ title, count, countColor }) {
  return (
    <div className="section-header">
      <h3 className="section-title">{title}</h3>
      {count !== undefined && (
        <span className="section-badge" style={{ "--badge-color": countColor }}>{count}</span>
      )}
    </div>
  );
}

// ── Main App ────────────────────────────────────────────────────────────────

export default function App() {
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [data, setData]         = useState(null);
  const [fileName, setFileName] = useState(null);

  const accents = ["#6ee7b7","#93c5fd","#fcd34d","#f9a8d4","#a5b4fc","#fdba74","#67e8f9","#d9f99d","#c4b5fd","#fca5a5"];

  const handleFile = async (file) => {
    setLoading(true); setError(null); setData(null); setFileName(file.name);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await axios.post(`${API_URL}/upload`, form, { headers: { "Content-Type": "multipart/form-data" } });
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const chartData     = data ? monthlyToChartData(data.monthly_revenue) : [];
  const anomalies     = data?.anomalies     ?? [];
  const recommendations = data?.recommendations ?? [];

  // find anomalous months for reference lines on chart
  const anomalyMonths = new Set(
    anomalies.filter(a => a.type === "Revenue Drop" || a.type === "Revenue Spike")
             .map(a => a.period.replace("-", " "))
  );

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-mark">▲</span>
            <span className="logo-text">Analytic<em>s</em></span>
            <span className="version-tag">v2</span>
          </div>
          {fileName && !loading && (
            <button className="reset-btn" onClick={() => { setData(null); setError(null); setFileName(null); }}>
              ↩ New File
            </button>
          )}
        </div>
      </header>

      <main className="main">
        {!data ? (
          <div className="landing">
            <h1 className="hero-title">Decision<br/>Intelligence</h1>
            <p className="hero-sub">Upload a CSV → get insights, anomaly alerts, and strategic recommendations.</p>
            <div className="feature-pills">
              <span className="pill pill-green">Revenue Insights</span>
              <span className="pill pill-red">Anomaly Detection</span>
              <span className="pill pill-blue">Recommendations</span>
            </div>
            <UploadZone onFile={handleFile} loading={loading} />
            {error && <div className="error-banner">⚠ {error}</div>}
          </div>
        ) : (
          <div className="dashboard">
            <div className="dash-header">
              <h2 className="dash-title">Dashboard</h2>
              <div className="dash-meta">
                <span className="dash-file">📁 {fileName}</span>
                {anomalies.length > 0 && (
                  <span className="dash-alert-count">⚠ {anomalies.length} alert{anomalies.length > 1 ? "s" : ""}</span>
                )}
              </div>
            </div>

            {/* ── KPI Grid ── */}
            <div className="insights-grid">
              {data.insights.map((ins, i) => {
                const { label, value } = parseInsight(ins);
                return <InsightCard key={i} label={label} value={value} accent={accents[i % accents.length]} />;
              })}
            </div>

            {/* ── Chart ── */}
            <div className="chart-card">
              <h3 className="chart-title">Monthly Revenue</h3>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="revGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#6ee7b7" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6ee7b7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="month" tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false}
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip content={<CustomTooltip />} />
                  {chartData.map((d) =>
                    anomalyMonths.has(d.month) ? (
                      <ReferenceLine key={d.month} x={d.month} stroke="rgba(248,113,113,0.4)"
                        strokeDasharray="4 3" strokeWidth={1.5} />
                    ) : null
                  )}
                  <Area type="monotone" dataKey="revenue" stroke="#6ee7b7" strokeWidth={2.5}
                    fill="url(#revGradient)"
                    dot={{ fill: "#6ee7b7", r: 4, strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: "#fff", stroke: "#6ee7b7", strokeWidth: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
              {anomalyMonths.size > 0 && (
                <p className="chart-legend-note">
                  <span className="legend-line" /> Red lines mark anomalous months
                </p>
              )}
            </div>

            {/* ── Two-column signals panel ── */}
            <div className="signals-grid">

              {/* Alerts */}
              <div className="signals-col">
                <SectionHeader
                  title="⚠ Alerts"
                  count={anomalies.length}
                  countColor="#f87171"
                />
                {anomalies.length === 0 ? (
                  <div className="empty-state green">
                    <span>✓ No anomalies detected</span>
                  </div>
                ) : (
                  <div className="signals-list">
                    {anomalies.map((a, i) => <AnomalyCard key={i} anomaly={a} />)}
                  </div>
                )}
              </div>

              {/* Recommendations */}
              <div className="signals-col">
                <SectionHeader
                  title="💡 Recommendations"
                  count={recommendations.length}
                  countColor="#93c5fd"
                />
                {recommendations.length === 0 ? (
                  <div className="empty-state">
                    <span>No recommendations at this time</span>
                  </div>
                ) : (
                  <div className="signals-list">
                    {recommendations.map((r, i) => <RecommendationCard key={i} rec={r} />)}
                  </div>
                )}
              </div>

            </div>
          </div>
        )}
      </main>
    </div>
  );
}
