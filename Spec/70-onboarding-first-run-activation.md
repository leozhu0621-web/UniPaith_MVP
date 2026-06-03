# 70 · Onboarding, First-Run & Activation — Build Spec

> The "feel finished and guided" layer: a student cold-start that reaches value in ≤2 actions, a polished first impression (auth + first login), institution setup-wizard finish, and a forms-at-scale system (autosave, multi-step chrome, upload UX, inline-edit) so long workflows never feel fragile. Operationalizes the one-paragraph first-run note in `53` §4 and the institution wizard `30` into a full activation spec. Companion to `64`, `66` (motion), `67` (states/copy), `69` (a11y), `44` (adaptive intake), `19` (Discover), `30` (institution setup).
>
> Status: **draft v2.0** · 2026-06-02 · v2 = first issue.

---

## 1. What exists vs what to build (ground truth)

- **Student Discover** (`pages/student/DiscoverHomePage.tsx`, `discover/ChatPanel.tsx`) is polished — typing indicator, suggested-prompt chips, `aria-live` transcript, a limited-mode banner. But cold-start still asks the student to start talking with little scaffolding; the seeded "try this" path is thin.
- **Readiness scaffolding exists**: the `ReadinessRail` + `ApplyReadyChecklist` (`44`) and profile completion meters (`08`) give the bones of progressive activation — they need to become the guiding spine, not passive widgets.
- **Institution setup**: a first-run wizard exists (`pages/institution/setup`, `30`) orchestrating profile/program/data/team — needs the same finish (progress, save-and-exit, path-to-first-value).
- **Forms**: the core is excellent — `Input`/`Textarea` (reserved error region, ARIA), `LoginPage`/`SignupPage` use React Hook Form + Zod. Gaps: no **autosave** state machine on long forms (profile, program editor); no standard **multi-step wizard** chrome; **file-upload UX** is minimal (transcripts, data upload `24`); no unified **inline-edit** pattern; `err: any` in catch blocks (`LoginPage.tsx:38`, `SignupPage.tsx:43`).
- **First impression**: auth screens carry legacy tokens (`LoginPage.tsx:47,74,76` — fixed in `65`); the very first authenticated screen isn't tuned as a "welcome."

**Principle (from the papers):** the student experience is "a coaching and self-discovery process" that should make a student feel **heard** and lower overwhelm (`64` §2.4). Activation isn't a tutorial wall — it's the counselor gently starting the conversation. Students "expect self-service, transparency, and instant feedback" and the ability to "edit inputs and rerun without restarting" — so onboarding is **progressive, reversible, and low-pressure**, never a mandatory form gauntlet (the Adaptive Intake "progressive completion thresholds," `44`).

---

## 2. The activation model

- **Path-to-value ≤ 2 meaningful actions** on both sides (`53` §4). Student: land → say one thing in Discover → see a first match forming. Institution: land → publish one program (or import data) → see the first applicant signal.
- **Progressive disclosure, not upfront forms.** Ask for the minimum to produce value, then deepen (`44` thresholds: Basic → Personality → Identity). Never block the whole product behind a completion wall.
- **Reversible + transparent.** Every onboarding input is editable later; the system always shows what it understood (the artifact rail, `66` §6) and flags low-confidence items to confirm (`67` §7) rather than guessing silently.
- **Earned momentum.** Completion nudges celebrate progress lightly (the one earned-gold beat is reserved for real milestones, `66` §5) — never nagging, never exclamation-mark hype (`02` §16).

---

## 3. Student first-run

### 3.1 Discover cold-start
The empty Discover state is the single highest-churn moment (`53` §4). Make it a warm, seeded start:
- A short, friendly opener in the counselor voice + **3-4 seeded "try this" chips** that drop the student straight into a real conversation ("I don't know what to major in", "Help me find affordable schools near me", "I want to study abroad"). One tap starts a real, streamed (`66` §6) exchange — no blank prompt box staring back.
- A one-line "here's how this works" (chat → we build your profile → we find matches) — dismissible, shown once.

