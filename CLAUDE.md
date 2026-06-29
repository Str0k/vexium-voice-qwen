# Vexium AI — Bilingual Voice Receptionist MVP

> **▶ Retomando? Lee `CONTEXT.md` primero** — tiene el estado actual y cómo seguir.

## What we're building
A bilingual (English/Spanish) AI voice receptionist that answers calls, quotes services,
checks availability, and books appointments, capturing each booking as structured data.
MVP for Vexium AI (vexiumai.com) — voice agents for the US Hispanic and LATAM markets.

## Status (2026-06-02) — read CONTEXT.md for the full handoff
Phases 1 & 2 + a **web demo** are DONE. **Public demo LIVE 24/7: https://demo.vexiumdata.com**
— runs on the **`ram-linux` server** (systemd services, via Cloudflare tunnel), migrated off the
laptop 2026-06-01; **demo domain switched to `demo.vexiumdata.com` 2026-06-02**
(`demo.conexionks.com` was retired from the tunnel 2026-06-02 — returns 404; its DNS record was
left in place but is unused). Runtime stack: Deepgram **Flux** STT + **Claude Haiku 4.5**
on Bedrock + **ElevenLabs Flash v2.5** TTS (Regina MX for ES / a US voice for EN, swapped per
turn via UpdateSpeak; Aura-2 fallback). Enterprise prompts — **two demo verticals** switchable in the widget (`?v=`): dental ("Sofía") + restaurant ("Valentina" / Vexium Cocina). **Twilio (real phone) is
Phase 3, not built yet.** Git author = **Cristian Ramirez <marketyuc@gmail.com>** (Str0k), NOT bpeakdigital.

## Architecture
Two transports today; Deepgram Voice Agent owns turn-taking/barge-in/STT+LLM+TTS — do NOT
rebuild a custom pipeline.
- **Web demo (LIVE):** Browser (Next.js in `web/`) → `server.py` (FastAPI WS bridge) → Deepgram
  Voice Agent. Browser sends linear16 16k, plays 24k, records the call. Served same-origin via
  the Cloudflare tunnel (`/ws` → bridge :8000, rest → frontend :3000). See `comandostart.md`.
- **Mic dev:** `dev_client.py` (laptop mic → Voice Agent). For quick local tests.
- **Phone (Phase 3, TODO):** Twilio Media Streams (mulaw 8kHz) → the same bridge. Needs a US number.

Voice Agent internals: STT Flux `flux-general-multi` v2 · LLM Claude via AWS Bedrock (`aws_bedrock`)
· TTS ElevenLabs Flash v2.5 (BYO) with Aura-2 fallback. Functions `check_availability` +
`book_appointment` (client-side, logic in `clinic.py`). Booking captured as structured data.

