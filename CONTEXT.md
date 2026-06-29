# Vexium Voice — Contexto del proyecto y handoff

> **¿Retomando en una sesión nueva (o eres otra IA)? Lee este archivo primero.** Resume
> TODO el proyecto y dónde está. Acompáñalo de `CLAUDE.md` (se autocarga en Claude Code),
> `PLAN.md` (plan por fases), `README.md` (cómo correrlo) y `comandostart.md` (comandos
> para levantar el demo).

**Última actualización: 2026-06-03.** Dominio del demo cambiado a **demo.vexiumdata.com**
(`demo.conexionks.com` **retirado del túnel** — responde 404; su registro DNS quedó sin uso).

---

## 📁 Dónde vive
- **Local:** `C:\Users\psiqu\vexium-voice` — repo git. Abre Claude Code desde aquí (carga el MCP de AWS).
- **GitHub:** `Str0k/vexium-voice` (**PRIVADO**). Todo sincronizado.
- **Identidad git del repo (IMPORTANTE):** commits como **Cristian Ramirez <marketyuc@gmail.com>**
  (cuenta GitHub **Str0k**) — NO `cristian@bpeakdigital.com` (Vercel bloqueaba esos deploys). Ya
  está fijo en el config local del repo.

## 🎯 Qué construimos
Recepcionista de voz **bilingüe EN/ES** para **Vexium AI** (vexiumai.com). Contesta llamadas,
cotiza servicios, **verifica disponibilidad** y **agenda citas** capturando cada reserva como
datos estructurados. MVP de fundador solo. Mercado: hispanos en US + LATAM.

## ✅ ESTADO ACTUAL (2026-06-01) — Fases 1, 2 y demo web LISTAS · DEMO PÚBLICO 24/7

**Demo público:** **https://demo.vexiumdata.com** — corre **24/7 en el servidor `ram-linux`**
(Ubuntu siempre encendido, vía Tailscale) como **servicios systemd**. **Ya NO depende de la Lenovo**
(migrado 2026-06-01). Para operarlo/actualizarlo ver `comandostart.md`.

**Stack en runtime (verificado en vivo):**
- **STT:** Deepgram **Flux** `flux-general-multi` v2, `language_hints:[en,es]`, `eot_threshold 0.75`,
  `eager_eot_threshold 0.6`, `keyterms` de vocabulario dental. (Sin `agent.language` — Flux lo rechaza.)
- **LLM:** **Claude Haiku 4.5** en **AWS Bedrock** (`us.anthropic.claude-haiku-4-5-20251001-v1:0`, us-east-2).
- **TTS:** **ElevenLabs Flash v2.5** (BYO-TTS dentro de Deepgram). **Voz por idioma vía `UpdateSpeak`:**
  ES → **Regina** (MX, mujer) `9Godp7dNohUvXk6qp0gS` · EN → **Eryn** (US/americana, mujer) `DXFkLCBUTmvXpp2QwZjA`
  (nombres/idioma verificados en la API de ElevenLabs). **Detección de idioma por turno:** prefiere el campo
  `languages[0]` de Deepgram Flux si viene (en nuestra config suele venir `null`) y si no cae a la heurística
  `detect_language`, que cambia ante **cualquier señal clara** ES/EN — **sin histéresis** (turnos ambiguos como
  "okay"/números/un nombre → `None`, no voltea; el acento es un boost de español, no override). El switch se
  verificó funcionando (Deepgram responde `SpeakUpdated`). Fallback automático a **Deepgram Aura-2**
  si `ELEVENLABS_VOICE_ID` no está. Defaults de voz tuneados vía API (stability 0.5, similarity 0.78,
  style 0, speaker_boost on; ES speed 0.97 / EN 1.0) — esos viven en la cuenta de ElevenLabs, no en el repo.
- **Cerebro/prompts (2 personas):** **"Sofía"** (dental) y **"Valentina"** (restaurante), nivel call-center
  empresarial: IDENTITY LOCK anti-injection, read-back con deletreo, frase de relleno antes de cada función,
  manejo de interrupciones/silencios, registro "usted", + **secciones compartidas de Empatía / Razonamiento /
  honestidad ("no sé", anti-alucinación) / canalización a un agente humano** (`agent_config._human_sections`,
  en ambos verticales). En `agent_config.build_system_prompt(vertical)`.
