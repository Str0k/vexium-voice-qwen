# Vexium Voice Receptionist — Build Plan

Execute ONE phase per Claude Code session. After each phase: test the milestone,
commit, then run `/clear` and start the next phase. This file persists on disk and
survives context resets — check off items as you complete them.

---

## Phase 0 — Pre-flight (human: Cristian, before any code)  — STATUS: ~done except Twilio
- [ ] Buy a **US** Twilio phone number; note Account SID + Auth Token  ← ONLY remaining blocker (needed for Phase 3, not Phase 1)
- [x] Confirm Deepgram API key works (includes $200 free credit)
- [x] AWS Bedrock: enable **Claude model access** in your region (Console → Bedrock → Model access)
- [x] Create an IAM user with `bedrock:InvokeModel` permission; note keys, region, and Bedrock model ID
- [~] ElevenLabs — NOT needed for the MVP. (We use Deepgram Aura-2 for TTS. ElevenLabs *Agents*
      is a different product we don't use; a plain ElevenLabs key is only an optional voice upgrade later.)
- [x] (Fallback) Anthropic API key — in case Bedrock model access is delayed
- [x] Install locally: Python 3.11+, git  ( ngrok pending — only needed at Phase 3 )
- [x] Fill `.env` with your values: copy `.env.example` → `.env`, then DEEPGRAM_API_KEY + AWS creds + BEDROCK_MODEL_ID (Claude 3.5 was EOL — switched to claude-haiku-4-5-20251001)

---

## Phase 1 — Skeleton + microphone test (NO phone yet)
**Goal:** validate the Deepgram + LLM + TTS loop locally via mic, before touching telephony.
- [x] Reference base: official `deepgram-devs/sts-twilio` (built a minimal `dev_client.py` instead of cloning the Twilio bridge — phone comes in Phase 3)
- [x] Set up project structure, virtualenv, dependencies, and .env loading (`agent_config.py`, `.env.example`, `requirements.txt`)
- [x] `dev_client.py` written: mic → Voice Agent (linear16 16k) → speaker, with barge-in + live transcript
- [x] Configure Deepgram Voice Agent: Nova-3 STT, bilingual receptionist greeting/prompt, Aura-2 TTS
- [x] LLM: chose `aws_bedrock` (Claude on Bedrock) — config validated, nesting correct
- [x] `.env` filled, `dev_client.py` run → agent greets in Spanish (Estrella) and converses fluidly with sub-second latency (2026-05-28)

**✋ MILESTONE — STOP & TEST:** ✅ DONE 2026-05-28 — Mic loop validated in Spanish with Aura-2 Estrella (Mexican female) + Claude Haiku 4.5 on Bedrock us-east-2.

---

## Phase 2 — Bilingual receptionist brain
**Goal:** a receptionist that books appointments in Spanish AND English.
- [x] Set LLM = Claude via **AWS Bedrock** (Haiku 4.5, us-east-2 — already validated in Phase 1)
- [x] Bilingual STT: `flux-general-multi` v2, `language_hints:[en,es]`, `agent.language=multi` (in `.env`)
- [x] Tuned bilingual SYSTEM PROMPT (sound-human rules, one-language-per-reply, say numbers/dates aloud)
- [x] Added client-side `book_appointment` function (`agent.think.functions` in `agent_config.py`)
- [x] `FunctionCallRequest` handler in `dev_client.py` → prints `📅 BOOKING:` + sends `FunctionCallResponse`
- [x] TTS upgraded to `aura-2-selena-es` (LatAm female, one of 5 Aura-2 voices that code-switch EN/ES)
- [x] **TESTED (mic):** full booking validated in Spanish (BOOKING captured, 4 fields). English path
      validated later through the web demo + per-language voice switch. ✅

**✋ MILESTONE — DONE (2026-05-29).** Bilingual booking validated, then iterated far past it — see Phase 2.5.

---

## Phase 2.5 — Web demo + premium voice + public deploy  — STATUS: ✅ DONE (2026-05-31)
Beyond the original plan; this is the LIVE demo today (https://demo.vexiumdata.com).
- [x] FastAPI WS bridge `server.py` (browser ↔ Deepgram), reuses `agent_config` + `clinic`
- [x] Next.js frontend `web/` — premium bilingual landing (ES/EN toggle, default EN), in-browser call
      widget, audio-reactive "Aurora Orb", live transcript, full-call recording, SVG logo, dental demo selector
- [x] **ElevenLabs Flash v2.5 BYO-TTS** — Regina (MX) for ES + a US voice for EN, swapped per detected
      language via `UpdateSpeak`; Aura-2 fallback. Voice saved-defaults tuned via API.
- [x] **Enterprise "Sofía" prompt** (identity lock, name read-back + spelling, grouped phone read-back,
      mandatory pre-tool stall line, interruption/silence rules, objections playbook, usted register)
- [x] **Deepgram tuning** — `eot 0.75` + `eager 0.6` + dental `keyterms`. All smoke-tested vs the live API.
- [x] **Public deploy = Cloudflare named tunnel** (`vexium-demo`) → `demo.vexiumdata.com` (frontend + bridge,
      same-origin; `/ws` → :8000, rest → :3000). Runs from the laptop (3 processes; see `comandostart.md`).
- [x] Pushed to GitHub `Str0k/vexium-voice` (private). **Vercel = discarded** (frontend-only, can't run the bridge).
- [x] **Migrated to the `ram-linux` server (2026-06-01)** — 3 systemd services (`vexium-bridge` :8100,
      `vexium-web` :3100, `vexium-tunnel`), active+enabled, 24/7, off the laptop. (Hurdle: ram-linux's
      slow WiFi truncated the SWC binary on `npm install`; fixed by downloading it on the laptop + LAN
      transfer + `npm install --offline`.) See `comandostart.md`.

**✋ MILESTONE — DONE.** Public web demo live 24/7 (ram-linux) with bilingual premium voices + enterprise brain.

---

## Phase 3 — Connect Twilio (real phone call)
**Goal:** call a real number and talk to the agent.
- [ ] Wire the Twilio Media Streams ↔ Deepgram bridge (the VoiceAgentSession class)
- [ ] Start ngrok; set the Twilio number's Voice webhook to the ngrok URL
- [ ] Verify mulaw 8kHz audio both directions (the reference repo handles this — confirm)

**✋ MILESTONE — STOP & TEST:** Call your Twilio number from your phone; book an appointment by voice. Commit.

---

## Phase 4 — Capture booking + harden
**Goal:** a reliable demo with the booking captured.
- [ ] `book_appointment` writes structured JSON (console + appointments.json)
- [ ] Silence handling (prompt "¿Sigue ahí?" / "Are you still there?" after dead air)
- [ ] Barge-in / interruption handling (wired to Twilio `clear` event)
- [ ] Mid-call language switching; handle "repeat that" / "repítemelo"
- [ ] Tune greeting, latency, and voice

**✋ MILESTONE — STOP & TEST:** End-to-end demo; appointment saved to file. Commit.

---

## Phase 5 — Record demo
Voice is now ElevenLabs (Regina MX / US) and the demo is already live at
**https://demo.vexiumdata.com** — so this is mostly "hit record".
- [x] Voice/latency dialed in (ElevenLabs Flash v2.5 + enterprise prompt + Deepgram tuning)
- [ ] Record a demo (screen of the web call, or a real phone call once Phase 3 is done) for
      Isa @ Twilio, NVIDIA Inception, the ElevenLabs grant, the Twilio Searchlight app, and the pitch deck

**✋ MILESTONE:** A polished demo asset. (Hosting = Phase 6 — AWS. Fly.io idea dropped.)

---

## Phase 6 — Deploy to AWS (run 24/7 without the laptop)
**Goal:** the demo runs in the cloud so it works without Cristian's machine on.
**Simplest path (given the Cloudflare tunnel already works):** a **Lightsail box running bridge +
frontend + cloudflared** — move the exact 3 processes from the laptop to an always-on box. The
Cloudflare tunnel provides TLS + the `demo.vexiumdata.com` hostname, so **no ALB/ACM/public IP
needed**. Auto-deploy on `git push` via a small GitHub Action (SSH `git pull` + restart).
**Hosting decision (researched 2026-05-28):** Lightsail first, graduate to ECS Fargate at scale.
App Runner is DEAD; API Gateway WS + Lambda does NOT fit continuous audio. The Track A/B below is
the Twilio-centric variant (use it if/when serving Twilio instead of the browser demo).

### Track A — Lightsail (do this first, MVP)
- [ ] Dockerize the server (`server.py`: FastAPI/Starlette + uvicorn; routes: `GET /health`,
      `POST /voice` returns TwiML `<Connect><Stream wss://…/twilio>`, `WS /twilio` = the bridge)
- [ ] Push image to **Lightsail Container Service (Micro, ~$10/mo)** in **us-east-2** (near Bedrock)
- [ ] Set secrets as deployment env vars (Deepgram key, AWS creds, Bedrock model) — NOT in the image
- [ ] Point a domain (e.g. `api.vexiumai.com`) at the Lightsail HTTPS endpoint; **verify `wss://` works**
- [ ] Set the Twilio number's Voice webhook → the HTTPS endpoint; confirm a real call end-to-end
      and that the WSS connection holds for the whole call

### Track B — ECS Fargate + ALB (later, at scale; Twilio's reference pattern)
- [ ] Image to **ECR**; **Fargate** service (start 0.5 vCPU / 1 GB) in a **public subnet** (avoid NAT cost)
- [ ] **ALB + ACM cert** for TLS/`wss://`; enable sticky sessions on the target group; `/health` check
- [ ] **IAM Task Role** for Bedrock (drop the static access keys); secrets in **Secrets Manager**
- [ ] Autoscale tasks on concurrent connections (CloudWatch). (NLB only if you need static IP / min latency.)

**✋ MILESTONE:** A real phone call is answered by the cloud-hosted agent and books an appointment.

---

## Phase 7 — SaaS productization (multi-tenant: each business self-serves)
**Goal:** any business signs up, enters its info, gets its own voice agent on its own number.
**Researched 2026-05-28** (Vapi/Retell/Synthflow patterns + AWS multi-tenant guidance).

**Core architecture:**
- **Multi-tenancy = pooled model:** shared DB, `tenant_id` on EVERY table, every query filters on it.
  Add **Postgres Row-Level Security (RLS)** as a safety net ("a single missing tenant filter is a
  data breach"). Separate DB/schema only for enterprise compliance later.
- **Per-tenant config lives in the DB, loaded per call:** business name/type, greeting, system prompt,
  services + prices, hours/booking rules, voice, language. (Today these are hardcoded in `clinic.py`
  + `agent_config.py` — Phase 7 moves them into a `tenants` / `agent_config` table.)
- **Inbound number → tenant routing:** map each Twilio phone number to a `tenant_id`; on a call, resolve
  the tenant by the dialed (`To`) number (or a TwiML custom parameter), load its config, and build the
  Deepgram `Settings` dynamically per call.
- **Onboarding:** signup → intake form (business info, services, hours, pick a voice) → provision/assign
  a Twilio number → agent live.
- **Dashboard:** web app (Next.js) — edit config, view bookings/call logs/transcripts, manage billing.
- **Billing:** Stripe subscription + usage metering (minutes); enforce plan limits.
- **Data store:** Postgres (RDS or Supabase) for tenants/config/bookings/call logs.
- **Evolution:** start as a modular monolith; extract services (gateway, agent runtime, config store,
  conversation store, billing meter) past ~500 active tenants.

**Suggested build order:**
- [ ] 1. Externalize config to a DB; load a tenant's config per call by dialed number (dogfood with 1 tenant = you)
- [ ] 2. Minimal web dashboard + auth (view/edit your own agent + see bookings)
- [ ] 3. Per-tenant Twilio number provisioning (subaccounts or a number pool)
- [ ] 4. Stripe subscriptions + per-minute usage metering + plan limits
- [ ] 5. Self-serve onboarding/intake flow (no manual setup)
- [ ] 6. Harden isolation (RLS), logging, analytics, per-tenant appointments export

**✋ MILESTONE:** A second business onboards itself and takes a real, fully-isolated call.

---

## Bilingual receptionist SYSTEM PROMPT (starting point — tune in Phase 2)

```
You are the virtual receptionist for {{BUSINESS_NAME}}, a {{BUSINESS_TYPE}}
(e.g., a dental clinic). You answer inbound phone calls and your primary job is
to book appointments.

LANGUAGE
- Detect the caller's language from their first words and respond in that language
  (English or Spanish). If they switch languages mid-call, switch with them.
- Speak naturally and warmly, like a friendly human receptionist — not a robot.

VOICE STYLE
- Keep every response SHORT (1–2 sentences). This is a phone call, not an essay.
- Ask one question at a time. Never read long lists.
- Use natural spoken phrasing, contractions, and a calm, helpful tone.

YOUR GOAL: BOOK AN APPOINTMENT
Collect, one at a time:
1. The caller's full name
2. The reason for the visit / service they need
3. Their preferred date and time
Then read the details back and confirm before finalizing. When confirmed, call the
book_appointment function with the collected information.

GUIDELINES
- If you didn't catch something, politely ask them to repeat it.
- If they go off-topic, gently guide back to booking.
- If they ask something you don't know (prices, specific doctor availability),
  say you'll have a team member follow up, and still capture their info.
- Never invent specific availability, prices, or medical/legal advice.
- Confirm spelling of the name if unsure.
- End warmly once the appointment is booked.

Begin every call with a brief bilingual-friendly greeting, e.g.:
"Thank you for calling {{BUSINESS_NAME}}, how can I help you today?"
(and be ready to continue in Spanish if they respond in Spanish).
```

---

## Notes for Claude Code
- Start each session by reading CLAUDE.md (auto-loaded) and this PLAN.md.
- Do NOT attempt multiple phases in one session — context stays clean and focused.
- Before coding Deepgram-specific calls, fetch the current Deepgram Voice Agent docs
  (the API evolves; append /llms.txt to docs URLs for an AI-readable version).
- After each phase, summarize what changed and what to test, then wait.
