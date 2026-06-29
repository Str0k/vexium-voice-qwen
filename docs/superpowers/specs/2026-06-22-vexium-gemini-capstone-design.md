# Design Spec — Sofía: Vexium Concierge Agent (Gemini/ADK) for the Kaggle Capstone

**Author:** Cristian Ramirez · **Date:** 2026-06-22 · **Status:** APPROVED (full reframe locked)
**Competition:** Kaggle "AI Agents: Intensive Vibe Coding Capstone Project" (`vibecoding-agents-capstone-project`) — **Track: Concierge Agents**
**Deadline:** July 6 2026, 11:59 PM PT *(MUST re-verify on the live page — some sources say Jun 30; see §9)*
**Source app:** `C:\Users\psiqu\vexium-voice\` (Sofía / Vexium Dental vertical)
**Supporting research:** `KAGGLE_DOSSIER.md` (verified dossier — full reuse map, video shot-list, full risk register)

---

## 1. Goal & success criteria

Adapt the existing deployed Vexium voice receptionist ("Sofía", dental vertical) into a **Gemini-based multi-agent system** submitted to the Kaggle Concierge capstone, optimized to **place in the Concierge track**, not merely to qualify.

**Success criteria:**
1. **Valid submission** by deadline: public GitHub repo + ≤2,500-word Kaggle Writeup (Track = Concierge) + cover image + ≤5-min YouTube video.
2. **Passes the hard gate:** demonstrably implements **≥3 of 6 course concepts** — locked target: **ADK multi-agent + MCP server + Security/PII** (+ Deployability as a likely 4th).
3. **Reuses** the existing Sofía prompt, function schemas, and `clinic.py` booking logic (no rebuild of the "intelligence").
4. **Voice** bilingual EN/ES demo works as the "wow" layer, with a **text fallback** so a mic/Live failure degrades gracefully.
5. A guaranteed **floor** exists at every point: even if voice/deploy fail, the repo + text demo + video is a complete, competitive submission.

---

## 2. Locked decisions

- **Strategy:** full win-optimized reframe. ADK multi-agent + MCP + PII security is the **scoring spine (Tier A)**; voice/text app is the **demo/wow layer (Tier B)**. Build Tier A first.
- **Vertical:** Dental / "Sofía" only (most complete; exists locally).
- **Language:** bilingual EN/ES is the headline differentiator (native to Gemini native-audio; prompt enforces "stay in caller's language").
- **Model:** Gemini (text) for the ADK agents; `gemini-3.1-flash-live-preview` (Preview, v1alpha) for voice. **Never gate the submission on the preview voice model.**
- **Deliverable backbone:** public **GitHub repo** (not an AI Studio link — AI Studio is NOT required). Live demo URL is optional polish.
- **Key safety:** the Gemini API key is **server-side only**; the browser uses **ephemeral tokens**. No key in client code (June-19-2026 unrestricted-key rejection makes this mandatory).

---

## 3. Corrected competition facts (grounds the whole plan)

These corrected earlier wrong assumptions (which came from the separate, finished `gemini-3` hackathon). All re-verify on the live page (§9):
- **AI Studio app link is NOT required** — a public GitHub repo with setup instructions satisfies the "Public Project Link".
- **Video ≤5 min on YouTube**; **Writeup ≤2,500 words**.
- **~70% of score = implementation**, with a **hard gate of ≥3 of 6 course concepts** (ADK multi-agent, MCP server, Antigravity, Security, Deployability, Agent skills). Prior track winners were multi-agent ADK systems.
- **Judging does NOT require a live endpoint.**

---

## 4. Architecture

```
TIER A — scoring spine (ADK multi-agent + MCP + PII)            [build first, where 70% of points live]
┌──────────────────────────────────────────────────────────────────────────────┐
│  Receptionist Orchestrator (ADK Agent)                                         │
│    instruction = reused Sofía prompt + 4 "human" sections                      │
│    ├── Booking sub-agent (ADK)       → gathers slots, calls tools, returns      │
│    │                                   a strict Pydantic `Booking`             │
│    └── Verification sub-agent (ADK)   → rejects incomplete/unconfirmed booking, │
│                                         forces a retry (self-correction)        │
│  tools ──────────────► MCP server `clinic-mcp`                                  │
│                          check_availability(), book_appointment()              │
│                          (reuses clinic.py logic in Python, ~verbatim)          │
│  PII layer: mask phone (•••• 0182), no raw-phone logging, session-only data    │
└──────────────────────────────────────────────────────────────────────────────┘
TIER B — demo / wow layer (public URL)                          [build after spine]
┌──────────────────────────────────────────────────────────────────────────────┐
│  React/TS app shell ── Text ⇄ Voice toggle                                     │
│    • Chat engine:  generateContent + function-calling loop  (reliable fallback)│
│    • Voice engine: Live API (gemini-3.1-flash-live-preview) via ephemeral token │
│    • Live JSON booking panel (structured-data capture, PII masked)             │
│    • Token-mint endpoint /api/token (server-side; uses:1, short expiry, rate-lim)│
│  Deploy: AI Studio Publish (Starter) OR own Cloud Run; key as server secret     │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Why the spine wins points:** ADK multi-agent (orchestrator + 2 sub-agents) + MCP server + Security covers 3 course concepts; Cloud Run/Publish adds Deployability as a 4th. Voice alone covered ~1.