### 3.2 Progressive completion + nudges
- The `ReadinessRail` (`44`) becomes the visible spine: "You're match-ready" / "2 things to add for stronger matches" — always a concrete next step, never a guilt meter.
- Completion is **layered** (`44`): match-ready gate (enough to recommend) vs apply-ready gate (enough to apply). The UI states which the student has reached and what unlocks next.
- Nudges are contextual and rare: surfaced at the right moment (e.g. after first matches: "Add your test scores to sharpen these"), not a persistent badge swarm.

### 3.3 Coachmarks / tooltips (first-time, dismissible)
- The signature, non-obvious surfaces get a **one-time** coachmark: the dual-score ring ("Fitness = how well it fits you; Confidence = how sure we are"), the rationale popover ("Tap to see why"), the compare tray. Shown once, dismissible, never re-shown (persist in `ui-store`).
- Use the new `Tooltip` primitive (`65` §7 / `69`) for persistent discoverability of icon-only actions; coachmarks for the one-time orientation.

---

## 4. First impression (auth + first login)

- **Auth screens** (`LoginPage`/`SignupPage`): token cleanup (`65`), typed errors (kill `err: any`), the editorial duotone, the wordmark per brand rules (`01` §7 — never recolored/re-spaced), and brand-voice copy. This is the literal first pixels — it must read finished.
- **First authenticated screen** is tuned as a welcome, not a dashboard dump: for a brand-new student that's the seeded Discover (§3.1); for a returning student it's their journey state (matches / applications). The transition from signup → first value is one motion (`66`), not a jarring reload.
- **Role routing** is clean (student → `/s`, institution → `/i/setup` if incomplete, `05` §3) with the 401→`/login?next=` round-trip preserving intent (`54` §6).

---

## 5. Institution first-run

