import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const badge = (label, color) => (
  <span
    style={{
      background: color,
      color: "#fff",
      borderRadius: 4,
      padding: "2px 8px",
      fontSize: 11,
      fontWeight: 700,
      marginLeft: 6,
    }}
  >
    {label}
  </span>
);

const SectionHeader = ({ title, count, accent }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      margin: "18px 0 8px",
      borderBottom: `2px solid ${accent}`,
      paddingBottom: 6,
    }}
  >
    <span style={{ fontWeight: 700, fontSize: 14, color: accent }}>{title}</span>
    <span
      style={{
        background: accent,
        color: "#fff",
        borderRadius: 10,
        padding: "1px 8px",
        fontSize: 12,
        fontWeight: 700,
      }}
    >
      {count}
    </span>
  </div>
);

const Card = ({ children, style = {} }) => (
  <div
    style={{
      background: "#1e2330",
      border: "1px solid #2a2f3e",
      borderRadius: 8,
      padding: "10px 14px",
      marginBottom: 8,
      fontSize: 13,
      ...style,
    }}
  >
    {children}
  </div>
);

export default function RadarPanel({ token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchRadar = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/radar/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRadar();
    // auto-refresh every 60 seconds
    const interval = setInterval(fetchRadar, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading)
    return (
      <div style={{ padding: 24, color: "#888", fontSize: 13 }}>
        Loading radar...
      </div>
    );

  if (error)
    return (
      <div style={{ padding: 24, color: "#f87171", fontSize: 13 }}>
        Radar error: {error}
      </div>
    );

  const { sla, clusters, stuck_orders } = data;
  const totalAlerts = sla.breached + sla.at_risk + clusters.incidents_detected + stuck_orders.total;

  return (
    <div
      style={{
        padding: "16px",
        overflowY: "auto",
        height: "100%",
        fontFamily: "inherit",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 4,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 15, fontWeight: 700, color: "#e2e8f0" }}>
            🛰 Issue Radar
          </span>
          {totalAlerts > 0 && badge(`${totalAlerts} alerts`, "#dc2626")}
        </div>
        <button
          onClick={fetchRadar}
          style={{
            background: "transparent",
            border: "1px solid #3a3f50",
            color: "#94a3b8",
            borderRadius: 4,
            padding: "3px 10px",
            fontSize: 11,
            cursor: "pointer",
          }}
        >
          ↺ Refresh
        </button>
      </div>
      {lastRefresh && (
        <div style={{ fontSize: 10, color: "#4b5563", marginBottom: 12 }}>
          Last updated: {lastRefresh} · auto-refreshes every 60s
        </div>
      )}

      {totalAlerts === 0 && (
        <div
          style={{
            textAlign: "center",
            color: "#22c55e",
            padding: "32px 0",
            fontSize: 13,
          }}
        >
          ✅ All clear — no active alerts
        </div>
      )}

      {/* ── SLA BREACHES ── */}
      {(sla.breached > 0 || sla.at_risk > 0) && (
        <>
          <SectionHeader
            title="SLA Alerts"
            count={sla.breached + sla.at_risk}
            accent="#dc2626"
          />
          {sla.items.map((t) => (
            <Card key={t.ticket_id}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 4,
                }}
              >
                <span style={{ fontWeight: 600, color: "#e2e8f0" }}>
                  {t.ticket_id}
                </span>
                <span>
                  {t.alert === "BREACHED"
                    ? badge("BREACHED", "#dc2626")
                    : badge("AT RISK", "#f59e0b")}
                  {badge(t.priority, "#6366f1")}
                </span>
              </div>
              <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 4 }}>
                {t.description}
              </div>
              <div style={{ display: "flex", gap: 16, fontSize: 11, color: "#64748b" }}>
                <span>Account: {t.account_id}</span>
                <span>
                  {t.hours_remaining < 0
                    ? `Overdue by ${Math.abs(t.hours_remaining).toFixed(1)}h`
                    : `${t.hours_remaining}h remaining`}
                </span>
              </div>
            </Card>
          ))}
        </>
      )}

      {/* ── INCIDENT CLUSTERS ── */}
      {clusters.incidents_detected > 0 && (
        <>
          <SectionHeader
            title="Incident Clusters"
            count={clusters.incidents_detected}
            accent="#f59e0b"
          />
          {clusters.items.map((c) => (
            <Card key={c.cluster}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 6,
                }}
              >
                <span style={{ fontWeight: 600, color: "#e2e8f0" }}>
                  {c.cluster}
                </span>
                {badge(`${c.ticket_count} tickets`, "#f59e0b")}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {c.tickets.map((t) => (
                  <span
                    key={t.ticket_id}
                    style={{
                      background: "#2a2f3e",
                      borderRadius: 4,
                      padding: "2px 7px",
                      fontSize: 11,
                      color: "#94a3b8",
                    }}
                  >
                    {t.ticket_id} · {t.account_id}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </>
      )}

      {/* ── STUCK ORDERS ── */}
      {stuck_orders.total > 0 && (
        <>
          <SectionHeader
            title="Stuck Orders (BOOKED)"
            count={stuck_orders.total}
            accent="#8b5cf6"
          />
          {stuck_orders.items.map((o) => (
            <Card key={o.order_id}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 4,
                }}
              >
                <span style={{ fontWeight: 600, color: "#e2e8f0" }}>
                  {o.order_id}
                </span>
                {badge("STUCK", "#8b5cf6")}
              </div>
              <div style={{ display: "flex", gap: 16, fontSize: 11, color: "#64748b" }}>
                <span>Account: {o.account_id}</span>
                <span>Carrier: {o.carrier || "Unknown"}</span>
                <span>
                  {o.hours_in_booked === "unknown"
                    ? "Age unknown"
                    : `Stuck ${o.hours_in_booked}h`}
                </span>
              </div>
            </Card>
          ))}
        </>
      )}
    </div>
  );
}