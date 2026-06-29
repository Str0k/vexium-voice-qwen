# Vexium Voice — Web demo

Elegant landing page with a **browser voice demo**: the visitor clicks the mic, talks to
the bilingual AI receptionist (the same agent as `dev_client.py`), and can download a
recording of the whole call. Built with Next.js (App Router), deploys to Vercel.

## Architecture

```
Browser (this app, on Vercel)  ──WSS audio──►  server.py (the bridge)  ──►  Deepgram Voice Agent
   mic → PCM16 16k                                (holds the secrets)         (STT + Claude/Bedrock + TTS)
   speaker ← PCM16 24k
   records mic + agent → .webm
```

The **frontend** goes on Vercel. The **bridge** (`server.py`, in the repo root) canNOT run on
Vercel (serverless can't hold a continuous audio WebSocket) — run it locally with ngrok now,
deploy it to AWS later (Phase 6).

## Run it locally

**1. Start the bridge** (from the repo root, with your `.env` filled in):

```bash
# Windows PowerShell, from C:\Users\psiqu\vexium-voice
.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
```

**2. Start the frontend** (from `web/`):

```bash
cd web
npm install
cp .env.local.example .env.local   # default points at ws://localhost:8000/ws
npm run dev                        # http://localhost:3000
```

Open http://localhost:3000 and click the mic. (Browsers allow mic on `localhost` and on HTTPS.)

## Make the local bridge reachable from a deployed frontend (ngrok)

If you deploy the frontend to Vercel but keep the bridge on your laptop:

```bash
ngrok http 8000
# take the https URL, e.g. https://abc123.ngrok-free.app
# in Vercel project env vars set:
#   NEXT_PUBLIC_BRIDGE_URL = wss://abc123.ngrok-free.app/ws
```

> The frontend must use `wss://` (secure) when served over HTTPS — ngrok gives you that.

## Deploy the frontend to Vercel

1. Push this repo to GitHub.
2. In Vercel: **New Project → import the repo → set Root Directory to `web`**.
3. Add env var **`NEXT_PUBLIC_BRIDGE_URL`** = your bridge URL (`wss://…/ws`).
4. Deploy.

The bridge still needs to be running (ngrok or AWS) for the call button to work.