- **Setup wizard** (`30`, `pages/institution/setup`): give it the forms-at-scale chrome (§6) — clear step progress, **save-and-exit + resume**, per-step validation, and a visible "what this unlocks" so an admissions team sees why each step matters.
- **Path-to-first-value:** the wizard's success state is a concrete win — "Your program is live" / "We imported 1,240 prospects" — with a direct link to the surface where the value shows up (the public program page, the pipeline).
- **The "virtual student" tuning** (the paper's institution profiling — fine-tune the target applicant conversationally) is a signature institution moment; give it the same streamed, transparent chat treatment as student Discover (`66` §6), cobalt-not-gold (`65`/`68`).

---

## 6. Forms-at-scale system

The mechanics that make long workflows feel solid:

| Capability | Spec |
|---|---|
| **Autosave** | Long forms (profile `08`, program editor `23`, identity/goals/needs) autosave on change (debounced) with a clear status: "Saving…" → "Saved" → "Couldn't save — retry" (the `67` error pattern). A `useAutosave` hook owns the state machine; never a silent loss. Pairs with optimistic field save (`54` §4). |
| **Multi-step wizard** | A `Wizard`/`Stepper` chrome: step progress, back/next, **save-and-exit + resume**, per-step validation before advance, a summary/review step. Used by institution setup (`30`), data upload (`24`). |
| **Optimistic field save + conflict** | Inline edits commit optimistically (`66` §5 success beat student-side / quiet cobalt institution-side); on a server conflict (stale version) surface a non-destructive "this changed elsewhere — reload?" rather than clobbering. |
| **Async / server validation** | Server-side validation (422, `54` §7) renders at the field via the reserved error region; async checks (e.g. uniqueness) show an inline pending → valid/invalid state, never a blocking spinner. |
| **File upload** | Drag-and-drop + click, multi-file, per-file **progress**, type/size validation with brand-voice errors, retry on failure, and the transcript/credential **OCR path** (`24`/`38`) shown as "Reading your transcript…" → extracted fields to confirm (`67` §7 low-confidence confirm). Today's upload is minimal; this is the biggest forms gap. |
| **Inline edit** | One pattern for edit-in-place (profile fields, program fields): click-to-edit, autosave, ESC to cancel, keyboard + SR accessible (`69`). Replaces ad-hoc per-tab edit logic across the profile tabs. |

---

## 7. Copy (brand voice — onboarding)

Sentence case, no exclamation marks, warm + plain (`02` §16, `67` §8):
| Key | String |
|---|---|
| `discover.coldstart.opener` | "Hi — I'm here to help you figure out your next step. What's on your mind?" |
| `discover.coldstart.hint` | "Not sure where to start? Try one of these." |
| `readiness.matchReady` | "You're ready for matches." |
| `readiness.next` | "Add {thing} to sharpen your matches." |
| `autosave.saving` / `saved` / `error` | "Saving…" / "Saved" / "Couldn't save — try again." |
| `upload.reading` | "Reading your transcript… we'll show you what we found to confirm." |
| `inst.setup.programLive` | "Your program is live. Here's where students will see it." |

---

## 8. Build tasks (checklist)

- [ ] Discover cold-start: seeded "try this" chips → streamed first exchange; one-time "how this works" line.
- [ ] Promote `ReadinessRail` to the activation spine; layered match-ready/apply-ready states; contextual nudges (not a badge swarm).
- [ ] One-time, dismissible coachmarks for dual-ring / rationale / compare (persist in `ui-store`); `Tooltip` for icon actions.
- [ ] Auth polish: tokens (`65`), typed errors, wordmark + brand voice; tune the first authenticated screen as a welcome.
- [ ] Institution setup wizard: stepper chrome + save-and-exit/resume + path-to-first-value; streamed "virtual student" tuning (cobalt).
- [ ] Build `useAutosave` + status indicator; adopt on profile / program-editor / identity-goals-needs.
- [ ] Build `Wizard`/`Stepper`; adopt on `30`/`24`.
- [ ] Build the file-upload component (drag-drop, progress, validation, OCR-confirm path); replace minimal uploads.
- [ ] Build the inline-edit pattern; replace ad-hoc profile-tab edit logic.
- [ ] Centralize onboarding copy (§7) in `lib/copy.ts` (`67` §8).

---

## 9. Acceptance

- [ ] A brand-new student reaches a forming match in ≤ 2 actions from first login; Discover never shows a bare empty prompt.
- [ ] A new institution reaches a concrete first value (program live / data imported) from the wizard, which supports save-and-exit + resume.
- [ ] Coachmarks show once and never again; nudges are contextual, never nagging; no exclamation marks in onboarding copy.
- [ ] Long forms autosave with a visible Saving/Saved/Error status; nothing is silently lost; conflicts are non-destructive.
- [ ] File upload supports drag-drop + progress + validation + retry; the OCR path shows extracted fields to confirm.
- [ ] Inline edit is one accessible pattern across profile + program fields.
- [ ] Auth + first authenticated screen read as finished (tokens, wordmark, voice).

---

## 10. Open questions

- **Coachmark engine.** Build a tiny one-time-coachmark utility vs adopt a tour library. Recommend a tiny in-house utility (4-5 coachmarks total) over a heavyweight tour dep (`54` bundle budget).
- **Autosave vs explicit save.** Profile/identity → autosave (recommended, matches "edit and rerun without restarting"). Program editor → autosave-draft + explicit publish (institution wants intentional publish). Confirm per surface.
- **OCR scope.** Full transcript OCR-to-fields for v1 vs upload-and-attach with manual entry, OCR post-launch. Recommend upload + manual confirm for v1 with the OCR path stubbed behind the same confirm UI, so the UX is built once.
- **Onboarding metrics.** Wire activation events (first message, match-ready reached, first save, program-live) via the analytics bus (`54` §10) to measure path-to-value — confirm the events are defined.
