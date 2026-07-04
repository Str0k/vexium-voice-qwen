# Deploying Vexium Voice on Alibaba Cloud (hackathon-proof setup)

> **Why this document matters:** the Qwen Cloud Hackathon requires (1) the backend
> running on Alibaba Cloud, (2) a short screen recording proving it, and (3) a link to a
> code file that uses Alibaba Cloud services/APIs. This guide gets all three.

## What already counts as "Alibaba Cloud services and APIs" in this repo

Link any of these files as the code-proof in the Devpost form:

- [`qwen_brain.py`](../qwen_brain.py) — qwen3-max via Model Studio (`dashscope-intl.aliyuncs.com`)
- [`integrations/tablestore_store.py`](../integrations/tablestore_store.py) — Alibaba Cloud Tablestore (OTSClient)
- [`integrations/sms.py`](../integrations/sms.py) — Alibaba Cloud SMS (`alibabacloud_dysmsapi`)
- [`integrations/qwen_tts.py`](../integrations/qwen_tts.py) — qwen3-tts-flash on Model Studio

## Target topology (one small ECS instance is enough)

```
Internet ──▶ ECS (Ubuntu 22/24, Singapore ap-southeast-1)
             ├─ caddy (or nginx)  :80/443
             │    ├─ /ws, /chat, /tts, /summary, /events, /feed, /status,
             │    │  /run-due-reminders   → uvicorn :8000  (vexium-bridge)
             │    └─ everything else      → next start :3000 (vexium-web)
             ├─ vexium-bridge.service  (uvicorn server:app)
             └─ vexium-web.service     (next start)
             ▼
             Tablestore instance (same region) · Model Studio (DashScope intl) · Alibaba SMS
```

## Step by step

### 1. ECS instance
- Console → ECS → Create. Region **Singapore (ap-southeast-1)** (closest to
  `dashscope-intl` and Tablestore intl).
- `ecs.e-c1m2.large` (2 vCPU / 4 GB) or similar burstable is plenty. Ubuntu 22.04+.
- Security group: open 22 (your IP), 80, 443.

### 2. System setup

```bash
sudo apt update && sudo apt install -y python3.11-venv python3-pip git caddy nodejs npm
git clone https://github.com/Str0k/vexium-voice-qwen.git && cd vexium-voice-qwen
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env        # DASHSCOPE_API_KEY + TABLESTORE_* + SMS keys
cd web && npm install && npm run build && cd ..
```

### 3. Tablestore
- Console → Tablestore → Create instance (e.g. `vexium`), same region.
- Put endpoint + instance + an AccessKey (RAM user with Tablestore R/W) in `.env`.
- `python scripts/provision_tablestore.py` (creates the 5 `vx_*` tables).

### 4. systemd services

`/etc/systemd/system/vexium-bridge.service`
```ini
[Unit]
Description=Vexium Voice bridge (FastAPI + Qwen)
After=network.target
[Service]
WorkingDirectory=/home/ubuntu/vexium-voice-qwen
ExecStart=/home/ubuntu/vexium-voice-qwen/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000
Restart=always
[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/vexium-web.service`
```ini
[Unit]
Description=Vexium Voice web (Next.js)
After=network.target
[Service]
WorkingDirectory=/home/ubuntu/vexium-voice-qwen/web
ExecStart=/usr/bin/npm run start
Restart=always
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now vexium-bridge vexium-web
```

### 5. Caddy reverse proxy (automatic HTTPS with a domain)

`/etc/caddy/Caddyfile` — route the bridge's API + WS paths to :8000, the rest to :3000:

```caddy
demo.yourdomain.com {
    @bridge path /ws /chat /tts /summary /events /feed /status /run-due-reminders
    handle @bridge {
        reverse_proxy 127.0.0.1:8000
    }
    handle {
        reverse_proxy 127.0.0.1:3000
    }
}
```

`sudo systemctl reload caddy`. (No domain? Use the ECS public IP with `:80` as the site
address — HTTP is fine for judging access.)

> The frontend auto-targets same-origin, so no `NEXT_PUBLIC_*` changes are needed when
> the bridge and web share one host.

### 6. Reminders timer (optional but nice)
- Simplest: `crontab -e` → `*/10 * * * * curl -s -X POST http://127.0.0.1:8000/run-due-reminders?tenant=dental`
- Cloud-native alternative: an **Alibaba Function Compute** timer that POSTs the same URL.

### 7. Record the deployment proof (separate from the demo video)
One ~60-second screen recording showing, in one take:
1. Alibaba Cloud console: the running ECS instance (region + status).
2. SSH: `systemctl status vexium-bridge vexium-web` (active), `curl localhost:8000/status`.
3. Tablestore console: the `vx_*` tables with rows.
4. The public URL loading, and `/dashboard` with the Cloud stack panel showing
   **Tablestore: connected**.

### 8. Keep it alive through judging
Judging runs through **July 31, 2026** — leave the instance up and the demo public
(free access, no login) until then.
