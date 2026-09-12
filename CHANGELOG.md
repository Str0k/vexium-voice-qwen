# Changelog

Changes that affect people running or extending the application are recorded here.

## 0.2.0 - 2026-09-11

This release establishes a reproducible development baseline for the reference app.

### Fixed

- Malformed chat and speech input now returns HTTP 422 instead of raising server
  errors or coercing non-string values into model input.
- Model errors no longer echo the provider exception into the chat response.
- The voice bridge cancels and awaits its peer task when either connection ends.
- The browser limits conversation history to the documented request bounds.
- Microphone capability and reduced-motion preferences are synchronized with React;
  switching dashboard tenants clears the previous tenant's visible state.

### Added

- Python dependency manifest and lockfile, with a generated runtime pip export.
- Linux/Windows Python CI, frontend lint/build checks and Dependabot configuration.
- Regression tests for request validation and upstream voice disconnection.
- Browser smoke tests for desktop/mobile text fallback, tenant changes and reduced motion.
- Contribution guide, issue/PR templates and a Spanish quickstart.
- Architecture notes describing simulation behavior and production gaps.

### Changed

- Frontend upgraded to Next.js 16.3.5 and React 19.3.0 with an npm lockfile.
- Python formatting and import ordering are enforced by Ruff.
- README no longer promises a hosted hackathon demo or unverified performance.

## 0.1.0 - historical baseline

The July 2026 code demonstrates Qwen text/voice orchestration, calendar and payment
adapters, reminder scheduling, caller memory and a dashboard. No tagged release
was published for that baseline.
