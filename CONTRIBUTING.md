# Contributing

Vexium Voice welcomes reproducible bug reports, accessibility improvements, tests
and integrations. Start with a small change that solves a specific problem.
For a new provider or an architectural change, discuss the design in an issue first.

## Development setup

Install Python 3.12 or 3.13, uv 0.11.17 or newer, and Node 24. From a fresh clone:

```sh
uv sync --locked
cd web
npm ci
```

No external provider is needed to run the test suite. Tests allow local loopback
connections for the Windows event loop and block other outbound socket connections.
Use mocks for network services and fictional names, phone numbers and conversations.

## Checks

From the repository root, run the same Python checks as CI:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=65
```

The coverage floor is a regression guard for the existing suite, not a claim of
complete coverage. Voice transport and live provider behavior still need more tests.
For frontend changes, run these commands from `web`:

```sh
npm run lint -- --max-warnings=0
npm run build
npx playwright install chromium
npm run test:e2e
```

The browser suite uses mocked HTTP/SSE responses, blocks external requests and
covers desktop/mobile text fallback, tenant switching and reduced motion.
Check keyboard navigation and language switching manually when changing those flows.

## Dependencies

`pyproject.toml` is the Python source of truth; `uv.lock` fixes the resolution.
`requirements.txt` is a generated runtime-only export for pip-based deployments.
After changing Python dependencies, regenerate it with:

```sh
uv lock
uv export --no-dev --no-hashes --no-emit-project --output-file requirements.txt
```

For JavaScript, commit both `web/package.json` and `web/package-lock.json`.
ESLint stays on 9.39.5 because the current Next ESLint plugins do not support
ESLint 10 consistently; track [Next.js #89764](https://github.com/vercel/next.js/issues/89764)
before upgrading it. CI checks the supported combination.

## Pull requests

Explain the triggering input, previous behavior, new behavior and verification.
For a bug fix, add a regression test that fails on the previous implementation.
Keep unrelated changes separate. AI assistance is welcome, but contributors must
review, understand and validate what they submit. Do not claim testing you did not run.

## Useful next contributions

These are open engineering needs, not promises of upcoming functionality:

- Mock both sides of the voice bridge to cover tool events and cancellation errors.
- Make business-time handling explicit across local and cloud environments.
- Add persistent booking-conflict protection and concurrent reminder claiming.
- Add browser smoke tests for text fallback and tenant switching.

Read [architecture and limitations](docs/ARCHITECTURE.md) before choosing a task.
