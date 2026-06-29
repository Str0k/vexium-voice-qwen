// ════════════════════════════════════════════════════════════════════
// VEXIUM — Audio-Reactive Aurora Orb driver  (FINAL / production)
//
// Two pieces:
//   1. setupAnalyser(audioContext, sourceNodes) — builds the silent
//      analyser graph. Pass { caller:[...nodes], agent:[...nodes] } for
//      the dual-source tint, OR a flat array of nodes for single-source.
//      Returns a handle with .readCaller/.readAgent/.readBands,
//      .connectCaller/.connectAgent (to wire BufferSources later), .dispose.
//   2. startOrbLoop(handle, orbEl) — rAF loop that writes smoothed
//      --level + --level-bass/-mid/-treble (and --src) onto orbEl. A 3-band
//      frequency split makes the orb read as "analyzing speech", not an
//      amplitude blob. Two-stage attack/release so it snaps to speech and
//      decays organically. Pauses when the tab is hidden. Returns stop().
//
// Mutates the DOM directly at rAF cadence — NEVER React state — so a
// live call produces zero re-renders.
// ════════════════════════════════════════════════════════════════════

// Live reduced-motion check (re-reads, so toggling the OS setting mid-session works).
const _RM_MQL =
  typeof window !== "undefined" && window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : null;
const isReduced = () => !!(_RM_MQL && _RM_MQL.matches);

// ── 1. ANALYSER GRAPH ───────────────────────────────────────────────
// Each analyser hangs off a SILENT gain node (never connected to
// destination) so reading amplitude never affects what the user hears.
export function setupAnalyser(audioContext, sourceNodes) {
  const mk = () => {
    const gain = audioContext.createGain();
    gain.gain.value = 1;
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 512;                   // enough bins for a 3-band split
    analyser.smoothingTimeConstant = 0.6;     // light HW smoothing; JS does the rest
    gain.connect(analyser);                   // silent: gain -> analyser, no destination
    return {
      gain,
      analyser,
      buf: new Uint8Array(analyser.fftSize),             // time-domain (RMS amplitude)
      fbuf: new Uint8Array(analyser.frequencyBinCount),  // frequency bins (band split)
    };
  };

  // Normalize input: array => single-source; object => dual-source.
  const dual = sourceNodes && !Array.isArray(sourceNodes);
  const callerNodes = dual ? sourceNodes.caller || [] : sourceNodes || [];
  const agentNodes  = dual ? sourceNodes.agent  || [] : [];

  const caller = mk();
  const agent  = dual ? mk() : caller;       // single-source: share one analyser

  callerNodes.forEach((n) => { try { n.connect(caller.gain); } catch {} });
  agentNodes.forEach((n)  => { try { n.connect(agent.gain);  } catch {} });

  const rms = (a) => {
    a.analyser.getByteTimeDomainData(a.buf);
    let sum = 0;
    for (let i = 0; i < a.buf.length; i++) {
      const v = (a.buf[i] - 128) / 128;
      sum += v * v;
    }
    return Math.sqrt(sum / a.buf.length);
  };

  // Average three frequency sub-ranges (bass / mid-speech / treble), 0..1.
  const bandsOf = (a) => {
    a.analyser.getByteFrequencyData(a.fbuf);
    const len = a.fbuf.length;
    const avg = (lo, hi) => {
      let s = 0, n = 0;
      for (let i = lo; i < hi && i < len; i++) { s += a.fbuf[i]; n++; }
      return n ? s / n / 255 : 0;
    };
    return [avg(1, 8), avg(8, 48), avg(48, 130)]; // bass, mid (voice), treble
  };

  return {
    dual,
    // Read normalized 0..1 amplitudes; tune the multiplier to your levels.
    readCaller: () => Math.min(1, rms(caller) * 3.2),
    readAgent:  () => (dual ? Math.min(1, rms(agent) * 3.2) : 0),
    // Whoever is speaking drives each band (max across sources).
    readBands: () => {
      const c = bandsOf(caller);
      if (!dual) return c;
      const g = bandsOf(agent);
      return [Math.max(c[0], g[0]), Math.max(c[1], g[1]), Math.max(c[2], g[2])];
    },
    // Wire BufferSources that are created later (e.g. each agent TTS chunk).
    connectAgent:  (node) => { try { node.connect(agent.gain);  } catch {} },
    connectCaller: (node) => { try { node.connect(caller.gain); } catch {} },
    dispose: () => {
      try { caller.gain.disconnect(); } catch {}
      if (dual) { try { agent.gain.disconnect(); } catch {} }
    },
  };
}

