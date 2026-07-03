"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { dict } from "./i18n";
import { resolveBridgeUrl, resolveHttpBase } from "./bridge";
import { setupAnalyser, startOrbLoop, spawnRipple } from "./orb-driver";

const OUTPUT_RATE = 24000; // Aura-2 linear16 output
const MAX_RETRIES = 3;           // auto-reconnect attempts when a connection fails to open
const CONNECT_TIMEOUT_MS = 6000; // give up on a single attempt after this, then retry
const CTA_URL = "https://vexiumai.com"; // post-call "book a setup call" link (change freely)

// Speak an ISO datetime the way a human reads it (locale-aware), with a safe fallback.
function fmtWhen(iso, lang) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  try {
    return d.toLocaleString(lang === "es" ? "es-MX" : "en-US", {
      weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
    });
  } catch { return iso; }
}

// Normalize a bridge FunctionResult into a single booking-card shape. The dental and
// restaurant verticals return DIFFERENT keys ({booking} vs {reservation}) with different
// fields — normalize both so the card never renders empty.
function normalizeBooking(evt) {
  const { name, result } = evt || {};
  if (!result || result.status !== "confirmed") return null;
  if (name !== "book_appointment" && name !== "book_reservation") return null;
  const b = result.booking || result.reservation || {};
  return {
    code: result.confirmation_code || "",
    name: b.caller_name || "",
    phone: b.phone || "",
    when: b.preferred_datetime || b.reservation_datetime || "",
    service: b.service || "",
    party: b.party_size || null,
    occasion: b.occasion || "",
    seating: b.seating_preference || "",
    raw: result,
  };
}

