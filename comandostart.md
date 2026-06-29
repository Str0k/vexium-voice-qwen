# 🚀 Vexium — operar el demo

**Demo público: https://demo.vexiumdata.com** — corre **24/7 en el servidor `ram-linux`**
(Ubuntu, siempre encendido) como servicios systemd. **No hay que arrancar nada a mano** y
**no depende de la Lenovo** (migrado 2026-06-01).

## Lo que corre en ram-linux (systemd, auto-arranque + auto-reinicio)
| Servicio | Puerto | Qué es |
|---|---|---|
| `vexium-bridge` | 8100 | Bridge FastAPI (navegador ↔ Deepgram) |
| `vexium-web` | 3100 | Frontend Next.js (producción) |
| `vexium-tunnel` | — | cloudflared → `demo.vexiumdata.com` (`/ws`→8100, resto→3100) |

> Puertos 8100/3100 (no 8000/3000) para no chocar con los otros servicios de ram-linux.

## Gestionar / diagnosticar (desde la Lenovo, por SSH)
```bash
# estado
ssh ram-linux "systemctl is-active vexium-bridge vexium-web vexium-tunnel"
# reiniciar
ssh ram-linux "sudo systemctl restart vexium-bridge vexium-web vexium-tunnel"
# logs en vivo
ssh ram-linux "journalctl -u vexium-bridge -f"
# salud
ssh ram-linux "free -h; curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8100/"
```

## Actualizar tras cambiar código
1. En la Lenovo: editas → `git push`.
2. En ram-linux (jala + build + restart):
```bash
ssh ram-linux "cd ~/vexium-voice && git pull && cd web && CI=1 npm run build && sudo systemctl restart vexium-bridge vexium-web"
```
> El repo en ram-linux aún no tiene auth de GitHub para `git pull`. Alternativa hasta
> configurarlo: re-transferir desde la Lenovo con
> `tar czf /tmp/v.tgz --exclude=.venv --exclude=node_modules --exclude=.next --exclude=.env.local . && scp /tmp/v.tgz ram-linux:/tmp/ && ssh ram-linux "cd ~/vexium-voice && tar xzf /tmp/v.tgz"`
> (preserva `node_modules`/`.venv`/`.env` existentes), luego build + restart.
> Si `npm install` se cuelga en ram-linux (WiFi lenta), baja el binario SWC en la Lenovo
> (`npm pack @next/swc-linux-x64-gnu@<ver>`) y pásalo por LAN — ver historial.

## Cloudflare — dominio del demo / túnel
- **Dominio actual:** `demo.vexiumdata.com` (zona `vexiumdata.com`, proxied → túnel `vexium-demo`
  id `d5f4a796-…`). **Retirado:** `demo.conexionks.com` (404; fuera del ingress desde 2026-06-02,
  su registro DNS quedó sin uso).
- **Config del túnel:** `~/.cloudflared/vexium-config.yml` (ingress: `^/ws$`→:8100, resto→:3100).
  Tras editarla → `sudo systemctl restart vexium-tunnel`.

### Cambiar / agregar un dominio nuevo (guía verificada 2026-06-02)
1. El dominio debe estar **en la misma cuenta Cloudflare** (NS `armfazh`/`heidi.ns.cloudflare.com`).
2. **Re-autenticar el cert para esa zona** (el `cert.pem` solo cubre las zonas autorizadas al crearlo;
   un dominio agregado después NO está cubierto → cloudflared crea el registro en la zona equivocada):
   ```bash
   ssh ram-linux "mv ~/.cloudflared/cert.pem ~/.cloudflared/cert.pem.bak; cloudflared tunnel login"
   ```
   Abre el link que imprime → elige la zona → **Authorize**.
   ⚠️ **ram-linux tiene IPv6 roto.** Si el login falla con `Failed to fetch resource`, el cert quedó
   "en espera" en Cloudflare; tráelo **por IPv4** (la URL `https://login.cloudflareaccess.org/…=` del log):
   `ssh ram-linux 'curl -4 -o ~/.cloudflared/cert.pem "<callback-URL>"'`.
   Si cloudflared está viejo (el servicio corre 2026.3.0), baja la última (`cloudflared-linux-amd64`
   de GitHub releases) a `/tmp` y úsala SOLO para el login.
3. **Crear el DNS apuntando al túnel** (forzando el config correcto, si no usa otro túnel por defecto):
   ```bash
   ssh ram-linux "cloudflared tunnel --config ~/.cloudflared/vexium-config.yml route dns vexium-demo demo.NUEVO.com"
   ```
4. Agregar el hostname al **ingress** (`vexium-config.yml`) → `sudo systemctl restart vexium-tunnel`.
5. **Verificar:** `curl -s -o /dev/null -w '%{http_code}' https://demo.NUEVO.com/` (200) **y** un
   WebSocket real a `/ws` (handshake 101 — `curl` da 404 falso a través de Cloudflare; usa un cliente WS).

## Desarrollo local en la Lenovo (sin tocar producción)
```powershell
# bridge local (puerto 8000)
.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
# frontend local (puerto 3000) -> abre http://localhost:3000
cd web ; npm run dev
# test rápido por micrófono (sin web)
.venv\Scripts\python.exe dev_client.py
```
El frontend en `localhost` se conecta al bridge local `:8000` automáticamente (same-origin).

## Notas
- **Stack:** Deepgram Voice Agent (Flux bilingüe) + Claude Haiku (Bedrock) + ElevenLabs
  Flash v2.5 (Regina MX / voz US, switch por idioma). Reservas + disponibilidad por function calling.
- **Secretos** en `~/vexium-voice/.env` en ram-linux (gitignored, no se sube). Si lo cambias,
  `sudo systemctl restart vexium-bridge`.
- **Tono de voz** (stability/style/speed) = saved defaults de cada voz en el dashboard de ElevenLabs.
- **Red de ram-linux:** WiFi 2.4 GHz (`The Estate`), ~52 Mbps↓ / ~47 Mbps↑, latencia ~4 ms, 0% pérdida —
  **sano** para el demo (una llamada usa ~0.4 Mbps). ⚠️ **IPv6 roto** (sin ruta a internet por v6): si una
  descarga o login de cloudflared falla, forzar IPv4 (`curl -4`). Subir el WiFi a 5 GHz aceleraría los deploys.
- **Certs cloudflared** en `~/.cloudflared/`: `cert.pem` (actual, scoped a `vexiumdata.com`),
  `cert.pem.bak-multizone` (anterior, puede administrar `bpeakdata.us`/`conexionks.com`), `cert.pem.preauth`.
  Backups del ingress: `vexium-config.yml.bak-both` (con conexionks) / `.bak-conexionks` (original).
- **Always-on AWS** = Fase 6 (Lightsail). Hoy ram-linux ya da el 24/7 gratis.
