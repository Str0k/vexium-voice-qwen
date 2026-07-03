# Devpost Submission Plan — Global AI Hackathon Series with Qwen Cloud

**Competition:** https://qwencloud-hackathon.devpost.com/ · **Track 4: Autopilot Agent**
**Deadline:** July 9, 2026, 2:00 PM PT (official rules) — an Alibaba Cloud post said
July 8, so **treat July 8 as the internal deadline**.
**Judging period:** July 10–31 → the live demo must stay up (free, no login) until **July 31**.

## Submission checklist (from the official rules)

- [ ] **Public repo** with all source + run instructions. **License must be visible in
      the GitHub "About" sidebar** → repo Settings: make public; the MIT `LICENSE` file
      is already at the root (GitHub auto-detects it — verify the About box shows "MIT").
- [ ] **No secrets in the repo** (`.env` is gitignored; double-check history before going public).
- [ ] **Proof of Alibaba Cloud deployment**: short recording per
      [DEPLOY_ALIBABA.md §7](DEPLOY_ALIBABA.md) **plus** a link to a code file using
      Alibaba Cloud APIs (use `integrations/tablestore_store.py` or `qwen_brain.py`).
- [ ] **Architecture diagram** — the mermaid diagram in the README (export a PNG for the
      Devpost gallery too; judges may not click through).
- [ ] **Demo video < 3 minutes**, public on YouTube (script below).
- [ ] **Text description** (draft below) — includes the required
      **"significantly updated during the Submission Period"** explanation.
- [ ] **Track selected:** Autopilot Agent.
- [ ] **Testing access:** public demo URL in the submission (works free, no login).
- [ ] **Everything in English.**
- [ ] *(Optional, +$1,000 award, 10 winners)* **Blog/social post** about the build
      journey (draft in [BLOG_POST.md](BLOG_POST.md)) — add its URL to the submission.

## How we score on their rubric

- **Technical Depth & Engineering (30%)** — qwen3-max function calling drives both a
  realtime voice pipeline (as Deepgram's BYO `think` provider — an unusual, deep
  integration) *and* a text agent; qwen3-tts-flash; Qwen-as-judge auto-QA; full
  fine-tuned Qwen2.5-7B pilot on HuggingFace.
- **Innovation & AI Creativity / architecture quality (30%)** — modular verticals
  (prompt+tools+handlers registry), every integration behind a graceful fallback
  (in-memory Tablestore clone, simulated Cal.com/Stripe, honest `/status`), 44 tests,
  event-sourced metrics, SSE dashboard.
- **Problem Value & Impact (25%)** — missed calls are lost revenue for US Hispanic
  clinics/restaurants; bilingual voice is the differentiator; live ROI dashboard makes
  the value literal (deposits, after-hours saves). Multi-tenant by design → productizable.
- **Presentation & Documentation (15%)** — README with diagram, this plan, deploy guide,
  screenshots, sub-3-minute front-loaded video.

## Video script (2:45, front-loaded — judges may stop at 3:00)

| Time | Shot | Script (spoken) |
|---|---|---|
| 0:00–0:15 | Landing page, hit *Start call* | "This is Vexium — a bilingual AI receptionist for the 65-million US Hispanic market. It's answering live. Watch it book me, in two languages, end to end." |
| 0:15–1:15 | **Live voice call** (screen + audio). Ask in English, switch to Spanish mid-call; book "Monday 9am" → busy → accept alternative; confirm. Booking card pops with JSON. | Let the call speak. Point at: language badge flipping + voice changing, the availability check firing, the booking card with structured JSON "this is what your CRM receives." |
| 1:15–1:40 | Dashboard, split-screen with the call. | "Every event lands in Alibaba Cloud Tablestore and streams here live: the call, the booking, the deposit. And every finished call is scored by Qwen itself as a QA judge — task completion, tool accuracy, hallucinations." |
| 1:40–2:05 | Text mode: tap a suggestion chip, get reply + Qwen TTS audio. | "No mic? The same qwen3-max brain runs the text mode, and qwen3-tts-flash speaks the answers — this path is 100% Qwen on Model Studio." |
| 2:05–2:30 | Architecture diagram (README). | "One FastAPI bridge. Deepgram handles ears and mouth; **qwen3-max is the brain** — it decides when to check the calendar, charge a Stripe deposit, send Alibaba Cloud SMS, recall a returning patient, or hand off to a human. Everything persists in Tablestore, multi-tenant." |
| 2:30–2:45 | Cloud stack panel + tests passing + HF model page. | "It degrades gracefully — clone it with one API key and everything runs. 44 tests. And we've already fine-tuned a Qwen2.5-7B on 273 synthetic calls as the path to a self-hosted brain. Vexium: never miss a call again." |

