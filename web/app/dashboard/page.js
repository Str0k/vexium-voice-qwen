"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Logo from "../Logo";
import { dict } from "../i18n";
import { resolveHttpBase } from "../bridge";

const EMPTY = {
  bookings: 0, revenue_usd: 0, deposits_pending_usd: 0, calls: 0, handoffs: 0,
  after_hours: 0, reminders_sent: 0, scored_calls: 0,
  avg_task_completion: null, avg_tool_accuracy: null, hallucinations: 0,
};

const FEED_ICONS = {
  call_handled: "📞", booking_made: "📅", deposit_pending: "💳",
  deposit_collected: "💰", handoff: "🤝", after_hours: "🌙",
  reminder_sent: "⏰", call_scored: "🧪",
};

function timeAgo(ts, lang) {
  if (!ts) return "";
  const s = Math.max(0, Math.round((Date.now() - ts) / 1000));
  if (s < 60) return lang === "es" ? `hace ${s}s` : `${s}s ago`;
  const m = Math.round(s / 60);
  if (m < 60) return lang === "es" ? `hace ${m} min` : `${m}m ago`;
  const h = Math.round(m / 60);
  return lang === "es" ? `hace ${h} h` : `${h}h ago`;
}

function eventDetail(e) {
  if (e.type === "booking_made" && e.service) return e.service;
  if ((e.type === "deposit_pending" || e.type === "deposit_collected") && e.amount_usd != null)
    return `$${e.amount_usd}`;
  if (e.type === "handoff" && e.reason) return e.reason;
  if (e.type === "call_handled" && e.turns != null) return `${e.turns} turns`;
  if (e.type === "call_scored")
    return `task ${e.task_completion ?? "–"} · tools ${e.tool_accuracy ?? "–"}${e.hallucination ? " · ⚠️" : ""}`;
  return "";
}

function Kpi({ label, value, glow }) {
  return (
    <div className="dash-kpi">
      <span key={String(value)} className={`dash-kpi-v ${glow ? "glow-blue" : "metal"}`}>{value}</span>
      <span className="dash-kpi-k">{label}</span>
    </div>
  );
}