export default function CallWidget({ t, demos }) {
  const L = t || dict.en.call;
  const D = demos || dict.en.demos;
  const uiLang = L === dict.es.call ? "es" : "en";
  const [status, setStatus] = useState("idle"); // idle | connecting | live | error
  const [transcript, setTranscript] = useState([]);
  const [recordingUrl, setRecordingUrl] = useState(null);
  const [error, setError] = useState("");
  const [vertical, setVertical] = useState("dental"); // which demo business to call
  const [booking, setBooking] = useState(null);       // captured booking (the wow card)
  const [latency, setLatency] = useState(null);        // last time-to-first-audio (ms)
  const [bestLatency, setBestLatency] = useState(null);
  const [langSwitches, setLangSwitches] = useState(0); // ES<->EN swaps this call
  const [copied, setCopied] = useState(false);
  const [orbFx, setOrbFx] = useState(""); // transient orb flash: answering | barging | swap
  const [mode, setMode] = useState("voice"); // voice (Deepgram bridge) | text (Qwen /chat)
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [speakOn, setSpeakOn] = useState(true); // Qwen TTS playback for text replies

  const ws = useRef(null);
  const ctx = useRef(null);
  const micStream = useRef(null);
  const micNode = useRef(null);
  const recordDest = useRef(null);
  const recorder = useRef(null);
  const chunks = useRef([]);
  const sources = useRef(new Set());
  const nextPlay = useRef(0);
  const listRef = useRef(null);
  const statusRef = useRef("idle");
  const retryTimer = useRef(null);
  const retries = useRef(0);
  const cancelled = useRef(false);
  const verticalRef = useRef("dental");
  const lastUserTurnAt = useRef(0); // ms timestamp of the last user turn (for latency)
  const lastLang = useRef(null);    // last bubble language (to count switches)
  const orbFxTimer = useRef(null);  // transient orb-flash timeout
  const chatAudio = useRef(null);   // current Qwen TTS <audio> (stop before replacing)
  const chatSeq = useRef(0);        // guards stale /chat responses after a reset

  // Audio-reactive orb: the driver owns the analyser graph + rAF smoothing and
  // writes --level / --src straight onto the orb element (no React re-renders).
  const orbRef = useRef(null);
  const orbDriver = useRef(null);
  const stopOrb = useRef(null);
  const Lref = useRef(L);
  Lref.current = L; // latest i18n dict, reachable from queued retry timers

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight; // scroll the box, never the page
  }, [transcript]);

  // Release the previous recording's blob URL when it changes / on unmount.
  useEffect(() => () => { try { recordingUrl && URL.revokeObjectURL(recordingUrl); } catch {} }, [recordingUrl]);

  const cleanup = useCallback(() => {
    cancelled.current = true;
    if (retryTimer.current) { clearTimeout(retryTimer.current); retryTimer.current = null; }
    if (orbFxTimer.current) { clearTimeout(orbFxTimer.current); orbFxTimer.current = null; }
    try { stopOrb.current && stopOrb.current(); } catch {}
    try { chatAudio.current && chatAudio.current.pause(); } catch {}
    try { orbDriver.current && orbDriver.current.dispose(); } catch {}
    try { if (micNode.current) micNode.current.port.onmessage = null; } catch {}
    try { ws.current && ws.current.close(); } catch {}
    try { micStream.current?.getTracks().forEach((tr) => tr.stop()); } catch {}
    try { if (recorder.current && recorder.current.state !== "inactive") recorder.current.stop(); } catch {}
    try { ctx.current && ctx.current.close(); } catch {}
    sources.current.clear();
    if (orbRef.current) orbRef.current.style.setProperty("--level", "0");
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  function setPhase(p) { statusRef.current = p; setStatus(p); }

  // Brief, discrete orb "flash" tied to a real event (answering / barge-in / language
  // swap). Uses React state (infrequent — not per-frame), so it never touches the
  // rAF-driven --level loop. Cleared after `ms`.
  function flashOrb(fx, ms = 450) {
    setOrbFx(fx);
    if (orbFxTimer.current) clearTimeout(orbFxTimer.current);
    orbFxTimer.current = setTimeout(() => setOrbFx(""), ms);
  }

  function resetConversation() {
    setBooking(null);
    setTranscript([]);
    setRecordingUrl(null);
    setLatency(null);
    setBestLatency(null);
    setLangSwitches(0);
    setError("");
    lastLang.current = null;
    chatSeq.current += 1; // invalidate in-flight /chat replies
    setChatBusy(false);
    try { chatAudio.current && chatAudio.current.pause(); } catch {}
  }

  function pickVertical(id) {
    if (statusRef.current !== "idle" || chatBusy || id === vertical) return; // not mid-call, not a no-op
    setVertical(id);
    verticalRef.current = id;
    // Clear the previous call's recap/booking so panels don't mismatch the new business.
    resetConversation();
  }

  function pickMode(m) {
    if (m === mode || statusRef.current === "live" || statusRef.current === "connecting") return;
    setMode(m);
    setPhase("idle");
    setError("");
    // Keep the conversation: a prospect who just finished a voice call can hop
    // into Text and continue with full context (recap/booking survive the
    // round-trip; /chat receives the prior turns as history). Only a vertical
    // change wipes state.
    try { chatAudio.current && chatAudio.current.pause(); } catch {}
  }

  function bargeIn() {
    for (const s of sources.current) { try { s.stop(); } catch {} }
    sources.current.clear();
    nextPlay.current = ctx.current ? ctx.current.currentTime : 0;
  }

  function playChunk(arrayBuffer) {
    if (!ctx.current) return;

    // Time-to-first-audio: from the last user turn to the first audio of the reply.
    if (lastUserTurnAt.current) {
      const ms = Math.round(performance.now() - lastUserTurnAt.current);
      lastUserTurnAt.current = 0;
      if (ms > 60 && ms < 12000) {
        setLatency(ms);
        setBestLatency((b) => (b == null || ms < b ? ms : b));
      }
    }

    const pcm = new Int16Array(arrayBuffer);
    const f32 = new Float32Array(pcm.length);
    for (let i = 0; i < pcm.length; i++) f32[i] = pcm[i] / 0x8000;

    const buffer = ctx.current.createBuffer(1, f32.length, OUTPUT_RATE);
    buffer.copyToChannel(f32, 0);
    const src = ctx.current.createBufferSource();
    src.buffer = buffer;
    src.connect(ctx.current.destination);
    if (recordDest.current) src.connect(recordDest.current);
    if (orbDriver.current) orbDriver.current.connectAgent(src); // drives the agent halo tint

    const startAt = Math.max(ctx.current.currentTime, nextPlay.current);
    src.start(startAt);
    nextPlay.current = startAt + buffer.duration;
    sources.current.add(src);
    src.onended = () => sources.current.delete(src);
  }

  function handleEvent(evt) {
    switch (evt.type) {
      case "ConversationText": {
        const role = evt.role === "user" ? "user" : "agent";
        const lang = evt.lang || null;
        // Count switches off the AGENT voice only: the agent bubble's lang === the
        // server's real voice state, whereas a user bubble reacts to a single borrowed
        // word and would over-count (making the marquee pill lie). The per-bubble pill
        // still renders for both roles.
        if (lang && role === "agent") {
          if (lastLang.current && lang !== lastLang.current) {
            setLangSwitches((n) => n + 1);
            flashOrb("swap", 550); // the signature ES<->EN voice swap — make it pop
          }
          lastLang.current = lang;
        }
        if (role === "user") lastUserTurnAt.current = performance.now(); // anchor latency
        setTranscript((arr) => [...arr, { role, text: evt.content || "", lang }]);
        break;
      }
      case "FunctionResult": {
        const norm = normalizeBooking(evt);
        if (norm) setBooking(norm);
        break;
      }
      case "UserStartedSpeaking":
        bargeIn();
        flashOrb("barging", 420); // visibly "duck" when the caller interrupts the agent
        break;
      case "Error":
        setError(evt.description || "Error");
        setPhase("error");
        break;
      default:
        break;
    }
  }

  // Open the bridge WebSocket. On a failed/flaky connection it retries quietly a
  // few times (transient mobile network, Safari/Private Relay, a tunnel blip) and
  // only surfaces the error after all attempts are exhausted. Audio is already set
  // up by startCall(), so retries never re-prompt for the mic.
  function connect() {
    if (cancelled.current) return;
    const socket = new WebSocket(resolveBridgeUrl(verticalRef.current));
    socket.binaryType = "arraybuffer";
    ws.current = socket;
    let opened = false;

    const timer = setTimeout(() => {
      if (!opened) { try { socket.close(); } catch {} } // hung attempt -> onclose retries
    }, CONNECT_TIMEOUT_MS);

    socket.onopen = () => {
      opened = true;
      clearTimeout(timer);
      retries.current = 0;
      setPhase("live");
      flashOrb("answering", 600); // "answered" snap, tied to the real WS open
      nextPlay.current = ctx.current ? ctx.current.currentTime : 0;
      if (micNode.current) {
        micNode.current.port.onmessage = (e) => {
          if (socket.readyState === WebSocket.OPEN) socket.send(e.data);
        };
      }
      chunks.current = [];
      try {
        const rec = new MediaRecorder(recordDest.current.stream);
        rec.ondataavailable = (e) => e.data.size > 0 && chunks.current.push(e.data);
        rec.onstop = () => {
          const blob = new Blob(chunks.current, { type: rec.mimeType || "audio/webm" });
          setRecordingUrl(URL.createObjectURL(blob));
        };
        rec.start();
        recorder.current = rec;
      } catch {}
    };

    socket.onmessage = (e) => {
      if (e.data instanceof ArrayBuffer) playChunk(e.data);
      else { try { handleEvent(JSON.parse(e.data)); } catch {} }
    };

    socket.onerror = () => {}; // failures surface via onclose, which owns the retry logic

    socket.onclose = () => {
      clearTimeout(timer);
      if (opened) {                                  // dropped after connecting (mid-call)
        if (statusRef.current === "live") { cleanup(); setPhase("idle"); } // release mic/recorder/ctx
        return;
      }
      if (cancelled.current) return;                 // user hung up while connecting
      if (retries.current < MAX_RETRIES) {           // transient failure -> retry quietly
        retries.current += 1;
        setPhase("connecting");
        retryTimer.current = setTimeout(connect, Math.min(500 * retries.current, 2000));
      } else {
        setError(Lref.current.connError);            // exhausted -> show the error (current language)
        setPhase("error");
      }
    };
  }

  async function startCall() {
    setError("");
    setTranscript([]);
    setRecordingUrl(null);
    setBooking(null);
    setLatency(null);
    setBestLatency(null);
    setLangSwitches(0);
    setCopied(false);
    setOrbFx("");
    if (orbFxTimer.current) { clearTimeout(orbFxTimer.current); orbFxTimer.current = null; }
    lastLang.current = null;
    lastUserTurnAt.current = 0;
    setPhase("connecting");
    cancelled.current = false;
    retries.current = 0;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      ctx.current = audioCtx;
      await audioCtx.audioWorklet.addModule("/mic-worklet.js");

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      micStream.current = stream;

      const micSource = audioCtx.createMediaStreamSource(stream);
      const node = new AudioWorkletNode(audioCtx, "mic-processor");
      micNode.current = node;
      micSource.connect(node);

      const dest = audioCtx.createMediaStreamDestination();
      recordDest.current = dest;
      micSource.connect(dest);

      // Reactive orb: caller = mic, agent = TTS chunks (wired in playChunk).
      const driver = setupAnalyser(audioCtx, { caller: [micSource], agent: [] });
      orbDriver.current = driver;
      stopOrb.current = startOrbLoop(driver, orbRef.current);

      // Audio is ready — open the bridge connection (auto-retries on failure).
      connect();
    } catch (err) {
      setError(err?.message || L.micError);
      setPhase("error");
      cleanup();
    }
  }

  function endCall() {
    cleanup();
    setPhase("idle");
  }

  // ── Text mode: the same Qwen3-Max brain over POST /chat (no mic needed) ──
  async function sendChat(e) {
    if (e) e.preventDefault();
    const text = chatInput.trim();
    if (!text || chatBusy) return;
    const seq = chatSeq.current;
    setError("");
    setChatInput("");
    const next = [...transcript, { role: "user", text, lang: null }];
    setTranscript(next);
    setChatBusy(true);
    const t0 = performance.now();
    try {
      const res = await fetch(`${resolveHttpBase()}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vertical: verticalRef.current,
          messages: next.map((m) => ({
            role: m.role === "user" ? "user" : "assistant",
            content: m.text,
          })),
        }),
      });
      if (!res.ok) throw new Error(`chat ${res.status}`);
      const out = await res.json();
      if (seq !== chatSeq.current) return; // conversation reset while in flight
      const ms = Math.round(performance.now() - t0);
      setLatency(ms);
      setBestLatency((b) => (b == null || ms < b ? ms : b));
      for (const ev of out.tool_events || []) {
        const norm = normalizeBooking(ev);
        if (norm) setBooking(norm);
      }
      if (out.reply) {
        setTranscript((arr) => [...arr, { role: "agent", text: out.reply, lang: null }]);
        if (speakOn) playQwenTts(out.reply, seq);
      }
    } catch {
      if (seq === chatSeq.current) setError(Lref.current.chatError);
    } finally {
      if (seq === chatSeq.current) setChatBusy(false);
    }
  }

  // Spoken reply via Qwen TTS (qwen3-tts-flash). Any failure = stay text-only.
  async function playQwenTts(text, seq) {
    try {
      const res = await fetch(`${resolveHttpBase()}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) return;
      const { url } = await res.json();
      if (!url || seq !== chatSeq.current) return;
      try { chatAudio.current && chatAudio.current.pause(); } catch {}
      const audio = new Audio(url);
      chatAudio.current = audio;
      audio.play().catch(() => {});
    } catch {}
  }

  function copySummary() {
    const lines = transcript.map((m) => `${m.role === "user" ? L.you : L.agent}: ${m.text}`);
    let text = `${L.recapTitle} — Vexium AI\n\n${lines.join("\n")}`;
    if (booking) text += `\n\n${L.bookingTitle}:\n${JSON.stringify(booking.raw, null, 2)}`;
    try {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {}
  }

  const live = status === "live";
  const connecting = status === "connecting";
  const vOpt = (D.options || []).find((o) => o.id === vertical) || (D.options || [])[0];
  const hadCall = transcript.length > 0 || !!recordingUrl;
  const showRecap = !live && !connecting && hadCall;

  return (
    <div className="panel">
      <div className="demos">
        <span className="demos-label">{D.label}</span>
        {(D.options || []).map((o) => (
          <button
            type="button"
            key={o.id}
            className={`chip pick ${o.id === vertical ? "on" : ""}`}
            onClick={() => pickVertical(o.id)}
            disabled={status !== "idle" && o.id !== vertical}
            aria-pressed={o.id === vertical}
          >
            {o.name}
          </button>
        ))}
        {D.soon.map((s) => (
          <span className="chip soon" key={s}>{s}<em>{D.soonTag}</em></span>
        ))}
      </div>

      <div className="mode-row">
        <h2 className="panel-title">{vOpt?.title || L.title}</h2>
        <div className="mode-tabs" role="tablist" aria-label="Voice / text">
          <button
            type="button" role="tab" aria-selected={mode === "voice"}
            className={mode === "voice" ? "on" : ""}
            onClick={() => pickMode("voice")}
            disabled={live || connecting || chatBusy}
          >
            {L.modeVoice}
          </button>
          <button
            type="button" role="tab" aria-selected={mode === "text"}
            className={mode === "text" ? "on" : ""}
            onClick={() => pickMode("text")}
            disabled={live || connecting || chatBusy}
          >
            {L.modeText}
          </button>
        </div>
      </div>
      <p className="hint">{mode === "text" ? L.textHint : (vOpt?.hint || L.hint)}</p>

      {/* "Try saying…" coaching rail — steers prospects into the wow paths.
          In text mode a chip prefills the input, so one tap starts the flow. */}
      {vOpt?.prompts?.length > 0 && (
        <div className="try-rail">
          <span className="try-label">{L.tryLabel}</span>
          {vOpt.prompts.map((p) => (
            <button
              type="button"
              className={`try-chip ${mode === "text" ? "tappable" : ""}`}
              key={p}
              onClick={() => mode === "text" && setChatInput(p)}
              tabIndex={mode === "text" ? 0 : -1}
            >
              “{p}”
            </button>
          ))}
        </div>
      )}

      {mode === "voice" && (
      <div className="orb-wrap">
        <button
          ref={orbRef}
          className={`orb ${status} ${orbFx}`}
          onClick={live ? endCall : startCall}
          onPointerDown={spawnRipple}
          disabled={connecting}
          aria-label={live ? L.hang : L.start}
        >
          <span className="orb-halo h1" aria-hidden="true" />
          <span className="orb-halo h2" aria-hidden="true" />
          <span className="orb-halo h3" aria-hidden="true" />
          <span className="orb-halo h4" aria-hidden="true" />
          <span className="orb-core">
            <span className="orb-clip">
              <svg className="ic ic-mic" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4M8 22h8" />
              </svg>
              <svg className="ic ic-stop" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="6" width="12" height="12" rx="2.5" />
              </svg>
            </span>
          </span>
        </button>

        <div className="status">
          {status === "idle" && <span>{L.idle}</span>}
          {connecting && <span>{L.connecting}</span>}
          {live && <span><b>{L.liveA}</b> {L.liveB}</span>}
          {status === "error" && <span style={{ color: "var(--blue-bright)" }}>{error}</span>}
        </div>

        {/* Live proof pills: response time + the (invisible-until-now) bilingual switch */}
        {(latency != null || langSwitches > 0) && (
          <div className="stat-pills">
            {latency != null && (
              <span className="stat-pill"><b>{(latency / 1000).toFixed(1)}s</b> {L.respLabel}</span>
            )}
            {langSwitches > 0 && (
              <span className="stat-pill lang"><b>{langSwitches}×</b> {L.switchesLabel}</span>
            )}
          </div>
        )}

        <div className="btn-row">
          {!live ? (
            <button className="btn primary" onClick={startCall} disabled={connecting}>
              {connecting ? L.starting : L.start}
            </button>
          ) : (
            <button className="btn danger" onClick={endCall}>{L.hang}</button>
          )}
        </div>

        {!live && !connecting && <p className="consent">{L.consent}</p>}
      </div>
      )}

      {/* Booking captured — the "oh, it actually booked me" moment, with the raw data */}
      {booking && (
        <div className="booking-card">
          <div className="bc-head">
            <span className="bc-check" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <span className="bc-title">{L.bookingTitle}</span>
            {booking.code && <span className="bc-code">{booking.code}</span>}
          </div>
          <div className="bc-grid">
            {booking.name && <div><span>{L.bName}</span>{booking.name}</div>}
            {booking.phone && <div><span>{L.bPhone}</span>{booking.phone}</div>}
            {booking.when && <div><span>{L.bWhen}</span>{fmtWhen(booking.when, uiLang)}</div>}
            {booking.service && <div><span>{L.bService}</span>{booking.service}</div>}
            {booking.party && <div><span>{L.bParty}</span>{booking.party}</div>}
            {booking.occasion && <div><span>{L.bOccasion}</span>{booking.occasion}</div>}
            {booking.seating && <div><span>{L.bSeating}</span>{booking.seating}</div>}
          </div>
          <details className="bc-json">
            <summary>{L.jsonToggle}</summary>
            <pre>{JSON.stringify(booking.raw, null, 2)}</pre>
          </details>
        </div>
      )}

      <div className="transcript" ref={listRef} role="log" aria-live="polite" aria-atomic="false">
        {transcript.length === 0 ? (
          <div className="empty">{L.empty}</div>
        ) : (
          transcript.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <span className="who">
                {m.role === "user" ? L.you : L.agent}
                {m.lang && <em className={`lang-pill ${m.lang}`}>{m.lang.toUpperCase()}</em>}
              </span>
              <span className="txt">{m.text}</span>
            </div>
          ))
        )}
        {mode === "text" && chatBusy && <div className="typing">{L.thinking}</div>}
      </div>

      {mode === "text" && (
        <div className="chat-zone">
          <form className="chat-row" onSubmit={sendChat}>
            <input
              className="chat-input"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={L.textPlaceholder}
              aria-label={L.textPlaceholder}
              maxLength={500}
              autoComplete="off"
            />
            <button className="btn primary" type="submit" disabled={chatBusy || !chatInput.trim()}>
              {L.send}
            </button>
          </form>
          <div className="chat-meta">
            <label className="speak-toggle">
              <input
                type="checkbox"
                checked={speakOn}
                onChange={(e) => setSpeakOn(e.target.checked)}
              />
              <span>{L.speakToggle}</span>
            </label>
            {latency != null && (
              <span className="stat-pill"><b>{(latency / 1000).toFixed(1)}s</b> {L.respLabel}</span>
            )}
          </div>
          {error && <p className="chat-error" role="alert">{error}</p>}
          <p className="consent">{L.poweredText}</p>
        </div>
      )}

      {/* Post-call recap: replay + the captured data + a real CTA (no dead-end download) */}
      {mode === "voice" && showRecap && (
        <div className="recap">
          <div className="recap-head">
            <span className="recap-title">{L.recapTitle}</span>
            {bestLatency != null && (
              <span className="recap-best">{(bestLatency / 1000).toFixed(1)}s {L.respLabel}</span>
            )}
          </div>
          {recordingUrl && <audio className="recap-audio" controls src={recordingUrl} />}
          <div className="recap-actions">
            <a className="btn primary" href={CTA_URL} target="_blank" rel="noopener noreferrer">{L.cta}</a>
            <button className="btn" onClick={copySummary}>{copied ? L.copied : L.copy}</button>
            <button className="btn" onClick={startCall}>{L.newCall}</button>
          </div>
        </div>
      )}

      <p className="note">{D.footnote}</p>
    </div>
  );
}
