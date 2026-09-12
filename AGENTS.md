# Repository guidance

Read README.md, CONTRIBUTING.md and docs/ARCHITECTURE.md before changing behavior.
This is the public Qwen reference app; changes here must not affect other Vexium deployments.

- Use `uv sync --locked` and `npm ci` in `web` for reproducible dependencies.
- Python checks: `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run pytest --cov --cov-fail-under=65`.
- Frontend checks: `npm run lint -- --max-warnings=0` and `npm run build` in `web`.
- Mock external providers in tests. Never use real caller data in fixtures.
- Add a failing regression test before fixing externally observable behavior.
- Keep business functions independent from HTTP/WebSocket transports.
- Keep blocking provider calls off the ASGI event loop.
- `pyproject.toml` is authoritative. Regenerate the runtime requirements export
  after dependency changes; see CONTRIBUTING.md.
- Do not label simulations as live integrations or claim production readiness.
- Keep CONTRIBUTING and architecture notes aligned with implementation changes.