---

## 5. Components (each = one purpose · interface · dependencies)

**Tier A**
- **A1 `clinic-mcp` (MCP server):** exposes `check_availability(requested_datetime)` and `book_appointment(caller_name, phone, service, preferred_datetime, language)` over MCP. Reuses `clinic.py` (pure, in-memory) almost verbatim in Python. Schemas = reused `agent_config.py` declarations.
- **A2 Receptionist orchestrator (ADK):** owns call flow; `instruction` = Sofía prompt + human sections; `tools` = A1; `sub_agents` = [A3, A4].
- **A3 Booking sub-agent (ADK):** gathers details → `check_availability` → on confirmation `book_appointment`; output = Pydantic `Booking`.
- **A4 Verification sub-agent (ADK):** validates required fields + slot-confirmed + PII well-formed; `{ok, missing[], reason}`; on `ok:false` orchestrator re-asks one question.
- **A5 PII-safety layer:** phone masking helper, no-log discipline, session-only storage, data-policy text in UI + README.

**Tier B**
- **B1 App shell + Text⇄Voice toggle** (reuses orb/i18n/Landing visuals).
- **B2 Chat engine** (`generateContent` + function-calling loop; reliable, mic-free fallback).
- **B3 Voice engine** (Live API; PCM16 16k in / 24k out; server VAD + barge-in flush on `interrupted`; `sessionResumption:{}`; one multilingual voice, no `languageCode`).
- **B4 Token-mint endpoint** (`POST /api/token` → `authTokens.create({uses:1, expiry short, live_connect_constraints})`; per-IP rate limit; key server-side).
- **B5 Booking-logic TS module** (port of `clinic.py` 35–160; Web Crypto SHA-1 `VX-XXXX` must match Python byte-for-byte on a fixed seed).
- **B6 Live JSON booking panel** (renders captured `booking` + `confirmation_code`, PII masked).
- **B7 Deploy/publish** (public no-login URL; fallback ladder §7).

---

## 6. Reuse map (condensed; full table in `KAGGLE_DOSSIER.md` §1)

