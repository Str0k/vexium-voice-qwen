# Vexium Voice — Qwen Edition (Qwen Cloud Hackathon fork)

> **¿Retomando? Lee `CONTEXT.md` primero** — estado actual y cómo seguir.
> Este repo es el FORK para el **Global AI Hackathon Series with Qwen Cloud**
> (Devpost, deadline **Jul 9 2026 2pm PT**, objetivo interno **Jul 8**). El original
> (Claude/Bedrock, demo público) vive en `C:\Users\psiqu\vexium-voice`.

## What this is
Bilingual (EN/ES) AI voice receptionist whose **brain is qwen3-max on Alibaba Cloud
Model Studio** (DashScope intl, OpenAI-compatible). Books appointments (Cal.com or
simulated), collects Stripe deposits, sends SMS (Alibaba/Twilio/simulated), remembers
callers, schedules reminders, escalates to humans, **scores every call with Qwen as a
judge**, and streams ROI to a live dashboard. Two verticals: dental (Sofía) y
restaurante (Valentina).

## Submission target (see docs/SUBMISSION.md for the full plan)
- Track 4 **Autopilot Agent** · repo público con licencia MIT visible · video <3 min ·
  diagrama de arquitectura · **backend corriendo en Alibaba Cloud + prueba grabada**
  (docs/DEPLOY_ALIBABA.md) · demo accesible hasta Jul 31 · todo en inglés.
- Judging: 30% uso técnico de Qwen Cloud APIs · 30% arquitectura/modularidad/manejo de
  errores · 25% valor de negocio · 15% presentación/docs.

## Architecture (two paths, one brain)
- **Voice:** browser → `server.py` (FastAPI WS `/ws`) → Deepgram Voice Agent (Flux STT,
  turn-taking, barge-in) con `think` = **qwen3-max** (`agent_config._think_block`).
  Voz ElevenLabs por idioma vía UpdateSpeak; Aura-2 fallback.
- **Text (sin mic, solo requiere DASHSCOPE_API_KEY):** `/chat` → `qwen_brain.run_turn`
  (loop de function calling) + `/tts` con **qwen3-tts-flash**. Mismo prompt y tools.
- **Persistencia:** Alibaba **Tablestore** (`integrations/tablestore_store.py`) con
  **fallback in-memory idéntico en API** cuando faltan credenciales (`store.backend()`).
  Tablas `vx_events/bookings/callers/tenants/reminders` (provision:
  `scripts/provision_tablestore.py`).
- **Dashboard:** `/dashboard` (Next.js) ← SSE `/events` + `/feed` + `/status`.
- **Fallbacks honestos:** Cal.com/Stripe → "simulated"; SMS → "skipped"; todo visible en
  el panel Cloud stack. Un clon fresco demuestra TODO con solo DASHSCOPE_API_KEY.

## Commands
```powershell
python -m pytest -q                    # 44 tests
python -m uvicorn server:app --port 8000
cd web ; npm run dev                   # localhost:3000 (usa bridge :8000 en localhost)
```

## Conventions / gotchas
- Git author de este repo = **Cristian Ramirez <marketyuc@gmail.com>** (Str0k).
- Secrets solo en `.env` (gitignored). Nada de keys en código ni en commits.
- El SDK real de Tablestore devuelve `(consumed, row, token)` en get_row y 4-tupla en
  get_range — SIEMPRE pasar por los helpers `store.get_attrs/put_attrs/_scan`.
- Deepgram NO reenvía `speed`/voice_settings para eleven_labs; tuning = saved defaults.
- Flux rechaza `agent.language`; detección por turno (`detect_language` + `languages[0]`).
- `BUSY_WEEKLY`: lunes 9/10/11am siempre ocupado → demo determinista de alternativas.
- El modo texto puntúa con el juez SOLO conversaciones que reservan (server.py /chat).
- En producción same-origin: rutear `/ws /chat /tts /summary /events /feed /status
  /run-due-reminders` al bridge (ver Caddyfile en docs/DEPLOY_ALIBABA.md).

## Docs map
`README.md` (submission-facing, EN) · `docs/SUBMISSION.md` (checklist + guion video +
texto Devpost) · `docs/DEPLOY_ALIBABA.md` (ECS + prueba) · `docs/BLOG_POST.md` (draft
Blog Award) · `docs/screenshots/` · `docs/internal/` (material del fork Gemini/Kaggle,
no relevante aquí) · `CONTEXT.md` (handoff en español).
