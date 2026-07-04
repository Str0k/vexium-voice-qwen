# Vexium Voice **Qwen Edition** — Contexto y handoff

> **¿Retomando en una sesión nueva? Lee esto primero.** Acompáñalo de `CLAUDE.md`
> (autocargado, decisiones + gotchas), `README.md` (submission-facing, inglés) y
> `docs/SUBMISSION.md` (plan de entrega al hackathon).

**Última actualización: 2026-07-03.**

## 🎯 Qué es este repo
Fork de Vexium Voice para el **Global AI Hackathon Series with Qwen Cloud** (Devpost).
Recepcionista de voz bilingüe EN/ES cuyo **cerebro es qwen3-max en Alibaba Cloud Model
Studio**. El repo original (Claude/Bedrock + demo público 24/7) sigue intacto en
`C:\Users\psiqu\vexium-voice` — **no tocar aquello desde aquí**.

## 🏁 La competición (verificado 2026-07-03, ver docs/SUBMISSION.md)
- **Devpost:** qwencloud-hackathon.devpost.com · Track 4 **Autopilot Agent**.
- **Deadline: Jul 9, 2026, 2:00pm PT** (un post de Alibaba dijo Jul 8 → objetivo interno
  **Jul 8**). Judging hasta **Jul 31** → el demo debe seguir vivo hasta entonces.
- Requisitos duros: repo público + licencia visible · **backend en Alibaba Cloud con
  grabación de prueba** · diagrama de arquitectura · video <3 min · inglés · explicar
  el "significantly updated during the Submission Period" (está redactado en SUBMISSION.md).
- Premios: 5 × ($7k + $3k credits) por track · Blog Award 10 × $1k (draft en
  docs/BLOG_POST.md) · Honorable mentions.

## ✅ ESTADO (2026-07-03) — código COMPLETO y verificado en local
**Todo lo de abajo está construido, con 44 tests verdes y verificado en navegador:**

- **Cerebro qwen3-max** en dos rutas: voz (Deepgram `think` → DashScope intl) y
  **modo texto `/chat`** (loop propio `qwen_brain.run_turn`, mismos tools). Verificado
  en vivo: recall_caller → check_availability (lunes 9am ocupado → alternativas) →
  book_appointment (código VX-XXXX) — todo en español natural, fechas ISO correctas.
- **Qwen TTS** (`qwen3-tts-flash`, `integrations/qwen_tts.py` + `/tts`): respuesta
  hablada del modo texto. Verificado: devuelve WAV real de OSS Singapur.
- **Juez Qwen** (`evaluation.py`): puntúa cada llamada de voz al colgar Y cada chat de
  texto que termina en reserva → evento `call_scored`. Verificado en vivo: 100/100/0.
- **Tablestore con fallback in-memory** (`integrations/tablestore_store.py`): misma API
  con o sin credenciales; `store.backend()` = "tablestore"|"memory". Compatible con las
  formas REALES del SDK (3-tupla get_row / 4-tupla get_range) — el código viejo no lo era.
  Tablas: vx_events, vx_bookings, vx_callers, vx_tenants, **vx_reminders** (nueva).
- **Reminders end-to-end**: al reservar se programan T-24h/T-1h; `POST
  /run-due-reminders` los dispara idempotente (cron o Alibaba FC timer).
- **Fallbacks honestos**: Cal.com y Stripe → "simulated" sin claves (el flujo completo
  funciona con SOLO `DASHSCOPE_API_KEY`); SMS → skipped; `/status` reporta todo.
- **Dashboard `/dashboard` rediseñado** (nivel juez/inversor): KPIs vivos por SSE, panel
  **Qwen quality judge** (metros task/tools + alucinaciones), panel **Cloud stack**
  (estados honestos: connected/local mode/simulated/offline), pipeline animado con
  qwen3-max resaltado, feed de actividad en vivo, bilingüe EN/ES, tenant switcher.
- **Widget con modo Voz|Texto**: texto = chat sin micrófono con chips que precargan el
  input, pill de latencia, toggle "Spoken reply (Qwen TTS)", misma booking card.
- **Landing actualizado**: marquee/stack Qwen3-Max · Model Studio · Tablestore · SMS,
  hero meta "Brain: Qwen3-Max", 8 cards de capacidades, 4 pasos, link al dashboard,
  favicon nuevo (web/app/icon.svg).
- **Docs de submission**: README (EN, con mermaid + screenshots), docs/SUBMISSION.md
  (checklist + guion de video 2:45 + texto Devpost), docs/DEPLOY_ALIBABA.md (ECS +
  Caddy + systemd + prueba), docs/BLOG_POST.md. Screenshots en docs/screenshots/.

## 🌐 GitHub (publicado 2026-07-03)
**https://github.com/Str0k/vexium-voice-qwen** — PÚBLICO, licencia MIT detectada,
description + topics puestos. Historial escaneado (sin claves; nunca se commiteó .env).
`.mcp.json`, `comandostart.md`, `PLAN.md` y `docs/internal/` quedaron FUERA del repo
público (gitignored, siguen en disco).

## ⏭️ LO QUE FALTA (en orden, para ganar)
1. **Deploy en Alibaba Cloud ECS** (requisito duro) — seguir docs/DEPLOY_ALIBABA.md.
   Región Singapur. Crear instancia Tablestore + RAM key + provision script. Configurar
   SMS si da tiempo (si no, queda "simulated" — es válido y honesto).
3. **Grabar la prueba de deployment** (~60s, checklist en DEPLOY_ALIBABA.md §7).
4. **Grabar el video <3 min** (guion listo en SUBMISSION.md; lunes 9am = alternativas
   determinista, cualquier otra hora = reserva limpia).
5. **Rellenar Devpost** (texto draft listo en SUBMISSION.md) + track Autopilot Agent.
6. *(Opcional $1k)* Publicar el blog (draft en BLOG_POST.md) y añadir URL.

## 🔑 Env clave (.env — ver .env.example)
`DASHSCOPE_API_KEY` (única obligatoria para demo texto) · `QWEN_BRAIN_MODEL=qwen3-max` ·
`QWEN_TTS_MODEL=qwen3-tts-flash` · `QWEN_TTS_VOICE=Cherry` · `TABLESTORE_*` (4 vars) ·
`SMS_PROVIDER=alibaba|twilio|none` + `ALIBABA_SMS_*` · `DEEPGRAM_API_KEY` (voz) ·
`ELEVENLABS_*` (voces) · `CALCOM_API_KEY`+`CALCOM_EVENT_TYPE_ID` · `STRIPE_API_KEY`.

## 🗂️ Mapa rápido
Ver tabla en README.md. Piezas nuevas de esta fase: `qwen_brain.py`, `evaluation.py`,
`integrations/qwen_tts.py`, `integrations/tablestore_store.py` (reescrito),
`reminders.py` (+store), `web/app/bridge.js`, `web/app/dashboard/page.js` (rediseño),
modo texto en `web/app/CallWidget.js`.

## 🧪 Verificación local (reproducir)
```powershell
python -m pytest -q                                  # 44 passed
python -m uvicorn server:app --port 8000             # bridge
cd web ; npm run dev                                 # localhost:3000
# texto: pestaña Text → "Quiero agendar una limpieza el lunes a las 10" → reserva
# dashboard: localhost:3000/dashboard → KPIs + juez + feed en vivo
```