function Meter({ label, value }) {
  const pct = typeof value === "number" ? Math.max(0, Math.min(100, value)) : 0;
  return (
    <div className="dash-meter">
      <div className="dash-meter-head">
        <span>{label}</span>
        <b>{typeof value === "number" ? `${pct}%` : "—"}</b>
      </div>
      <div className="dash-meter-track" role="img" aria-label={`${label}: ${typeof value === "number" ? pct + "%" : "n/a"}`}>
        <div className="dash-meter-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function StackRow({ item, t }) {
  // The server declares each service's state (on|fallback|simulated|offline);
  // the UI just renders the fact.
  const state = item.state || (item.connected ? "on" : "offline");
  const label = { on: t.stack.on, fallback: t.stack.fallback, simulated: t.stack.off }[state] || t.stack.offline;
  const dot = state === "on" ? "on" : state === "fallback" ? "fallback" : "off";
  return (
    <div className={`dash-svc ${item.alibaba ? "alibaba" : ""}`}>
      <span className={`dash-dot ${dot}`} aria-hidden="true" />
      <span className="dash-svc-name">{item.provider}</span>
      <span className={`dash-svc-state ${dot}`}>{label}</span>
    </div>
  );
}

export default function Dashboard() {
  const [lang, setLang] = useState("en");
  const [tenant, setTenant] = useState("dental");
  const [m, setM] = useState(EMPTY);
  const [conn, setConn] = useState("connecting"); // connecting | live
  const [feed, setFeed] = useState([]);
  const [stack, setStack] = useState([]);
  const t = dict[lang].dash;
  const tenantNames = dict[lang].demos.options;

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  // Live KPIs over SSE (the bridge pushes a fresh summary every 2s).
  useEffect(() => {
    const base = resolveHttpBase();
    const es = new EventSource(`${base}/events?tenant=${encodeURIComponent(tenant)}`);
    es.onopen = () => setConn("live");
    es.onerror = () => setConn("connecting"); // EventSource auto-reconnects
    es.onmessage = (e) => {
      try { setM({ ...EMPTY, ...JSON.parse(e.data) }); } catch {}
    };
    return () => es.close();
  }, [tenant]);

  // Activity feed: light polling (skipped while the tab is hidden).
  useEffect(() => {
    const base = resolveHttpBase();
    let stop = false;
    async function load() {
      if (document.hidden) return;
      try {
        const r = await fetch(`${base}/feed?tenant=${encodeURIComponent(tenant)}`);
        if (!r.ok) return;
        const data = await r.json();
        if (!stop) setFeed(data.events || []);
      } catch {}
    }
    load();
    const id = setInterval(load, 4000);
    return () => { stop = true; clearInterval(id); };
  }, [tenant]);

  // Integration status (once per mount — env-level truth, not per-tenant).
  useEffect(() => {
    const base = resolveHttpBase();
    fetch(`${base}/status`)
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => {
        if (!s) return;
        setStack([s.brain, s.store, s.sms, s.voice, s.tts, s.calendar, s.payments].filter(Boolean));
      })
      .catch(() => {});
  }, []);

  return (
    <div className="wrap dash">
      <nav className="nav">
        <Link className="brand" href="/" aria-label="Vexium AI">
          <Logo size={34} />
          <span className="word metal">VEXIUM&nbsp;AI</span>
        </Link>
        <div className="nav-right">
          <span className={`dash-live ${conn}`}>
            <span className="live" aria-hidden="true" />
            {conn === "live" ? t.live : t.connecting}
          </span>
          <div className="lang" role="group" aria-label="Language">
            <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
            <button className={lang === "es" ? "on" : ""} onClick={() => setLang("es")}>ES</button>
          </div>
        </div>
      </nav>

      <header className="dash-head">
        <div>
          <h1 className="dash-title"><span className="metal">{t.title}</span></h1>
          <p className="dash-sub">{t.sub}</p>
        </div>
        <div className="dash-tenants" role="group" aria-label={t.tenantLabel}>
          <span className="demos-label">{t.tenantLabel}</span>
          {tenantNames.map((o) => (
            <button
              type="button" key={o.id}
              className={`chip pick ${o.id === tenant ? "on" : ""}`}
              onClick={() => {
                if (tenant === o.id) return;
                setTenant(o.id);
                setConn("connecting");
                setM(EMPTY);
                setFeed([]);
              }}
              aria-pressed={o.id === tenant}
            >
              {o.name}
            </button>
          ))}
        </div>
      </header>

      <section className="dash-kpis" aria-label="KPIs">
        <Kpi label={t.kpis.calls} value={m.calls} glow />
        <Kpi label={t.kpis.bookings} value={m.bookings} glow />
        <Kpi label={t.kpis.pending} value={`$${Math.round(m.deposits_pending_usd)}`} />
        <Kpi label={t.kpis.revenue} value={`$${Math.round(m.revenue_usd)}`} />
        <Kpi label={t.kpis.handoffs} value={m.handoffs} />
        <Kpi label={t.kpis.afterHours} value={m.after_hours} />
        <Kpi label={t.kpis.reminders} value={m.reminders_sent} />
      </section>

      <div className="dash-grid">
        <section className="dash-card" aria-label={t.judge.title}>
          <div className="dash-card-head">
            <h2>{t.judge.title}</h2>
            <span className="dash-tag">qwen3-max</span>
          </div>
          <p className="dash-card-sub">{t.judge.sub}</p>
          {m.scored_calls > 0 ? (
            <>
              <Meter label={t.judge.task} value={m.avg_task_completion} />
              <Meter label={t.judge.tools} value={m.avg_tool_accuracy} />
              <div className="dash-judge-foot">
                <span><b>{m.hallucinations}</b> {t.judge.hallucinations}</span>
                <span><b>{m.scored_calls}</b> {t.judge.scored}</span>
              </div>
            </>
          ) : (
            <p className="dash-empty">{t.judge.none}</p>
          )}
        </section>

        <section className="dash-card" aria-label={t.stack.title}>
          <div className="dash-card-head">
            <h2>{t.stack.title}</h2>
            <span className="dash-tag alibaba">Alibaba Cloud</span>
          </div>
          <p className="dash-card-sub">{t.stack.sub}</p>
          <div className="dash-stack">
            {stack.map((item, i) => (
              <StackRow key={i} item={item} t={t} />
            ))}
          </div>
        </section>
      </div>

      <section className="dash-card dash-pipe-card" aria-label={t.pipeline.title}>
        <div className="dash-card-head"><h2>{t.pipeline.title}</h2></div>
        <div className="dash-pipe">
          {t.pipeline.nodes.map((n, i) => (
            <div className="dash-node-wrap" key={n}>
              <div className={`dash-node ${i === 2 ? "brain" : ""}`}>{n}</div>
              {i < t.pipeline.nodes.length - 1 && <span className="dash-link" aria-hidden="true" />}
            </div>
          ))}
        </div>
      </section>

      <section className="dash-card" aria-label={t.feed.title}>
        <div className="dash-card-head">
          <h2>{t.feed.title}</h2>
          <span className={`dash-live ${conn}`}><span className="live" aria-hidden="true" />{conn === "live" ? t.live : t.connecting}</span>
        </div>
        {feed.length === 0 ? (
          <p className="dash-empty">{t.feed.empty}</p>
        ) : (
          <ul className="dash-feed">
            {feed.map((e, i) => (
              <li key={`${e.ts}-${i}`} className="dash-evt">
                <span className="dash-evt-ic" aria-hidden="true">{FEED_ICONS[e.type] || "•"}</span>
                <span className="dash-evt-label">{t.feed.labels[e.type] || e.type}</span>
                <span className="dash-evt-detail">{eventDetail(e)}</span>
                <span className="dash-evt-time">{timeAgo(e.ts, lang)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer>
        <Link className="dash-back" href="/">{t.backToDemo}</Link>
        <span>{dict[lang].footer.tag}</span>
      </footer>
    </div>
  );
}