**Recording tips:** demo-critical determinism — ask for **Monday 9/10/11am** to always
trigger the alternatives flow; any other weekday hour books cleanly. Record the voice
call with system audio; keep one uncut take of the call if possible.

## Devpost text description (draft — paste & adapt)

> **Inspiration.** Clinics and restaurants serving the US Hispanic market miss calls
> every day — after hours, or because the caller prefers Spanish. Each missed call is a
> lost booking. We built the receptionist that never misses one.
>
> **What it does.** Vexium answers calls in Spanish and English (switching voice
> mid-call), quotes services, checks real availability, books appointments on the
> calendar, texts SMS confirmations, collects Stripe deposits for high-value services,
> remembers returning callers across sessions, schedules T-24h/T-1h reminders, and
> escalates to a human with a summary when it should. Every event streams to a live ROI
> dashboard — and **Qwen grades every call** (task completion, tool accuracy,
> hallucinations) as an automatic QA judge.
>
> **How we built it.** qwen3-max (Alibaba Cloud Model Studio, OpenAI-compatible
> endpoint) is the function-calling brain in two pipelines: (1) plugged directly into
> Deepgram Voice Agent as its BYO `think` provider for sub-second voice, and (2) a text
> agent with the same tools, voiced by qwen3-tts-flash. Business state — events,
> bookings, caller memory, tenant configs, reminders — lives in Alibaba Cloud Tablestore;
> notifications go out via Alibaba Cloud SMS. FastAPI bridge, Next.js frontend, SSE
> dashboard. 44 automated tests.
>
> **Significantly updated during the Submission Period.** The project started as a
> Claude-on-Bedrock voice demo. Since May 26, 2026 we rebuilt it around Qwen and Alibaba
> Cloud: migrated the brain to qwen3-max (voice `think` + a new text mode), added
> qwen3-tts-flash spoken replies, built the Qwen-as-judge evaluation layer, moved all
> persistence to Tablestore (events, cross-session caller memory, multi-tenant configs,
> reminders), integrated Alibaba Cloud SMS, Cal.com booking and Stripe deposits, added
> graceful zero-credential fallbacks for every integration, and shipped the live ROI
> dashboard. We also fine-tuned Qwen2.5-7B-Instruct on 273 synthetic dental calls
> ([VexiumZZ/qwen2.5-7b-vexium-voice](https://huggingface.co/VexiumZZ/qwen2.5-7b-vexium-voice)).
>
> **Challenges.** Realtime voice + LLM function calling is unforgiving about latency —
> we kept Deepgram's turn-taking and let qwen3-max do all decision-making;
> per-turn bilingual voice swapping without flapping took careful language detection.
>
> **What's next.** Twilio numbers for real phone lines, the fine-tuned 7B behind vLLM as
> a self-hosted brain, and onboarding the first pilot clinics.

## Judge-experience rehearsal (do this before submitting)

1. Fresh clone on a clean machine → `pip install` → set ONLY `DASHSCOPE_API_KEY` →
   text-mode booking works → dashboard shows the booking + judge score.
2. Public URL: voice call works on desktop Chrome + iPhone Safari.
3. Video link is public/unlisted-public; captions on (judges may watch muted).
4. README renders correctly on GitHub (mermaid, screenshots, license badge in About).