**Fine-tuned LLM pilot (not yet wired to production):** we trained a full fine-tune of
`Qwen2.5-7B-Instruct` on 273 synthetic dental conversations generated locally with a
`Qwen2.5-32B-Instruct` teacher. Result: [`VexiumZZ/qwen2.5-7b-vexium-voice`](https://huggingface.co/VexiumZZ/qwen2.5-7b-vexium-voice)
(loss 2.846). To use it, deploy behind an OpenAI-compatible endpoint (vLLM/Together/Fireworks/DeepInfra)
and point Deepgram's `think.provider.endpoint.url` to it. Docs and serving notes live in
`Documents/nvidiabrev/04-plan-vexium-finetuning.md`.

## Decisions locked (2026-05-28, from verified research)
- **Orchestrator = Deepgram Voice Agent, NOT ElevenLabs Agents.** ElevenLabs Agents is a
  separate competing platform; we do NOT need its access. ElevenLabs is only an *optional*
  TTS voice inside Deepgram, added later.
- **LLM = Claude via AWS Bedrock** (`think.provider.type: aws_bedrock`). `credentials` nests
  inside `provider`; `endpoint.url` (https://bedrock-runtime.{region}.amazonaws.com/) is a
  sibling of `provider`, inside `think`, and is REQUIRED. Managed `anthropic` is the 1-line
  fallback if Bedrock access lags.
- **TTS = ElevenLabs Flash v2.5 (ACTIVE)** as BYO-TTS inside Deepgram. Per-language voice via
  `UpdateSpeak`: ES → Regina (MX) `9Godp7dNohUvXk6qp0gS`, EN → **Eryn** (US/American) `DXFkLCBUTmvXpp2QwZjA`
  (bridge picks each turn's language: Deepgram Flux `languages[0]` if present, else the `detect_language`
  heuristic — switches on any clear ES/EN signal, no hysteresis; ambiguous turns stay put). **Deepgram does NOT forward `speed`/voice_settings for
  `eleven_labs`** (it rejects the Settings) — only `type`/`model_id`/`language_code`. Tune tone as
  each voice's SAVED DEFAULTS in ElevenLabs (done: stability 0.5, similarity 0.78, style 0,
  speaker_boost on; ES speed 0.97). **Deepgram Aura-2** (`aura-2-selena-es`) is the free fallback
  (used automatically if `ELEVENLABS_VOICE_ID` is unset). ElevenLabs Starter ($6/mo) = commercial.
- **STT:** Nova-3 for the Phase-1 loop check → Flux (`flux-general-multi`, version `v2`,
  `language_hints:["en","es"]`) for bilingual Phase 2 — native turn-taking + barge-in,
  ~260ms p50, no custom VAD.
- **Voice Agent WS:** `wss://agent.deepgram.com/v1/agent/converse`, auth via
  `subprotocols=["token", DEEPGRAM_API_KEY]`. Twilio audio = mulaw 8kHz; mic dev = linear16.
- **Deployment NOW = `ram-linux` server (24/7) + Cloudflare named tunnel** (`vexium-demo`) →
  `demo.vexiumdata.com`. 3 systemd services on ram-linux (active+enabled): `vexium-bridge` (:8100),
  `vexium-web` (Next.js prod :3100), `vexium-tunnel` (cloudflared). Migrated off the laptop 2026-06-01;
  see `comandostart.md` to operate/update. **Vercel = discarded** (frontend-only, can't run the WS bridge).
- **Hosting (Phase 6, optional upgrade) = AWS** (uses the $10k credits; better for an investor-facing,
  datacenter-grade demo). Simplest given the tunnel: a **Lightsail box running bridge + frontend +
  cloudflared** (no ALB/cert — the tunnel provides TLS). Graduate to **ECS Fargate** at scale. **App Runner
  is DEAD** (no WebSockets + closed to new customers 2026-04-30); **API Gateway WS + Lambda does NOT
  fit** continuous audio. Deploy in **us-east-2** (next to Bedrock). SaaS multi-tenant = **Phase 7**.
- **Base repo reference:** `deepgram-devs/sts-twilio` (official minimal Twilio bridge).
- **AWS MCP:** `.mcp.json` configures aws-api (read-only) + aws-pricing + aws-knowledge via
  `uvx` and the `vexium` AWS profile. Launch Claude Code from this folder to load it.

## Tech stack
- Python 3.11+ async — FastAPI WebSocket bridge (`server.py`) + mic client (`dev_client.py`)
- Deepgram Voice Agent API (single voice-to-voice endpoint); ElevenLabs Flash v2.5 BYO-TTS
- AWS Bedrock for Claude (BYO LLM: endpoint URL + AWS creds; model ID passed through)
- Frontend: **Next.js (App Router)** in `web/` — landing + in-browser call widget + recording
- **Cloudflare tunnel** for the public demo (dev/now); AWS Lightsail → ECS Fargate for deploy (Phase 6)
- Twilio Programmable Voice + Media Streams = Phase 3 (not built yet)

## Reference docs (pull the LATEST before writing code)
- Deepgram Voice Agent + Twilio: https://developers.deepgram.com/docs/twilio-and-deepgram-voice-agent
- Deepgram Voice Agent LLM models (Bedrock BYO): https://developers.deepgram.com/docs/voice-agent-llm-models
- Official Twilio+Deepgram inbound voice agent tutorial + repo (2026)
- TIP: append /llms.txt to any Deepgram docs URL for an AI-readable index, or .md for markdown

## Environment variables (.env — NEVER commit; see .env.example)
DEEPGRAM_API_KEY=
AWS_ACCESS_KEY_ID= / AWS_SECRET_ACCESS_KEY= / AWS_REGION=us-east-2 / BEDROCK_MODEL_ID=
DG_LISTEN_MODEL=flux-general-multi / DG_LISTEN_VERSION=v2 / DG_LANGUAGE_HINTS=en,es
DG_EOT_THRESHOLD=0.75 / DG_EAGER_EOT_THRESHOLD=0.6 / DG_KEYTERMS=... (dental vocab)
ELEVENLABS_API_KEY= / ELEVENLABS_VOICE_ID=<es> / ELEVENLABS_VOICE_ID_EN=<en> / ELEVENLABS_MODEL_ID=eleven_flash_v2_5
DG_SPEAK_MODEL=aura-2-selena-es   # fallback voice when ElevenLabs is unset
TWILIO_* (Phase 3) / ANTHROPIC_API_KEY (managed-LLM fallback)
# Web frontend: web/.env.local NEXT_PUBLIC_BRIDGE_URL (blank = same-origin /ws auto)

## Conventions
- Secrets live in .env (gitignored). Never hardcode keys anywhere.
- **Git author for this repo = Cristian Ramirez <marketyuc@gmail.com>** (already set repo-local).
- Before changing Deepgram `Settings` (speak/listen providers), **smoke-test** against the live API
  (connect → expect `SettingsApplied` + audio, not `Error`) — invalid fields get rejected wholesale.
- Test with `dev_client.py` (mic) or the web demo. Twilio = Phase 3.
- Commit after each working chunk with a clear message; push to GitHub (Str0k/vexium-voice).

## Don'ts
- Don't buffer the full LLM response before starting TTS — stream it (latency is everything in voice).
- Don't commit .env or any credentials.
- Don't hand-roll STT/TTS orchestration — Deepgram Voice Agent owns that.
- Don't use LATAM phone numbers yet (regulatory bundles). Use a US number for the MVP.

## Build plan
The full phased plan lives in PLAN.md. Execute ONE phase per session, test the
milestone, commit, then clear context and start the next phase. Update PLAN.md
checkboxes as you complete each item.
