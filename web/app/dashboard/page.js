"use client";
import { useEffect, useState } from "react";
export default function Dashboard() {
  const [m, setM] = useState({ bookings: 0, revenue_usd: 0, calls: 0, handoffs: 0, after_hours: 0 });
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_BRIDGE_HTTP || "http://localhost:8000";
    const es = new EventSource(`${base}/events?tenant=dental`);
    es.onmessage = (e) => setM(JSON.parse(e.data));
    return () => es.close();
  }, []);
  const Card = ({ label, value }) => (
    <div style={{ padding: 24, borderRadius: 16, background: "#0b0b12", color: "#fff", minWidth: 180 }}>
      <div style={{ fontSize: 14, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 40, fontWeight: 800 }}>{value}</div>
    </div>);
  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", padding: 32, background: "#050507", minHeight: "100vh" }}>
      <Card label="Citas agendadas" value={m.bookings} />
      <Card label="$ cobrado" value={`$${m.revenue_usd}`} />
      <Card label="Llamadas atendidas" value={m.calls} />
      <Card label="Escaladas a humano" value={m.handoffs} />
      <Card label="Capturadas fuera de horario" value={m.after_hours} />
    </div>);
}
