# Blog post draft — "I rebuilt my voice receptionist's brain with Qwen in two weeks"

> For the hackathon's **Blog Post Award** ($500 cash + $500 credits × 10 winners).
> Publish on dev.to / Medium / X (long-form) in English, add screenshots from
> `docs/screenshots/`, and paste the final URL into the Devpost submission.

---

**Title options**
- I swapped my voice agent's brain for qwen3-max — here's what surprised me
- Building a bilingual AI receptionist on Qwen Cloud: from missed calls to booked deposits
- qwen3-max as the `think` step of a realtime voice agent (and as its own QA judge)

---

My startup, Vexium, builds voice receptionists for businesses that serve the US Hispanic
market. The problem is painfully simple: a clinic that doesn't answer in Spanish at 8pm
loses a $300 patient. The fix is not simple: realtime bilingual voice AI that actually
*does* things — checks a calendar, charges a deposit, remembers a returning patient.

For the Global AI Hackathon with Qwen Cloud, I rebuilt the entire brain of the product
on Qwen. Three things made it work better than I expected.

## 1. qwen3-max as the `think` step of a realtime voice pipeline

Deepgram's Voice Agent handles the ears and mouth (bilingual STT, turn-taking,
barge-in) and lets you bring your own LLM as an OpenAI-compatible endpoint. Model
Studio's `dashscope-intl` endpoint is exactly that — so qwen3-max became the brain of a
sub-second voice loop with zero glue code:

```python
"think": {
  "provider": {"type": "open_ai", "model": "qwen3-max", "temperature": 0.7},
  "endpoint": {"url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
               "headers": {"authorization": f"Bearer {DASHSCOPE_API_KEY}"}},
  "prompt": SOFIA_PROMPT, "functions": TOOLS,
}
```

What surprised me: qwen3-max follows a *strict operating procedure* remarkably well. My
receptionist prompt is essentially a call-center SOP — confirm the name, read back the
phone, never promise a slot without checking, never book without a read-back. Qwen
respects the tool-gating rules (`check_availability` before `book_appointment`,
`recall_caller` as soon as it has a phone number) turn after turn, in both languages.

## 2. The same brain, twice — and Qwen TTS for free

Because the brain is just an OpenAI-compatible function-calling loop, the no-microphone
text demo reuses it verbatim (~40 lines: validate args → run tool → feed result back).
Then qwen3-tts-flash speaks the replies, so even the fallback path is voice-first and
100% Qwen. One brain, two transports, zero drift between what the voice agent and the
text agent can do.

## 3. Qwen judging Qwen

The sleeper feature: after every finished conversation, qwen3-max gets the transcript
plus the tool-call log and returns `{task_completion, tool_accuracy, hallucination}`.
That lands in Alibaba Cloud Tablestore next to the bookings and deposits, and streams to
a live dashboard. A voice agent that books appointments is a demo; a voice agent that
*audits itself* and shows you the QA scores next to the revenue is a product.

## The boring parts that won me over

- **Tablestore** is a great fit for event-sourced agent state: one `vx_events` table
  gives me metrics, an activity feed, and an audit log; `vx_callers` gives cross-session
  memory ("Bienvenido de nuevo, Cristian"). Schemaless rows meant zero migrations
  during a hackathon sprint.
- **Graceful degradation** was the best time investment: every integration
  (Tablestore, Cal.com, Stripe, SMS) has an honest fallback, and a `/status` endpoint
  reports what's real. Anyone can clone the repo with one API key and see the whole
  product work — including the judges.
- I also full fine-tuned **Qwen2.5-7B-Instruct** on 273 synthetic dental calls
  (Qwen2.5-32B as teacher) as the path to a self-hosted brain:
  [VexiumZZ/qwen2.5-7b-vexium-voice](https://huggingface.co/VexiumZZ/qwen2.5-7b-vexium-voice).

## Numbers

- 2 verticals (dental clinic, restaurant) from one config registry
- 8 tools the agent can call · 44 automated tests
- ~4–6s text-mode round trip including tool calls; sub-second voice replies
- 1 API key needed to run everything locally

The repo, architecture diagram, and a 3-minute demo are here: **[repo link]** ·
**[demo link]** · **[video link]**.

*Built solo with qwen3-max, qwen3-tts-flash, Tablestore, Alibaba Cloud SMS, Deepgram,
Next.js, and FastAPI.*
