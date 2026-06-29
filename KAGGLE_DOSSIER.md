# Vexium → Gemini "Sofía" Concierge Agent — Verified Design Dossier

**Kaggle "AI Agents: Intensive Vibe Coding Capstone" — Concierge Agents track**
**Author:** Cristian Ramirez · **Date:** 2026-06-22 · **Deadline:** July 6 2026, 11:59 PM PT (re-verify on the live page)
**Source app:** `C:\Users\psiqu\vexium-voice\` (Sofía / Vexium Dental vertical)

---

## 0. Read-this-first: what the skeptics actually changed

Three independent skeptic passes all **REFUTED the core premise** you started with. The corrections are not cosmetic — they change what you build. Internalize these four before reading anything else:

1. **AI Studio is NOT required.** The capstone (`vibecoding-agents-capstone-project`) requires a generic **"Public Project Link"** = any no-login demo URL **OR a public GitHub repo with setup instructions**. The string "AI Studio" appears nowhere on its Overview/Rules. The "mandatory AI Studio app link" belongs to a **different, finished** hackathon (`gemini-3`, Dec 2025). Do not over-optimize for AI Studio.
2. **The video is 5 minutes, on YouTube** — not 2 minutes. The writeup is **≤2,500 words** — not 250. (Those small numbers were also from the wrong competition.)
3. **70% of the score is implementation**, with a **hard gate: demonstrate ≥3 of 6 course concepts** (ADK multi-agent, MCP server, Antigravity, Security, Deployability, Agent skills). A single Gemini-Live voice app naturally hits only ~1–2. **Every prior-edition track winner was a multi-agent ADK system.** Voice is a "wow" demo layer, not where the points live.
4. **The deliverable must not depend on voice or on a live deployment.** Judging explicitly does **not require** a live endpoint. The guaranteed-valid floor is: public GitHub repo + ≤2,500-word writeup + ≤5-min YouTube video + cover image, Track = Concierge.

**Strategic consequence baked into this dossier:** we build an **ADK multi-agent core + an MCP tool server** (the point-bearing spine), ship it as a **public GitHub repo** (guaranteed-valid floor), and add the **Gemini Live voice front-end as the optional demo/wow layer** that we publish to a public URL only after the spine is done. The original "pure Gemini Live AI Studio app" plan is retained ONLY as the demo layer, never as the submission's backbone.

> **Note on the request as written.** You asked for a dossier framed around a single Gemini-Live AI Studio app (mode toggle, token-mint endpoint in an exported Node server, native publish). I have kept every one of those components — they are real and reusable — but **demoted them to the demo/wow layer** and added the ADK+MCP spine the rubric actually rewards. Building only the voice app would risk failing the 3-concept gate. This is the single most important deviation; everything below reflects it.

---

## 1. Refined Reuse Map (reuse / port-to-TS / drop)

Grounded in the verified code at `C:\Users\psiqu\vexium-voice\clinic.py` (160 lines) and `agent_config.py` (622 lines). I re-read both: the confirmation-code algorithm and the BUSY_WEEKLY fixtures are confirmed **exactly** as cited (see §1.4).

| Asset | File · lines | Verdict | Target form | Effort |
|---|---|---|---|---|
| Sofía dental system prompt | `agent_config.py` ~64–147 | **REUSE** | Gemini `systemInstruction` + ADK agent instruction | Low |
| 4 "human" sections (empathy / reasoning / honesty / handoff) | `agent_config.py` ~34–62 | **REUSE** verbatim | Append to instruction | None |
| `check_availability` schema | `agent_config.py` ~244–261 | **REUSE** (UPPERCASE types) | ADK tool decl + Gemini `functionDeclaration` | Low |
| `book_appointment` schema | `agent_config.py` ~263–295 | **REUSE** (add `enum:["es","en"]`) | ADK tool decl + Gemini `functionDeclaration` | Low |
| Clinic profile / hours / greeting | `clinic.py` 22–31 | **REUSE** | TS/Python const | None |
| Services array (11 items) | `clinic.py` 35–52 | **REUSE** | const | None |
| `BUSINESS_HOURS` | `clinic.py` 58–62 | **REUSE** | const | None |
| `BUSY_WEEKLY` demo fixtures | `clinic.py` 69–74 | **REUSE** | const — **demo-critical** | None |
| `check_availability()` logic | `clinic.py` 116–141 | **PORT to TS** (also keep Python in MCP) | pure function | Medium |
| `book_appointment()` + SHA1 code | `clinic.py` 144–160 | **PORT to TS** | pure function | Low |
| `_parse` / `_fmt` / `_free_slots_from` helpers | `clinic.py` 77–113 | **PORT to TS** | date utils | Medium |
| Web frontend (orb, i18n, Landing, fx) | `web/app/*` | **REUSE** visuals | adapt to demo layer | Low–Med |
| `CallWidget.js` transport | `web/app/CallWidget.js` | **PORT** | swap Deepgram WS → Gemini Live | High |
| Deepgram Voice Agent / Flux STT | `server.py`, `agent_config.py` | **DROP** | Gemini Live native audio | — |
| ElevenLabs BYO-TTS (Regina/Eryn, `UpdateSpeak`) | `agent_config.py` ~468–516 | **DROP** | Gemini Live single multilingual voice | — |
| AWS Bedrock / Claude Haiku plumbing | `agent_config.py` ~443–465 | **DROP** | Gemini model directly | — |
| FastAPI WS bridge | `server.py` (all) | **DROP** | browser↔Gemini direct + tiny token route | — |
| `detect_language` / `speak_for_language` heuristics | `agent_config.py` ~548–622 | **DROP** | native-audio auto-language (no `languageCode`) | — |

**Why the DROPs are forced (verified):** Gemini native-audio models *"automatically choose the appropriate language and don't support explicitly setting the language code."* So the entire per-turn voice-swap design (Regina-MX/Eryn-US via `UpdateSpeak`, confirmed in `CLAUDE.md`) and the `detect_language` heuristic become dead weight — you keep only the prompt's language rules and **one** multilingual voice (`Aoede`, `Kore`, or `Leda`).

### 1.4 The two demo-critical constants — verified verbatim from `clinic.py`

```python
# clinic.py:69-74  — recurring "already booked" hours (weekday: {hours})
BUSY_WEEKLY = { 0:{9,10,11}, 2:{15,16}, 4:{16,17}, 5:{12,13} }
#               Mon AM full   Wed PM     Fri late   Sat midday

# clinic.py:144-146 — deterministic confirmation code
def _confirmation_code(seed):                 # seed = f"{caller_name}|{phone}|{preferred_datetime}"
    return f"VX-{hashlib.sha1(seed.encode()).hexdigest()[:4].upper()}"
```

**Why this matters:** the SHA1 code is **deterministic** — the same name+phone+time always yields the same `VX-XXXX`. Pick your demo caller once and the confirmation code never changes between takes. Asking for **Monday 9/10/11am** (busy) forces the "offer alternatives" branch on camera every single time, regardless of the real recording date. This is your reproducibility backbone.

---

## 2. Component Breakdown

Each unit = one purpose, an interface, dependencies. **Tier A = the scoring spine (ADK + MCP), Tier B = the voice/AI-Studio demo layer.** Build Tier A first.

### TIER A — the scoring spine (where 70% of points live)

#### A1. MCP tool server (`clinic-mcp`)
- **Purpose (one thing):** expose the clinic's booking logic as MCP tools over a standard MCP server — this is the "MCP Server" course concept, scored in Code.
- **Interface:** MCP server exposing two tools: `check_availability(requested_datetime) -> {available, message, alternatives[]}` and `book_appointment(caller_name, phone, service, preferred_datetime, language) -> {status, confirmation_code, booking}`. Schemas are the **reused** `agent_config.py` declarations (UPPERCASE types).
- **Dependencies:** ported `clinic.py` logic (you can keep it **in Python** here — `clinic.py` is pure in-memory, zero external deps, so the MCP server reuses it almost as-is). MCP Python SDK.
- **Reuse:** `clinic.py` 22–160 nearly verbatim.

#### A2. Receptionist orchestrator agent (ADK)
- **Purpose:** own the call flow — greet, gather name/phone/service/time, decide when to call tools, hand off to sub-agents. This is the "Agent / multi-agent (ADK)" concept.
- **Interface:** ADK `Agent` with `instruction` = the Sofía prompt + 4 human sections (reused), `tools` = MCP `clinic-mcp` tools, plus `sub_agents = [booking_agent, verification_agent]`.
- **Dependencies:** Google ADK, Gemini model (text), A1 (MCP), A3, A4.

#### A3. Booking sub-agent (ADK)
- **Purpose:** once details are gathered, call `check_availability`, then (only on confirmation) `book_appointment`; return the structured booking.
- **Interface:** ADK sub-agent; input = collected slots; output = a **Pydantic** `Booking` object (strict agent-to-agent I/O — the NewsPulse winner pattern).
- **Dependencies:** A1 (MCP tools), Pydantic.

#### A4. Verification / confirmation sub-agent (ADK)  ← the "wow"/self-correction
- **Purpose:** before booking is finalized, verify every required field is present, the slot was actually confirmed available, and PII is well-formed; **reject and force a retry** if not (the LoopAgent self-correction that separated the prior Concierge winner).
- **Interface:** ADK sub-agent; input = proposed `Booking`; output = `{ok: bool, missing: [], reason}`. On `ok:false` the orchestrator re-asks one question.
- **Dependencies:** Pydantic schema, A3.

#### A5. PII-safety layer (Concierge track mandate)
- **Purpose:** keep personal info safe — the Concierge track explicitly scores "keep personal information safe and secure." This is the "Security features" concept.
- **Interface:** a thin module that (a) **never logs raw phone numbers** (masks to `•••• 0182`), (b) keeps PII in session memory only / no third-party persistence, (c) states the data-handling policy in the UI and README.
- **Dependencies:** none heavy — it's discipline + a masking helper + a README section. Cheap points.

### TIER B — the voice / AI-Studio demo layer (the "wow")

#### B1. App shell + mode toggle
- **Purpose:** one screen, a **Text ⇄ Voice** toggle, so judges always have a working path even if mic/Live fails.
- **Interface:** React/TS shell; `mode: "text" | "voice"`; renders chat engine (B2) or voice engine (B3); reuses the orb (`web/app/orb-driver.js`), `i18n.js`, Landing visuals.
- **Dependencies:** B2, B3, F (live JSON panel).
- **Reuse:** `web/app/Landing.js`, `orb-driver.js`, `i18n.js`, `fx.js` (visuals only).

#### B2. Chat engine (`generateContent` + function-calling loop)
- **Purpose:** text booking — the **reliable fallback** that never depends on a mic.
- **Interface:** `sendMessage(text)`; runs `generateContent` with `config.tools=[{functionDeclarations:[checkAvail, book]}]`; loop: model emits `functionCall{name,args}` → run TS tool (or call MCP) → append `functionResponse{name,response}` → re-call → final text.
- **Dependencies:** `@google/genai`, the ported TS tools (or A1 via HTTP), system prompt.
- **Reuse:** schemas + prompt. **Port:** `clinic.py` logic to TS.

#### B3. Voice engine (Live API + ephemeral-token client)
- **Purpose:** real-time bilingual voice booking — the headline demo moment.
- **Interface:** `startCall()` → `GET /api/token` (B4) → open WS `wss://generativelanguage.googleapis.com/.../BidiGenerateContentConstrained?access_token=<token>` (**v1alpha**) → stream mic (PCM16 **16 kHz**) → play model audio (PCM16 **24 kHz**) → on `toolCall` run tools, reply `sendToolResponse({functionResponses:[{id,name,response}]})`.
- **Critical config:**
  - model `gemini-3.1-flash-live-preview` (Preview), `responseModalities:[AUDIO]`, one voice (`Aoede`).
  - server VAD on (`automaticActivityDetection`), **on `serverContent.interrupted` flush the 24 kHz playback queue** (barge-in).
  - `sessionResumption:{}` so a long call doesn't drop at ~10 min.
  - **No `languageCode`, no per-turn voice swap** — native audio code-switches itself.
- **Dependencies:** B4 (token), AudioWorklet (capture/playback), the TS tools, system prompt.
- **Reuse:** `CallWidget.js` mic/playback scaffolding + orb. **Drop:** all Deepgram WS event handling.

#### B4. Token-mint endpoint (tiny Node server)
- **Purpose:** mint **short-lived Live ephemeral tokens server-side** so the browser never holds the real key (June-19 compliant by construction).
- **Interface:** `POST /api/token` → `authTokens.create({uses:1, expire_time:+30m, new_session_expire_time:+1m, http_options:{api_version:"v1alpha"}, live_connect_constraints:{model, voice, responseModalities}})` → return `{token: token.name}`. Add **per-IP rate limit**.
- **Dependencies:** `@google/genai` (server), `GEMINI_API_KEY` as a server-side secret/env var. This is the only server piece the voice layer needs; everything else is browser↔Gemini direct.
- **Note:** the AI Studio "Publish" button already gives you exactly this Node backend on Cloud Run with the key as a secret — so if you publish via AI Studio you may not need to hand-write a server, only add this route.

#### B5. Tools / booking-logic TS module (ported `clinic.py`)
- **Purpose:** the single source of truth for availability + booking on the client/demo side.
- **Interface:** `checkAvailability(iso) -> AvailabilityResponse`; `bookAppointment(name,phone,service,iso,lang) -> BookingResponse`; `confirmationCode(name,phone,iso)`. Plus `BUSINESS_HOURS`, `BUSY_WEEKLY`, `SERVICES` consts and ISO date helpers.
- **Dependencies:** Web Crypto `crypto.subtle.digest('SHA-1', …)` (browser) for the code; Node `crypto.createHash('sha1')` server-side — both must produce the same `VX-XXXX`.
- **Reuse:** direct translation of `clinic.py` 35–160. **Verify** the SHA1→hex→first-4→upper pipeline matches Python byte-for-byte (test with one fixed seed).

#### B6. Live JSON booking panel
- **Purpose:** show the **structured data capture** on screen as the call happens — the "missed call → booked appointment → captured row" payoff judges can see.
- **Interface:** subscribes to tool results; renders the live `booking` object + `confirmation_code` as a card/JSON, PII masked per A5.
- **Dependencies:** B2/B3 tool-result events.

#### B7. Deploy / publish
- **Purpose:** produce the public no-login URL for the demo layer.
- **Interface:** AI Studio **Publish (Starter Tier)** → Cloud Run `*.run.app` / `aistudio.google.com/apps/...` link, key as server-side secret, auto auth-key. Fallback: own GCP Cloud Run export, or skip deploy entirely (repo + video is a valid submission).
- **Dependencies:** B1–B6, `GEMINI_API_KEY`.

---

## 3. Phased 2-Week Plan (Mon Jun 22 → deadline)

**Principle:** de-risk the deliverable first (Phase 0 spike), then build the scoring spine, then add voice. If anything slips, you still have a valid, competitive submission.

> ⚠️ **Phase 0 is a publish-path spike and runs BEFORE any feature work.** Do not build Sofía until you have personally confirmed a published AI Studio hello-world yields a valid public no-login link, and tested whether voice/Live works in that published form.

| Day | Date | Focus | Concrete deliverable |
|---|---|---|---|
| **Mon** | **Jun 22** | **PHASE 0 — publish-path spike** | Re-verify on the LIVE Kaggle page: deadline (Jul 6 vs Jun 30), track, 3-concept gate, 2,500-word / 5-min YouTube rules. Create a **throwaway** AI Studio hello-world, click **Publish**, confirm it gives a **public no-login link** that opens in an incognito window. Note whether it's `aistudio.google.com/apps/...` or `*.run.app`. |
| **Tue** | **Jun 23** | **PHASE 0 cont. — voice-in-published spike** | In a throwaway app, test whether a **published** app can mint a Live ephemeral token + open the Live WS (does mic voice work end-to-end in the published form, not just the editor?). If yes → AI Studio publish is the demo path. If no/flaky → fall back to **own Cloud Run export** or **text-only voice-clip-in-video**. Lock the decision today. |
| **Wed** | **Jun 24** | Repo + spine scaffolding | Create the **public GitHub repo** (the guaranteed-valid deliverable). Scaffold ADK project. Port `clinic.py` into the **MCP server (A1)** (keep Python). Stand up `check_availability`/`book_appointment` over MCP; unit-test the BUSY_WEEKLY branches + the `VX-` code. |
| **Thu** | **Jun 25** | Orchestrator + booking agent (A2, A3) | Wire the receptionist orchestrator with the Sofía instruction + 4 human sections; booking sub-agent returns a **Pydantic `Booking`**. Text-driven end-to-end booking works in ADK. |
| **Fri** | **Jun 26** | Verification agent + PII (A4, A5) | Add the verification/self-correction sub-agent (rejects incomplete/unconfirmed bookings, forces a retry). Add PII masking + the data-handling policy. **Spine now hits ≥3 concepts: ADK multi-agent + MCP + Security.** |
| **Sat** | **Jun 27** | TS port + tools module (B5) | Port `clinic.py` → TS; verify SHA1 code matches Python on a fixed seed. Build `BUSINESS_HOURS`/`BUSY_WEEKLY`/`SERVICES` consts + date helpers. |
| **Sun** | **Jun 28** | Chat engine + JSON panel (B2, B6) | Text `generateContent` function-calling loop in the React shell; live JSON booking panel renders the captured row + code. **This is the reliable demo even with zero voice.** |
| **Mon** | **Jun 29** | App shell + mode toggle (B1) | Reuse Landing/orb/i18n visuals; Text⇄Voice toggle; bilingual UI strings. |
| **Tue** | **Jun 30** | Token endpoint (B4) | `/api/token` minting ephemeral tokens (`uses:1`, short expiry, `live_connect_constraints`, per-IP rate limit). Confirm `v1alpha` end-to-end. **(If the real deadline is Jun 30, the spine + text demo are already submittable today — stop and submit a v1, then keep improving.)** |
| **Wed** | **Jul 1** | Voice engine (B3) part 1 | Mic capture (AudioWorklet PCM16 16k), playback (24k), open Live WS with the token, get audio round-trip + greeting. |
| **Thu** | **Jul 2** | Voice engine (B3) part 2 | Function calls inside Live (`toolCall`→`sendToolResponse`), barge-in flush on `interrupted`, `sessionResumption`. Full **voice** booking works against BUSY_WEEKLY fixtures. |
| **Fri** | **Jul 3** | Deploy + harden (B7) | Publish demo via the path locked on Jun 23; test public no-login link in incognito; verify token rate-limit + constraints. Freeze a fixed demo date in the prompt. |
| **Sat** | **Jul 4** | Record + edit video | Shoot the 5-min YouTube video (script in §5 + the deeper rubric beats). Capture: problem, why agents, architecture diagram, live voice booking, JSON capture, the build. |
| **Sun** | **Jul 5** | Writeup + README + cover image | ≤2,500-word writeup to the rubric headings; 20-pt README; cover image; **submit early** (Track = Concierge, attach repo + YouTube + project link). |
| **Mon** | **Jul 6** | Buffer / submit by 11:59 PM PT | Final re-verify of the live deadline; fix anything; confirm all 4 mandatory pieces attached. **Do not wait for the last hour.** |

**Slip rule:** if voice (Jul 1–3) slips, ship **text-only** via the same spine + a screen-recorded text demo. The submission stays valid and competitive — voice was always icing.

---

## 4. Recommended Publish Path + Explicit Fallback

**Recommended (reflects all three skeptic verdicts):**

> **Primary deliverable = public GitHub repo** (ADK multi-agent + MCP server + README + setup instructions). This alone is a complete, valid, deploy-free submission and carries the implementation points. **Demo layer = AI Studio "Publish" (Starter Tier)** → public no-login `aistudio.google.com/apps/...` (Cloud Run-backed) URL with the key as a server-side secret and an auto-created auth key (June-19 compliant by construction), minting Live **ephemeral tokens** for browser-direct voice.

**Fallback ladder (use the first that holds):**

1. **AI Studio Publish + Voice** — if the Jun 22–23 spike confirms a published app can mint tokens and run Live voice end-to-end with a public no-login link. *Best case.*
2. **AI Studio Publish + Text-only** — if published-app voice is flaky/unverified, publish the **text** chat engine (reliable), and show **voice only as a recorded clip inside the YouTube video** (recorded from the editor/local). The public link is text; voice still appears in the demo.
3. **Own GCP Cloud Run export** — if Starter-Tier quota/2-app cap or token-minting-in-published is a blocker: export the ZIP, deploy to your **own billed** Cloud Run project, keep `GEMINI_API_KEY` a Cloud Run secret, customize the proxy + tighten rate limits. Still yields a public URL.
4. **Repo + video only, no live deploy** — judging does **not require** a live endpoint. Public GitHub repo with setup instructions + the 5-min YouTube demo is a fully valid Concierge submission. *Guaranteed floor — never below this.*

**Voice vs text-only:** text is the reliable spine of the demo; voice is the wow. Always ship the **mode toggle (B1)** so a mic/Live failure on judging day degrades gracefully to text rather than to a blank screen. **Never** bet the submission on the preview voice model (`gemini-3.1-flash-live-preview` is Preview + v1alpha and can change without notice).

---

## 5. 2-Minute Video Script (shot-by-shot, bilingual, < 2:00)

> The **capstone** allows **5 minutes** (use it — §3 Jul 4 covers the full beats: problem → why agents → architecture → demo → the build). This **2-minute cut** is the tight "live voice booking + JSON capture + business value" sequence you requested; drop it in as the demo segment of the 5-min video, or use standalone. Times are cumulative; total **1:58**.

| Time | Shot | On screen | Audio / VO (bilingual) |
|---|---|---|---|
| 0:00–0:08 | Cold open | Phone ringing, "MISSED CALL — 6:14 PM" then "CLINIC CLOSED" | VO (EN): "A dental clinic misses this call. That patient books somewhere else." |
| 0:08–0:16 | Title | "Sofía — Vexium Concierge Agent" + orb idle | VO (ES): "Sofía contesta cada llamada, en español o inglés, las 24 horas." |
| 0:16–0:24 | Click "Call Sofía" | Voice mode, orb wakes | SFX connect. Sofía (ES, live): *"Gracias por llamar a Vexium Dental, le atiende Sofía…"* |
| 0:24–0:36 | Live voice — request | Transcript streams; orb reacts | Caller (live, ES): *"Quiero una limpieza dental el lunes a las nueve de la mañana."* → **hits Monday 9am (BUSY_WEEKLY)** |
| 0:36–0:50 | **Alternatives branch** | JSON panel shows `available:false`, `alternatives[]` | Sofía: *"Permítame un momentito… mmm, esa hora ya está reservada. Le ofrezco el lunes a las dos, o el martes a las diez de la mañana."* |
| 0:50–1:00 | Caller picks free slot | Panel updates `available:true` | Caller: *"El martes a las diez, perfecto."* Sofía: *"Muy bien."* |
| 1:00–1:14 | Read-back + name/phone | Fields fill one by one, **phone masked `•••• 0182`** | Sofía (read-back): *"Entonces, Guadalupe Ramírez, martes diez de la mañana, limpieza dental, ¿correcto?"* Caller: *"Sí."* |
| 1:14–1:26 | **Booking fires** | JSON `book_appointment` → card flips to **`VX-A1F2`** confirmed | Sofía: *"¡Listo! Su cita quedó confirmada, código VX-A-uno-F-dos."* (deterministic SHA1 code) |
| 1:26–1:38 | Language flip (1 line) | Same call, switches to EN seamlessly | Caller (EN): "And do you have parking?" Sofía (EN, same voice): "Yes — free parking right out front. Anything else?" |
| 1:38–1:50 | Architecture flash | Diagram: Orchestrator → Booking → **Verification** sub-agents + **MCP** clinic server; "PII masked, never logged" | VO (EN): "A multi-agent ADK system — a verification agent rejects any incomplete booking — with the clinic logic exposed over MCP." |
| 1:50–1:58 | Business value close | "Missed call → booked appointment → captured row" + repo/URL | VO (ES): "De una llamada perdida… a una cita confirmada." (EN): "That's revenue saved, automatically." |

**Reproducibility:** the **Monday-9am → alternatives → confirmed** path and the **`VX-` code** are deterministic (BUSY_WEEKLY + SHA1), so every take is identical. Freeze a fixed "today" in the prompt before recording.

---

## 6. Writeup Outline (≤ 2,500 words, structured to the rubric)

Use the exact winner-proven headings (NewsPulse). Suggested budget in parentheses.

1. **Title + Subtitle** — e.g. "Sofía: a bilingual concierge that turns missed calls into booked care." Select **Track = Concierge Agents**. (≈20)
2. **Problem Statement** (≈300) — clinics/small businesses miss after-hours and overflow calls; each missed call = lost patient + lost revenue; Hispanic callers underserved in their language.
3. **Why agents? (Why not a script/IVR?)** (≈300) — open-ended conversation, empathy, language code-switching, multi-step gather→verify→book needs reasoning + tool use, not a decision tree; a verification agent self-corrects.
4. **What we built** (≈350) — Sofía, a **multi-agent ADK** system: receptionist orchestrator + booking sub-agent + verification/confirmation sub-agent; clinic logic exposed via an **MCP server**; bilingual voice + text front-end.
5. **Architecture** (≈450, **with diagram image**) — the agent graph, Pydantic agent-to-agent contracts, the MCP tool boundary, the ephemeral-token voice path (key never in browser), PII-safety. Name the **3+ course concepts** explicitly: **ADK multi-agent, MCP server, Security, Deployability.**
6. **Demo** (≈200) — embed the YouTube link; describe the missed-call→booked-appointment flow + the live JSON capture + the deterministic confirmation code.
7. **The Build** (≈350) — Gemini (text + `gemini-3.1-flash-live-preview` voice), ADK, MCP, ephemeral tokens on v1alpha, Cloud Run publish; what was reused from the existing Vexium voice app and what was ported.
8. **Security & Privacy** (≈200) — Concierge mandate: PII masking, no raw-phone logging, session-only data, server-side key/auth-key, rate-limited token endpoint, "no API keys in code."
9. **If we had more time / Future work** (≈150) — real calendar via MCP, Twilio phone-in, multi-clinic, memory of returning callers.

Plus the **Media Gallery cover image** (required) and confirm the word count stays ≤2,500.

---

## 7. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **3-concept gate failure** — judged as a single voice app, hits <3 concepts | **High** (if you build only the voice app) → **Low** (with the spine) | Disqualifying for points | Build the ADK multi-agent + MCP + Security spine FIRST (Phase A). Name the 3 concepts explicitly in writeup/README/video. |
| R2 | **Wrong-competition assumptions** (2-min/250-word/AI-Studio-required) | **High** if unchecked | Mis-built deliverable | Phase 0 Mon Jun 22: re-verify the LIVE Kaggle page. This dossier already uses the corrected rules (5-min/2,500/repo-OK). |
| R3 | **Deadline confusion** (Jun 30 vs Jul 6) | Medium | Could lose a week | Treat **Jun 30** as a soft internal target; have a submittable v1 by Jun 30 (spine+text). Re-verify live Timeline Mon and again before submit. |
| R4 | **June 19 2026 unrestricted-key rejection** — a browser-embedded/standard unrestricted key is now rejected outright | **Certain** if you embed a key client-side | Demo dead on arrival | **Never** ship a key client-side. Use the Publish/Cloud-Run server-side secret (auto auth-key) + ephemeral tokens. New AI Studio keys are already auth keys; if reusing an old key, restrict it to the Gemini API in the API Keys page. |
| R5 | **Quota drain on a public no-login app** (scraped token / looped sessions / judging-day spike) | Medium–High | App pauses exactly when judges open it (Starter-Tier group pause to ~midnight PT) | `uses:1`, short `expire_time`/`new_session_expire_time`, `live_connect_constraints` pinning model/voice/modality, **per-IP rate limit** on `/api/token`. Prefer your **own billed Cloud Run** to avoid the 2-app shared-quota pause. Text mode as the un-throttled fallback. |
| R6 | **Preview model instability** (`gemini-3.1-flash-live-preview` Preview + v1alpha can change/throttle) | Medium | Voice demo flaky on judging day | Don't gate submission on voice; mode toggle → text. Record a clean voice take in advance as a backup clip. |
| R7 | **Voice-in-published-app unverified** (can a published Starter-Tier app mint tokens + run Live?) | Medium | Forces path change late | Resolve in the **Phase 0 spike (Jun 22–23)** before building; fall back to own Cloud Run export or text-only-link + voice-in-video. |
| R8 | **SHA1 mismatch browser↔Python** (different `VX-` code) | Low | Demo/codebase inconsistency | One unit test on a fixed seed comparing Web Crypto SHA-1 vs `clinic.py` output before recording. |
| R9 | **Live session drop at ~10 min / barge-in audio overlap** | Low (calls are short) | Mid-call failure | `sessionResumption:{}`; flush 24 kHz queue on `serverContent.interrupted`. |
| R10 | **PII exposure** (raw phone in logs/UI) hurts the Concierge "secure" criterion | Medium | Lower track score | A5 masking + no-log discipline + explicit policy in README/UI. |
| R11 | **Last-minute submission failure** (missing one of the 4 mandatory pieces) | Medium | Invalid submission | Submit a complete v1 by Jul 5; Jul 6 is buffer only. Checklist: writeup + cover image + YouTube + project link, Track selected. |

---

## 8. Open Questions — confirm on the LIVE competition page before submitting

1. **Deadline:** is it **Jul 6 11:59 PM PT** (live Timeline) or **Jun 30** (some secondary sources)? Re-read the live Timeline; Kaggle reserves the right to amend.
2. **3-concept gate:** confirm the exact list and how many are required (research says **≥3 of 6**: ADK multi-agent, MCP, Antigravity, Security, Deployability, Agent skills). Confirm which need to appear in **Code** vs **Video**.
3. **Project Link:** confirm a **public GitHub repo with setup instructions** is accepted in lieu of a live demo (research says yes — verify the wording).
4. **Video:** confirm **≤5 min** and that it must be on **YouTube** specifically; confirm it's a required attachment.
5. **Writeup:** confirm **≤2,500 words** and the required elements (title, subtitle, Track selection, Media Gallery + cover image).
6. **Track scope:** confirm Concierge's **"personal/family/social + keep personal info safe"** framing — make sure a clinic-booking agent reads as *personal-life-simplification + PII-safety*, not pure business automation (else it leans "Agents for Business").
7. **Antigravity / Agents CLI:** confirm what these course concepts mean in this edition (research flagged them as listed-but-not-deep-dived) in case you want a cheap 4th concept.
8. **Team / submission limits:** one submission per team, max team size 5 — confirm if collaborating.
9. **Key/secret rule:** confirm the "DO NOT INCLUDE ANY API KEYS OR PASSWORDS IN YOUR CODE" gate and the **CC-BY 4.0** winner license (you'd open-source the winning code).
10. **Live-deploy requirement:** confirm judging does **not** require a live endpoint (research says it doesn't) so the repo-only floor is safe.

---

### Verification notes
- Re-read `clinic.py` (160 lines): `BUSY_WEEKLY = {0:{9,10,11}, 2:{15,16}, 4:{16,17}, 5:{12,13}}` and `_confirmation_code` (SHA1, first 4 hex, upper, `VX-` prefix, seed `name|phone|preferred_datetime`) confirmed **exactly** as cited.
- `CLAUDE.md` confirms the EN voice is **Eryn** (not "a US voice"), per-turn swap via `UpdateSpeak`, and a live demo at **demo.vexiumdata.com** — all of which the Gemini port **drops** (native audio = one multilingual voice, no swap).
- All competition-rule facts (≤2,500 words, ≤5-min YouTube, Jul 6 PT, repo-OK, 3-concept gate) come from browser-rendered Kaggle DOM per the research; **re-verify live before submitting** (§8).