- **REUSE (text, ~no effort):** Sofía dental prompt + 4 human sections (`agent_config.py`); function schemas `check_availability`/`book_appointment`; clinic profile/hours/services/greeting; **`BUSY_WEEKLY` + SHA1 confirmation-code (demo-critical determinism)**.
- **PORT (Python→TS):** `clinic.py` availability + booking logic + date helpers (Tier B); kept in Python for A1 (MCP).
- **DROP (transport-coupled):** Deepgram Voice Agent/Flux, ElevenLabs BYO-TTS + per-turn voice swap, AWS Bedrock plumbing, FastAPI WS bridge, `detect_language`/`speak_for_language` (native audio auto-language).

**Demo determinism:** `BUSY_WEEKLY = {0:{9,10,11},2:{15,16},4:{16,17},5:{12,13}}` → asking for **Monday 9am** always triggers the "offer alternatives" branch on camera; SHA1 code is deterministic per caller. Freeze a fixed "today" in the prompt before recording.

---

## 7. Plan, publish path & fallback

**Phased plan (Jun 22 → Jul 6, day-by-day in `KAGGLE_DOSSIER.md` §3).** Shape:
- **Phase 0 (Jun 22–23): publish-path spike** — re-verify live rules/deadline; publish a throwaway AI Studio hello-world; confirm a public no-login link; test whether a *published* app can mint Live tokens + run voice. Lock the deploy decision before any feature work.
- **Spine (Jun 24–26):** public repo + ADK scaffold + MCP server (A1) + orchestrator/booking/verification (A2–A4) + PII (A5). **After this, ≥3 concepts are met and a text submission is already valid.**
- **Demo layer (Jun 27–Jul 3):** TS port (B5), chat + JSON panel (B2/B6), shell/toggle (B1), token endpoint (B4), voice engine (B3), deploy (B7).
- **Polish (Jul 4–6):** record 5-min video, writeup + README + cover image, **submit early (by Jul 5)**, Jul 6 = buffer.

**Slip rule:** if voice slips, ship text-only via the same spine + screen-recorded demo. Submission stays valid and competitive.

**Publish fallback ladder (use first that holds):** 1) AI Studio Publish + Voice → 2) AI Studio Publish + text-only (voice as a recorded clip in the video) → 3) own billed Cloud Run export → 4) **repo + video only, no live deploy** (guaranteed floor — never below this).

---

## 8. Risks (top; full register in `KAGGLE_DOSSIER.md` §7)

- **R1 3-concept gate failure** → mitigated by building the ADK+MCP+Security spine first and naming the concepts in writeup/README/video.
- **R3 Deadline confusion (Jun 30 vs Jul 6)** → treat Jun 30 as soft internal target; have a submittable v1 (spine+text) by Jun 30.
- **R4 June-19 unrestricted-key rejection** → never ship a key client-side; server-side secret + ephemeral tokens.
- **R5 Quota drain on public app** → `uses:1`, short expiry, `live_connect_constraints`, per-IP rate limit, prefer own billed Cloud Run; text mode as un-throttled fallback.
- **R6 Preview voice model instability** → mode toggle to text; pre-record a clean voice take.

---

## 9. Open questions — confirm on the LIVE Kaggle page before committing the calendar

1. **Deadline:** Jul 6 11:59 PM PT vs Jun 30? (re-read live Timeline)
2. **3-concept gate:** exact list + how many required; which must show in Code vs Video.
3. **Project Link:** confirm a public GitHub repo (with setup instructions) is accepted in lieu of a live demo.
4. **Video/Writeup:** confirm ≤5 min YouTube + ≤2,500 words + cover image required.
5. **Track scope:** confirm a clinic-booking agent reads as Concierge (personal-life + PII-safety), not "Agents for Business".
6. **Rules gates:** "no API keys/passwords in code"; CC-BY-4.0 winner license; team limits.

---

## 10. Out of scope (YAGNI)

Twilio/phone-in; real calendar integration; multi-clinic/multi-tenant; persistence beyond session; the other 3 verticals (restaurant/ecommerce/inmobiliaria); per-turn voice swapping; any non-Gemini model. (Listed as "future work" in the writeup only.)
