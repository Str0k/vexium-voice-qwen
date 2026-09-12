# Architecture and operating boundaries

The project is a reference application for a bilingual receptionist. The API and
dashboard demonstrate booking workflows; they are not a production tenancy boundary.

## Request paths

Text requests pass through Pydantic request validation, a server-owned system prompt
and the bounded Qwen tool loop. Blocking provider calls run outside the ASGI event loop.
Only `user` and `assistant` messages are accepted from the browser. Each text request
receives a new call ID shared by its tool events and metrics; it is not a persistent
conversation session or an idempotency key.

Voice requests connect the browser to Deepgram. Two tasks relay traffic. Completion
of either task cancels and awaits the other before the connection is released.
Provider-side tool calls are dispatched to the same business functions as text calls.

## Contracts

`/chat` accepts `dental` or `restaurant`, 1–24 messages, and nonblank string content
of at most 2,000 characters per message. Unknown fields and invalid types return 422.
The frontend submits its latest 24 messages. Missing model configuration returns
503; provider failure returns 502 without copying the provider exception into the response.

`/tts` accepts a nonblank string of at most 2,000 characters and optional language
`es`, `en` or `auto`. It speaks at most the first 600 characters. The generated
OpenAPI schema at `/docs` is the detailed HTTP request reference.

## Storage and side effects

Tablestore is used when configured. Otherwise a process-local in-memory adapter
implements the same storage API. In-memory data disappears on restart and is not
shared across workers. Integration status indicates configuration, not a successful
live health check. Tests mock cloud APIs and do not certify vendor compatibility.

Calendar and payment fallbacks are simulations. With real providers configured,
booking tools can create external bookings, checkout links and messages. The demo
availability catalog is not an authoritative provider calendar.

## Known production gaps

The HTTP and WebSocket routes currently have no authentication, per-user quotas or
authorization for tenant access. CORS is permissive. Dashboard data may contain
caller information. Keep the reference app local with fictional data; a public
deployment needs an access-control layer, rate limits and a data-retention policy.

Reminder processing avoids repeated delivery after a persisted successful send in
a sequential run. It does not atomically claim reminders across concurrent workers,
and a crash between delivery and persistence can duplicate delivery. Skipped demo
SMS currently counts as sent. No exactly-once guarantee is provided.

Naive appointment times currently use the host timezone. Configure a single business
timezone consistently until timezone-aware scheduling is implemented. Background
quality scoring uses a daemon thread and may be interrupted during shutdown.

## Verification

CI installs locked dependencies, checks Python formatting and lint, runs mocked
tests on Linux and Windows, and builds the frontend on Node 24. Real calls, payments,
SMS and cloud deployments require a separate controlled integration test.
