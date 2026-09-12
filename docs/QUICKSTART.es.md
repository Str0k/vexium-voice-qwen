# Inicio rápido

Vexium Voice es una aplicación de referencia para un recepcionista bilingüe con
FastAPI, Qwen y Next.js. Incluye ejemplos de clínica dental y restaurante.
El demo del hackathon de julio de 2026 es histórico.

## Instalación

Instala Python 3.12 o 3.13, uv 0.11.17 o posterior y Node 24. Desde una terminal:

```sh
git clone https://github.com/Str0k/vexium-voice-qwen.git
cd vexium-voice-qwen
uv sync --locked
uv run uvicorn server:app --host 127.0.0.1 --port 8000
```

Abre otra terminal en la raíz del repositorio para iniciar la interfaz:

```sh
cd web
npm ci
npm run dev
```

Visita `http://localhost:3000`, el panel en `/dashboard` y la documentación de la
API en `http://127.0.0.1:8000/docs`. Sin proveedores configurados puedes explorar
la interfaz y ejecutar las pruebas. La generación de texto necesita Qwen y la
voz necesita también Deepgram; su uso puede tener costo.

## Comprobaciones

Desde la raíz del repositorio, estas pruebas usan servicios simulados y solo
permiten conexiones de red locales:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov --cov-fail-under=65
```

Desde `web`, ejecuta `npm run lint` y `npm run build`.
Consulta [CONTRIBUTING.md](../CONTRIBUTING.md) para proponer cambios y
[ARCHITECTURE.md](ARCHITECTURE.md) para conocer los límites de almacenamiento,
autenticación, recordatorios y zonas horarias del demo.