// ── 2. rAF LOOP ─────────────────────────────────────────────────────
// Exponential two-stage smoother: fast ATTACK (0.35) so the orb jumps to
// speech, slow RELEASE (0.18) so it decays gracefully (no jitter). An
// idle FLOOR keeps a faint life during silence. Writes --level + the three
// band levels (and --src) straight onto the orb element. Pauses on hidden.
export function startOrbLoop(handle, orbEl) {
  let lvl = 0;        // smoothed displayed level
  let src = 0;        // smoothed source mix (0 caller -> 1 agent)
  let b = 0, m = 0, tr = 0; // smoothed band levels
  let raf = 0;
  let stopped = false;
  const FLOOR = 0.06; // gentle baseline so LIVE never reads as dead
  const smooth = (cur, target) => cur + (target - cur) * (target > cur ? 0.35 : 0.18);

  const tick = () => {
    raf = 0;
    const c = handle.readCaller();
    const a = handle.dual ? handle.readAgent() : 0;

    // who has the floor (only meaningful in dual mode)
    if (handle.dual) {
      const total = c + a;
      const targetSrc = total > 0.04 ? a / total : src; // hold last when silent
      src += (targetSrc - src) * 0.12;                   // slow tint glide
    }

    const target = Math.max(handle.dual ? Math.max(c, a) : c, FLOOR);
    lvl = smooth(lvl, target);

    const bands = handle.readBands ? handle.readBands() : [0, 0, 0];
    b  = smooth(b,  Math.min(1, bands[0] * 1.7));
    m  = smooth(m,  Math.min(1, bands[1] * 1.8));
    tr = smooth(tr, Math.min(1, bands[2] * 2.2));

    // In reduced-motion, damp the value so opacity-only response is calm.
    const damp = isReduced() ? 0.6 : 1;
    if (orbEl) {
      orbEl.style.setProperty("--level", (lvl * damp).toFixed(3));
      orbEl.style.setProperty("--level-bass", (b * damp).toFixed(3));
      orbEl.style.setProperty("--level-mid", (m * damp).toFixed(3));
      orbEl.style.setProperty("--level-treble", (tr * damp).toFixed(3));
      if (handle.dual) orbEl.style.setProperty("--src", src.toFixed(3));
    }

    if (!stopped && !document.hidden) raf = requestAnimationFrame(tick);
  };

  // Resume cleanly when the tab becomes visible again (battery + no backlog).
  const onVis = () => {
    if (!stopped && !document.hidden && !raf) raf = requestAnimationFrame(tick);
  };
  if (typeof document !== "undefined") document.addEventListener("visibilitychange", onVis);
  raf = requestAnimationFrame(tick);

  return function stop() {
    stopped = true;
    if (raf) cancelAnimationFrame(raf);
    if (typeof document !== "undefined") document.removeEventListener("visibilitychange", onVis);
    if (orbEl) {
      orbEl.style.setProperty("--level", "0");
      orbEl.style.setProperty("--level-bass", "0");
      orbEl.style.setProperty("--level-mid", "0");
      orbEl.style.setProperty("--level-treble", "0");
    }
  };
}

// ── 3. PRESS RIPPLE (vanilla; no React state) ───────────────────────
// Attach as onPointerDown on the orb <button>. Spawns a ripple at the
// touch point inside .orb-clip and removes it on animationend. Skipped
// entirely under prefers-reduced-motion.
export function spawnRipple(e) {
  if (isReduced()) return;
  const clip = e.currentTarget.querySelector(".orb-clip");
  if (!clip) return;
  const rect = clip.getBoundingClientRect();
  const span = document.createElement("span");
  span.className = "ripple";
  span.style.left = `${e.clientX - rect.left}px`;
  span.style.top = `${e.clientY - rect.top}px`;
  span.addEventListener("animationend", () => span.remove(), { once: true });
  clip.appendChild(span);
}
