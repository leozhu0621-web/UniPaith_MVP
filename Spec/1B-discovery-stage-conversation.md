# 1B · Discovery Stage — 3-Track LLM-Led Conversation

> Stage 1 — Discovery. The chat-first onboarding-and-beyond surface at `/s` (the student app's home). Three tracks (Profile / Goals / Needs), three layers for the Profile track (Basic / Personality / Identity). Chat panel + live artifact rail.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s` (default) + `?track=profile|goals|needs&layer=basic|personality|identity`.

---

## 1. Purpose

Replace the "fill out 200 fields" onboarding pattern with conversation. The LLM (per `42-ai-agents-claude.md` §2 `DiscoveryOrchestrator`) drives the next prompt; the `DiscoveryExtractor` writes signals to the Prompt Library; the `DiscoveryJudge` decides when to switch layer or hand off to recommendation.

---

## 2. Three tracks

### 2.1 Profile track
Builds the durable profile via 3 layers of depth:
- **Basic** — demographics + academic factors (age, education level, location preferences, income level, first-gen, gender, test scores, grades).
- **Personality** — interests, passions, friends, career goals, location preferences, connection preferences.
- **Identity** — beliefs, values, worldview, self-awareness.

Discovery Orchestrator advances layers when the previous layer's completeness ≥ 80%.

### 2.2 Goals track
SMART goal stack across 3 categories: Academic, Social, Personal.

### 2.3 Needs track
Maslow-keyed map: Physiological → Safety → Social → Self-esteem → Self-actualization.

---

## 3. Visual layout

```
DISCOVER
Let's figure out what you're looking for

┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ Profile             │  │ Goals               │  │ Needs               │← TrackSelector
│ ━━━━━━━━━━○○  60%  │  │ ━━━━○○○○○○  30%   │  │ ━━━━━━○○○○  50%    │
│ Layer: Basic ●●○   │  │                     │  │                     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘

┌───────────────────────────────────────┐ ┌────────────────────────────────────┐
│  CHAT                                  │  ARTIFACT RAIL                       │
│                                        │  (switches by track × layer)         │
│  Counselor                             │                                       │
│  Tell me about a course you actually  │  BASIC SIGNALS                        │
│  enjoyed this year.                    │  ────                                  │
│                                        │  GPA: 3.7                              │
│  You                                   │  Location pref: East Coast             │
│  Algorithms — surprised myself.        │  Edu stage: senior                     │
│  Loved the puzzle of it.               │                                       │
│                                        │  IDENTITY SIGNALS (empty)              │
│  Counselor                             │  Add to Identity tab on Profile        │
│  Nice. What kind of puzzles outside   │                                       │
│  CS classes do you find yourself     │  GOAL STACK                            │
│  drawn to?                             │  - Academic: get top 30 MS CS         │
│                                        │  - Personal: stay debt-light          │
│  [____________________]  [Send]        │                                       │
│  Suggested prompts:                    │  NEEDS MAP                            │
│  · I love board games                  │  - Must: affordable                    │
│  · I like to fix things                │  - Strong: research                    │
│  · Word puzzles I guess                │  - Nice: city campus                   │
└───────────────────────────────────────┘ └────────────────────────────────────┘

[Generate strategy] (enabled when all 3 tracks ≥ 50%)
```

---

## 4. Per-track flow

### 4.1 Profile track flow

Layer state:
- **Basic** — agent prompts cover the basic fields; auto-advance at ≥ 80% completion.
- **Personality** — once basic done; can be triggered manually too.
- **Identity** — deepest layer; only after personality reaches a threshold.

The orchestrator NEVER asks a sensitive identity question in the basic layer.

### 4.2 Goals track flow

Agent walks the student through each SMART criterion per category. Outputs `student_goals` rows with provenance `from_discovery` + confidence.

### 4.3 Needs track flow

Agent walks Maslow levels bottom-up: physiological (housing/food) → safety → social → self-esteem → self-actualization. Each level: one or two questions. Outputs `student_needs` rows.

---

## 5. Chat semantics

- One question per turn. Never multi-question.
- Suggested replies as chips below the input — student can tap to send.
- "I don't know yet" is always a valid reply; orchestrator skips that field for now.
- "Skip this" jumps to next question.
- "Switch track" lets the student jump tracks anytime.

---

## 6. Artifact rail

Right-side panel that swaps per track × layer:

| Track / Layer | Widget |
|---|---|
| Profile / Basic | BasicSignalsWidget — list of fields filled with `from_discovery` source. |
| Profile / Personality | (PERSONALITY widget — currently placeholder per audit) |
| Profile / Identity | IdentitySignalsWidget — values / worldview / self-awareness with confidence dots. |
| Goals | GoalStackWidget — compact list of active goals. |
| Needs | NeedsMapWidget — Maslow pyramid summary. |

Each widget links to the relevant Profile tab.

---

## 7. Handoff to Stage 2

Two paths:
1. **Auto** — `DiscoveryJudge` decides handoff when match-ready threshold met.
2. **Manual** — "Generate strategy" CTA enabled when all 3 tracks ≥ 50%. Calls `POST /me/strategy/generate`.

On handoff: `StrategyAgent` runs; student is navigated to `/s/explore?showStrategy=open`.

---

## 8. Data shape

```ts
type DiscoverySession = {
  id: string;
  student_id: string;
  track: 'profile' | 'goals' | 'needs';
  layer: 'basic' | 'personality' | 'identity' | null;     // only profile uses layer
  status: 'active' | 'paused' | 'completed';
  started_at: ISO8601;
  last_message_at: ISO8601;
};

type DiscoveryMessage = {
  id: string;
  session_id: string;
  sender: 'student' | 'orchestrator' | 'system';
  body: string;
  extracted_signals: Record<string, { value: any; confidence: number }>;
  model_used: string;   // "claude-sonnet-4-6" | "rule_based" | ...
  created_at: ISO8601;
};
```

Endpoints:
- `GET /me/discovery/sessions` — list per track.
- `POST /me/discovery/sessions` — create.
- `POST /me/discovery/sessions/:id/messages` — orchestrator + extractor + validator + judge per turn.
- `GET /me/discovery/completion-map` — per-track completion %.

All gated on `ai_discovery_v2_enabled` flag.

---

## 9. States

- **No active session for current track:** ChatPanel auto-creates one on first message.
- **Loading message:** typing-indicator + disabled input.
- **Agent failure:** rule-based prompt served; banner "Limited mode active — your replies are still saved."
- **Track switch mid-session:** confirmation if there's a half-typed message.

---

## 10. AI integration

| Agent | Trigger | Purpose |
|---|---|---|
| `DiscoveryOrchestrator` | Each turn | Next prompt |
| `DiscoveryExtractor` | Each turn | Extract signals |
| `DiscoveryValidator` | Each turn | Sanity-check extraction |
| `DiscoveryJudge` | Every 3–5 turns | Decide continue/switch/handoff |
| `StrategyAgent` | Generate-strategy CTA | First / regenerated strategy |

Streaming: Phase 2 nice-to-have (current non-streaming acceptable).

---

## 11. Brand compliance

- TrackSelector cards in `--surface` with the active card outlined in `--accent`.
- Chat: counselor messages in `--surface` left-aligned; student messages in `--muted` right-aligned.
- "Suggested prompts" chips in cobalt outline.
- Generate-strategy CTA in `--primary` gold ONLY when enabled — the one earned accent moment.

---

## 12. Gaps (from `90`)

- G-S6: legacy `OnboardingPage` is a single-thread heuristic stub; spec recommends shimming it to seed a Discovery profile/basic session.
- PERSONALITY layer widget is placeholder (falls back to Identity).
- Phase B layer pin is currently `'basic'` — manual switcher not exposed in UI.

---

## 13. Tests

- Session creation on first message.
- Extracted signals persist + appear in artifact rail.
- Layer auto-advance at threshold.
- Judge handoff when all tracks ≥ threshold.
- Strategy generation on CTA.
- Failure: rule-based prompt served, no 5xx.

---

## 14. Copy

- "Let's figure out what you're looking for" (H1).
- "Tell me about a course you actually enjoyed this year." (orchestrator opener for Basic layer).
- "Suggested prompts" (chip-row label).
- "Generate strategy" (CTA).
- "Limited mode active — your replies are still saved." (fallback banner).
- "I don't know yet" / "Skip this" (always-available replies).

---

## 15. Open questions

- **Manual layer switcher.** When should we expose it? Recommend after basic completes, a small "Open Personality" link beside the layer chip.
- **PERSONALITY widget content.** What's the most useful summary? Recommend: interests / passions / career-direction hypothesis with confidence dots.
- **Cross-track context.** Should the orchestrator know what's been said in OTHER tracks? Yes — persona block includes summary of all three tracks' completion + recent extractions; keeps the chat coherent.
- **Voice input.** Mobile-first students may prefer voice. Defer.