- **Funciones (client-side) por vertical:** dental → `check_availability` + `book_appointment` (`clinic.py`);
  restaurante → `check_table_availability` (con tamaño de grupo + alternativas) + `book_reservation`
  (`restaurant.py`: menú+precios, especiales, dietético, política, disponibilidad por día). El bridge enruta
  por vertical vía `agent_config.handle_function`.
- **UX del demo (nivel inversor, 2026-06-03):** chips "prueba decir" por vertical · **badge ES/EN por turno** +
  contador de switches **reales** (cuenta sobre la voz del agente, no por palabra suelta) · **pill de latencia**
  (time-to-first-audio) · **tarjeta "Reserva capturada"** (normaliza dental `{booking}` / restaurante
  `{reservation}` + JSON "esto recibe tu CRM") · **recap post-llamada** (reproductor + CTA + copiar resumen) ·
  **disclosure de IA hablada** en el saludo + línea "honesto si preguntan" en el prompt + aviso de consentimiento ·
  switch de idioma **responsivo** (Deepgram `languages[0]` + heurística; cambia ante cualquier señal clara, no
  brinca en "okay"/números) · **saludo conciso** (con disclosure de IA). Flux afinado (eager 0.45 / eot 0.7 /
  timeout 6 s) + keyterms bilingües. Revisado por un workflow adversarial multi-agente (2 HIGH corregidos).
- **Visual / animación (nivel inversor, 2026-06-03):** orbe reactivo a la **frecuencia** de la voz
  (`--level-bass/-mid/-treble`, no solo amplitud) + 4º halo de agudos · flashes del orbe atados a eventos
  REALES (orbe "contesta" al abrir el WS, **duck** al barge-in, flourish al cambio ES↔EN) · aurora de fondo
  sutil · check de reserva que se **dibuja** (SVG) + filas que "imprimen" · estado de error rojo · pausa del
  rAF en background. **Todo CSS/JS puro, SIN dependencias nuevas.** **21st.dev descartado** (Tailwind/shadcn
  no encaja con el CSS a mano; se usa solo como moodboard). Revisado por workflow adversarial (0 críticos).
- **Landing rediseñado (showcase, 2026-06-03):** hero con **spotlight + beams** · banda de **stats con count-up** ·
  **marquee** del stack · how-it-works en **timeline numerada** · capacidades en **bento** con glow que sigue el
  cursor · **CTA** final · **scroll-reveal** por sección (IntersectionObserver en `web/app/fx.js`). Hand-built,
  **sin Tailwind/deps** (21st.dev descartado por lo mismo). a11y: headings correctos, `aria-live`, focus-visible,
  fallback `<noscript>`, reduced-motion. Revisado por workflow adversarial (2 HIGH + medios corregidos).

**Plan de demo actual:** **DOS verticales** seleccionables en el widget — **clínica dental** (recepcionista
"Sofía") y **restaurante de alta gama** ("Vexium Cocina", anfitriona "Valentina"). El frontend manda
`?v=dental|restaurant` al bridge, que carga el prompt + funciones + voz de ese vertical (registro en
`agent_config.VERTICALS`). E-commerce / inmobiliaria quedan "próximamente".

### Modelo LLM propio fine-tuneado (piloto)
Además de usar Claude Haiku en runtime, se entrenó un modelo propio como prueba de concepto:

- **Repo:** [`VexiumZZ/qwen2.5-7b-vexium-voice`](https://huggingface.co/VexiumZZ/qwen2.5-7b-vexium-voice)
- **Base:** `Qwen2.5-7B-Instruct` · **Método:** full fine-tuning
- **Dataset:** 273 conversaciones sintéticas del vertical **dental** (Sofía)
- **Teacher:** `Qwen2.5-32B-Instruct` ejecutado localmente en la instancia Brev
- **Entrenamiento:** 1 H100 80GB (dentro de un nodo 8×H100 en Brev) · Loss final: **2.846**
- **Estado:** Publicado en Hugging Face · **No conectado al demo todavía**

Para usarlo en el demo, se necesitaría desplegarlo en un endpoint OpenAI-compatible (vLLM, Together, Fireworks, DeepInfra) y cambiar `think.provider` del Deepgram Voice Agent. Ver `04-plan-vexium-finetuning.md` en `Documents/nvidiabrev` para serving options.

## 🏗️ Arquitectura — DOS transportes

```
A) DEMO WEB (EN VIVO):
   Navegador (web/, Next.js)  --PCM16 16k/24k WSS-->  server.py (FastAPI bridge)  -->  Deepgram Voice Agent
      mic + reproducción + grabación                    (guarda secretos, switch de voz)     (STT+Claude/Bedrock+TTS)
   Todo en ram-linux (systemd) + Cloudflare tunnel same-origin -> demo.vexiumdata.com (/ws=bridge:8100, resto=frontend:3100)

B) MIC LOCAL (dev): dev_client.py  ->  Deepgram Voice Agent   (test sin web)

C) TELÉFONO (Twilio): FASE 3, AÚN NO construido. Necesita comprar número US.
```
Deepgram Voice Agent maneja turn-taking/barge-in/orquestación. **NO reconstruir STT/TTS propio.**

## ☁️ Deployment actual — ram-linux (24/7, systemd) + Cloudflare tunnel
- **Host:** servidor `ram-linux` (Ubuntu, siempre encendido, accesible por Tailscale, alias SSH `ram-linux`).
  3 servicios systemd (**active + enabled** → auto-reinicio + sobreviven reboot), en `~/vexium-voice`:
  `vexium-bridge` (uvicorn :8100) · `vexium-web` (Next.js prod :3100) · `vexium-tunnel` (cloudflared).
- **Puertos 8100/3100** (no 8000/3000) para no chocar con los otros servicios de ram-linux
  (agente WhatsApp, Mattermost, SearXNG, etc.).
- **Túnel `vexium-demo`** (id `d5f4a796-...`) → DNS CNAME `demo.vexiumdata.com`. Config en
  `~/.cloudflared/vexium-config.yml` (ingress `^/ws$`→:8100, resto→:3100). Coexiste con el túnel
  propio de ram-linux (otro tunnel id `39679323-...`). El ingress sirve **solo** `demo.vexiumdata.com`;
  `demo.conexionks.com` fue **retirado** del túnel 2026-06-02 (responde 404), su registro DNS quedó sin uso. El cert
  (`~/.cloudflared/cert.pem`) se **re-autenticó para la zona `vexiumdata.com`** con cloudflared
  **2026.5.2** (el cert del 22-abr no cubría ese dominio nuevo). ⚠️ **ram-linux tiene IPv6 roto**:
  si cloudflared falla con `Failed to fetch resource`, forzar IPv4 (la causa fue que resolvía
  `login.cloudflareaccess.org` por IPv6).
- **Operar/actualizar:** `comandostart.md` (status/restart/logs por `ssh ram-linux`; update = git pull + build + restart).
- **`.env` con secretos vive en ram-linux** (`~/vexium-voice/.env`, gitignored). Repo en ram-linux sin auth GitHub aún.
- **Migrado de la Lenovo el 2026-06-01.** La Lenovo ya no corre nada de vexium (queda solo para dev local).
- **Vercel = descartado** (solo serviría el frontend; el bridge no corre ahí).
- **Upgrade futuro a AWS Lightsail = Fase 6** (datacenter, mejor para inversores; aprovecha créditos AWS).

## 🔒 Decisiones técnicas (verificadas)
- **Orquestador = Deepgram Voice Agent** (NO ElevenLabs *Agents*, que es otra plataforma).
- **LLM = Claude vía AWS Bedrock** (`think.provider.type: aws_bedrock`; `credentials` anida en `provider`;
  `think.endpoint.url = https://bedrock-runtime.{region}.amazonaws.com/` es OBLIGATORIO). Fallback 1 línea: `anthropic`.
- **TTS = ElevenLabs Flash v2.5** (activo). Deepgram **NO** reenvía `speed` ni `voice_settings` para
  `eleven_labs` (rompe el Settings) — solo `type`/`model_id`/`language_code`. El tono se ajusta como
  **saved defaults de la voz** en ElevenLabs. Aura-2 queda como fallback gratis.
- **Hosting (Fase 6) = AWS** (créditos $10k). Lo más simple ahora: **caja Lightsail + cloudflared** (mismo
  setup que la laptop, sin ALB/cert gracias al túnel) → `demo.vexiumdata.com` 24/7 sin PC. Fargate al escalar.
  App Runner MUERTO; API GW WS+Lambda no sirve (audio continuo).

## 🔌 Datos técnicos Deepgram Voice Agent (verificados)
- **WS:** `wss://agent.deepgram.com/v1/agent/converse`. **Auth:** `subprotocols=["token", DEEPGRAM_API_KEY]`.
- **Audio:** mic dev = linear16 (in 16000 / out 24000, `container:"none"`); Twilio = mulaw 8000.
- **Function calling:** `agent.think.functions` (schema OpenAI). Sin `endpoint` = client-side: recibes
  `FunctionCallRequest {functions:[{id,name,arguments(STRING),client_side}]}` → respondes
  `FunctionCallResponse {type,id,name,content(STRING)}`.
- **UpdateSpeak:** `{type:"UpdateSpeak", speak:{...}}` cambia la voz a media llamada (lo usamos para ES↔EN).
- **Mensajes server:** `Welcome`, `SettingsApplied`, `ConversationText {role,content}`, `UserStartedSpeaking`,
  `FunctionCallRequest`, `Error`, `Warning`, + audio binario.

## 💵 Costos / créditos (ver memorias del proyecto)
- Deepgram Voice Agent: BYO-TTS **$0.065/min** (crédito $200). + tokens Bedrock aparte.
- ElevenLabs **Starter $6/mo** (comercial, ~3 llamadas concurrentes). Key en `.env`. **Grant pendiente** (Scale 12mo).
- **NVIDIA Inception** + **$10k AWS** + **$7.5k Lambda Cloud (GPU)**. **Twilio Searchlight** (hasta $10k — aplicar con el demo).
- El cuello de escala NO es la caja: es la **concurrencia de ElevenLabs/Deepgram** (subir plan antes que migrar AWS).

## ▶️ OPCIONES PARA SEGUIR (elige según prioridad)
1. **Probar inglés en el demo web** (rápido) — validar el switch de voz ES↔EN end-to-end.
2. **Fase 3 — Twilio** (llamada telefónica real). Bloqueante: comprar **número Twilio US** + ngrok/tunnel.
   Escribir el bridge mulaw 8kHz (`server.py` ya es la base; falta el path `/twilio` + TwiML).
3. **Fase 6 — AWS Lightsail** (demo 24/7 sin PC). Mover bridge+frontend+cloudflared a una caja.
4. **Evaluación — Cekura/Coval** (llamadas simuladas, suite de regresión ES/EN). Trae MCP + skill de Claude Code.
5. **Tuning de voz ElevenLabs** (stability/style) a oído, vía API (la key ya tiene permisos `voices`).

## 🗂️ Mapa de archivos
| Archivo | Propósito |
|---|---|
| `CONTEXT.md` | **Este doc** — contexto + estado para retomar |
| `CLAUDE.md` | Contexto técnico (autocargado por Claude Code) + decisiones |
| `PLAN.md` | Plan por fases con checkboxes |
| `README.md` | Cómo correr (mic local + demo web) |
| `comandostart.md` | Comandos para levantar el demo público (3 procesos) |
| `agent_config.py` | Construye el `Settings` de Deepgram + prompt Sofía + `speak_for_language`/`detect_language` |
| `clinic.py` | Vertical dental: servicios/precios, horarios, `check_availability`, `book_appointment` |
| `restaurant.py` | Vertical restaurante: menú/precios, especiales, política, `check_table_availability`, `book_reservation` |
| `server.py` | Bridge FastAPI WebSocket (navegador ↔ Deepgram); switch de voz por idioma |
| `dev_client.py` | Cliente de micrófono local (test sin web) |
| `web/` | Frontend Next.js (landing premium + widget de llamada + grabación). `web/README.md` para deploy |
| `web/app/orb-driver.js` | Orbe audio-reactivo (band-split graves/medios/agudos) del botón de llamada |
| `web/app/fx.js` | FX del landing: `Reveal` (scroll-reveal), `CountUp` (stats), `spotlightMove` (glow al cursor) |
| `.env` (gitignored) | Secretos: Deepgram/AWS/ElevenLabs keys + voice IDs + tuning |
| `.env.example` | Template de `.env` |
| `.mcp.json` | MCP de AWS (aws-api/pricing/knowledge) |

## 🧠 Memorias del proyecto (en `~/.claude/.../memory/`)
NVIDIA Inception + créditos AWS/Lambda · ElevenLabs Startup Grant · Telefonía Twilio vs Telnyx ·
**Identidad git (marketyuc@gmail.com, no bpeakdigital)**.

## 🌐 Fuentes clave
- Deepgram Voice Agent: https://developers.deepgram.com/docs/voice-agent
- TTS models / ElevenLabs BYO: https://developers.deepgram.com/docs/voice-agent-tts-models
- UpdateSpeak: https://developers.deepgram.com/docs/voice-agent-update-speak
- Twilio + Deepgram: https://developers.deepgram.com/docs/twilio-and-deepgram-voice-agent
