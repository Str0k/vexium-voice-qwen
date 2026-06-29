# Vexium Voice — Bilingual AI Voice Receptionist (MVP)

Bilingual (EN/ES) AI voice receptionist that answers calls, quotes services, checks
availability, and books appointments. Built on **Deepgram Voice Agent** (Flux STT +
orchestration) with **Claude Haiku 4.5 on AWS Bedrock** (LLM) and **ElevenLabs Flash v2.5**
(TTS — a Mexican voice for Spanish, a US voice for English, swapped per turn).

> **New here / picking this up?** Read **`CONTEXT.md`** first (full handoff), then `CLAUDE.md`
> (decisions), `PLAN.md` (phases), and `comandostart.md` (how to launch the demo).

**Live demo:** https://demo.vexiumdata.com — runs **24/7 on the `ram-linux` server** (systemd
services + Cloudflare tunnel). Nothing to start manually; survives reboots. To operate/update it
(status, restart, logs, deploy a change) see **`comandostart.md`**.

## Local development (on the laptop)

```powershell
# voice bridge (port 8000)
.\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
# frontend (port 3000) -> http://localhost:3000  (auto-connects to the local bridge)
cd web ; npm install ; npm run dev
```
Edit → `git push`. To deploy to production: `git pull` + `npm run build` + restart the services on
ram-linux (see `comandostart.md`).

## Quick mic test (no web, no tunnel)

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in the keys (see CLAUDE.md)
python dev_client.py          # talk to it; live transcript prints in the terminal
```

## Quick mic test (no web, no tunnel)

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in the keys (see CLAUDE.md)
python dev_client.py          # talk to it; live transcript prints in the terminal
```

## Stack (runtime)
- **STT:** Deepgram Flux `flux-general-multi` v2, bilingual, `eot 0.75` / `eager 0.6` + dental keyterms.
- **LLM:** Claude Haiku 4.5 on AWS Bedrock (us-east-2). Enterprise "Sofía" system prompt.
- **TTS:** ElevenLabs Flash v2.5 (BYO inside Deepgram) — Regina (MX) / US voice per language via
  `UpdateSpeak`. Deepgram Aura-2 is the free fallback if `ELEVENLABS_VOICE_ID` is unset.
- **Functions (client-side):** `check_availability` + `book_appointment` (logic in `clinic.py`).
- **Frontend:** Next.js (App Router) in `web/`. **Deploy now:** `ram-linux` server (systemd) +
  Cloudflare tunnel, 24/7. **Phase 6 (optional upgrade):** AWS Lightsail.

## Status
Phases 1 & 2 + the web demo are **done and live 24/7** (on the `ram-linux` server, migrated off the
laptop 2026-06-01); the demo now has **two verticals** (dental + restaurant), switchable in the call
widget. Twilio (real phone) is **Phase 3, not built yet**. See `PLAN.md` for the full
roadmap (Phase 6 = AWS upgrade, Phase 7 = multi-tenant SaaS).

### Fine-tuned LLM pilot (ready to integrate)
- **Model:** [`VexiumZZ/qwen2.5-7b-vexium-voice`](https://huggingface.co/VexiumZZ/qwen2.5-7b-vexium-voice)
- **Base:** `Qwen2.5-7B-Instruct` · **Method:** full fine-tuning on a single H100
- **Data:** 273 synthetic dental conversations (Sofía vertical)
- **Loss:** 2.846
- **Usage:** not connected to the live demo yet; needs an OpenAI-compatible inference endpoint (vLLM, Together, Fireworks, DeepInfra) plugged into Deepgram's `think.provider`.
- **Project docs:** see `Documents/nvidiabrev/04-plan-vexium-finetuning.md` for training plan and serving options.

## Files
| File | Purpose |
|---|---|
| `server.py` | FastAPI WebSocket bridge (browser ↔ Deepgram); per-language voice switch |
| `agent_config.py` | Builds the Deepgram `Settings` + the Sofía prompt; `speak_for_language` / `detect_language` |
| `clinic.py` | Dental vertical: services/prices, hours, `check_availability`, `book_appointment` |
| `restaurant.py` | Restaurant vertical: menu/prices, specials, `check_table_availability`, `book_reservation` |
| `dev_client.py` | Laptop-mic client (test without the web) |
| `web/` | Next.js frontend (landing + in-browser call widget + recording). See `web/README.md` |
| `.env.example` | Template for secrets (copy to `.env`, never commit `.env`) |
| `CONTEXT.md` / `CLAUDE.md` / `PLAN.md` / `comandostart.md` | Handoff, decisions, roadmap, launch commands |

## Troubleshooting
- **`Error: UNPARSABLE_CLIENT_MESSAGE` / INVALID_SETTINGS:** an invalid field in the Deepgram
  `Settings`. Smoke-test before shipping (connect → expect `SettingsApplied`). Note: Deepgram rejects
  `speed`/voice_settings for the `eleven_labs` speak provider.
- **Bridge call doesn't connect from the public URL:** ensure the bridge (:8000) and the tunnel are both up.
- **Bedrock auth/region error:** confirm Claude model access in us-east-2 + IAM `bedrock:InvokeModel`.
- **Changed `.env`?** Restart the bridge (it loads env at startup).
