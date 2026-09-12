# Vexium Voice - Qwen reference app

Follow [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md) and the current
[architecture notes](docs/ARCHITECTURE.md). The hackathon documents are historical.

## Technical conventions

- Text and voice share the business functions in `clinic.py` and `restaurant.py`.
- Blocking provider work must run outside the ASGI event loop.
- Tablestore reads return SDK tuples: use `get_attrs`, `put_attrs` and `_scan`.
- Deepgram function calls must carry the server-owned tenant and call ID.
- Never describe configured services as having passed a live health check.
- The in-memory backend is process-local; reminders have no concurrent claiming.
- Git author for this repository: Cristian Ramirez <marketyuc@gmail.com>.

## Commands

Run the locked local checks before proposing changes:

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov --cov-fail-under=65
```

In `web`, run `npm ci`, `npm run lint`, `npm run build` and `npm run test:e2e`.
See CONTRIBUTING.md for browser installation and dependency updates.
