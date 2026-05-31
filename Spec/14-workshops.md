# 14 · Workshops — Feedback-Only

> Resume / Essay / Interview / Test preparation. **Schema-mechanically excludes any generation.** Two modes: general (not tied to a specific program) and program-specific. Surfaces in `/s/manage?tab=workshops`.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s/manage?tab=workshops`. **Schema invariant test:** `tests/test_workshop_no_generation_contract.py` per CLAUDE.md.

---

## 1. THE invariant

**Plan 2's LLM swap-in cannot break this without failing CI.**

The output schema mechanically excludes any field that could carry:
- A generated essay or model answer.
- A rewritten draft.
- A paragraph-level rewrite suggestion.
- A "here's how I would write it" suggestion exceeding 12 words.

The student does the writing. The agent gives structured feedback signals — clarity, structure, evidence, alignment to the program's focus — and surfaces missing elements. Nothing more.

This is the **brand commitment**: bias-avoidance is a practice; we don't author the student's voice for them.

---

## 2. Workshops tab structure

Three-button picker at the top:
```
[ Essay ] [ Interview ] [ Test prep ]
```

Each opens a panel. Mode selector inside each panel: **General** vs **Program-specific**. Program-specific surfaces "what materials matter most for this application type" and "which parts of existing materials are aligned vs weak for that target."

---

## 3. Essay workshop

### 3.1 Inputs
- Essay text (paste or autosave-typed in workspace).
- Optional prompt (e.g., "Tell us about a time you led a team").
- Optional target program (defaults to general).

### 3.2 Output schema (FEEDBACK-ONLY)

```ts
type EssayFeedback = {
  rubric_scores: Record<string, number>;        // 0–5 per rubric criterion
  structural_issues: Array<{
    severity: 'low' | 'medium' | 'high';
    location: string;                          // "paragraph 2" or "opening sentence"
    issue: string;                             // ≤ 160 chars
  }>;
  missing_elements: Array<{
    importance: 'low' | 'medium' | 'high';
    suggestion: string;                        // ≤ 160 chars, never a sentence the student should write
  }>;
};
```

**Forbidden fields** (schema rejects these on validation):
- `rewritten_paragraph`, `revised_essay`, `model_answer`, `suggested_paragraph`, `paragraph_replacement`, anything > 12 words that could replace student copy.

Agent: `WorkshopCoach (Essay variant)` (`45-ai-agents-claude.md` §7).

### 3.3 UX

```
ESSAY WORKSHOP

Mode: [General ▾] [Program-specific: U of Foo CS MS ▾]

Prompt: [Tell us about a time you led a team]

[ Paste or type your essay below ___________________________________ ]

[Get feedback]

─── FEEDBACK ────────────────────────────────
Rubric scores
  Clarity        ●●●●○
  Structure      ●●●○○
  Evidence       ●●●●●
  Specificity    ●●○○○

Structural issues
  ⚠ HIGH       Opening sentence is generic. Replace with a specific moment.
  ⚠ MEDIUM     Paragraph 2 lacks a clear topic sentence.

Missing elements
  ★ HIGH       No concrete metric of impact in the team-leadership story.
  ★ MEDIUM     Conclusion doesn't tie back to the program you're targeting.
```

No "Generate draft" button. No "Rewrite for me" button. Ever.

---

## 4. Interview workshop

### 4.1 Two sub-modes

**Practice questions mode** (generation IS allowed — these are coach questions, not student answers):
- Pick type: general / behavioral / technical.
- Pick focus area: leadership / failure / collaboration / domain-specific.
- Optional target program.
- Returns: 5–10 practice questions with "why this question" annotation.

**Score-a-response mode** (feedback-only):
- Paste a recorded response (text or transcript).
- Returns: rubric scores + structural issues + missing elements + suggested-questions-to-practice.

### 4.2 Output schema (score mode)

Same shape as Essay (`rubric_scores + structural_issues + missing_elements`), plus:
- `suggested_questions_to_practice: list[string]` (these are coach questions, not student answers; safe to generate).

Agent: `WorkshopCoach (Interview variant)` (`45` §8).

---

## 5. Test prep workshop

### 5.1 Inputs
- Test type (GRE / GMAT / TOEFL / IELTS / MCAT / LSAT / SAT / ACT).
- Current score / target score.

### 5.2 Output
```ts
type TestGuidance = {
  current_band: string;
  target_band: string;
  gap_analysis: Array<{ topic: string; recommendation: string }>;
  prep_recommendations: Array<{ action: string; time_commitment: string; priority: 'low' | 'med' | 'high' }>;
};
```

No model answers to test questions. Guidance only.

Agent: `WorkshopCoach (Test variant)` (`45` §9).

---

## 6. Program-specific mode (across all three)

When the student selects a target program:
- Workshop fetches the program's `requirements_checklist` + recent reviewer rubric (if institution provides).
- Feedback is tuned: surfaces what materials matter most for THIS application type, what existing materials are aligned vs weak FOR THIS TARGET.
- Outputs a per-program **readiness summary** in student language.

---

## 7. Data shape

```ts
type WorkshopFeedbackRun = {
  id: string;
  student_id: string;
  workshop_type: 'essay' | 'interview' | 'test';
  mode: 'general' | 'program_specific';
  target_program_id: string | null;
  input_text: string | null;            // essay text or interview response
  output: EssayFeedback | InterviewFeedback | TestGuidance;
  model_used: 'claude-sonnet-4-6' | 'claude-haiku-4-5-20251001' | 'rule_based';
  created_at: ISO8601;
};
```

Stored in `workshop_feedback_runs` table. Per CLAUDE.md "feedback-only" schema invariant.

Endpoints:
- `POST /me/workshops/essay/feedback`.
- `POST /me/workshops/interview/practice` (mode 1).
- `POST /me/workshops/interview/feedback` (mode 2).
- `POST /me/workshops/test/guidance`.
- `GET /me/workshops/runs` — history.
- `GET /me/workshops/runs/:id` — single run.

All gated on `ai_workshops_v2_enabled` feature flag. Per `04-llm-claude-migration.md` migration plan.

---

## 8. States

- **Loading:** spinner on the Get-feedback button.
- **Empty (first visit):** "Drop in an essay draft to get structured feedback."
- **Error (agent failure):** "We couldn't analyze this draft in depth. Showing rule-based result." + zeros + a one-issue retry note. Never 5xx (rule-based fallback).
- **Validation block (somehow output contains forbidden field):** server-side validation rejects → log + rule-based fallback. Test asserts.

---

## 9. AI integration

All three coaches per `45-ai-agents-claude.md`. Sonnet tier (workhorse). Cache: system block at 1h; persona at 5min; tail = the artifact uncached.

---

## 10. Brand compliance

- "Get feedback" CTA in cobalt (secondary). Never gold (we're not the artist).
- Rubric dot fills in `--primary` gold (this is the one accent moment).
- Severity badges per `02-design-system.md` §11 alert colors.
- No marketing imagery; no "AI magic" framing in copy.

---

## 11. Gaps (from `47`)

- G-A5 (defer): legacy `EssayWorkshopPage.tsx` and `ResumeWorkshopPage.tsx` still lazy-loaded by Profile's "Essays & Resume" tab. Phase E deletion target.
- Resume workshop is currently part of the legacy pages; spec aligns it with Essay's feedback-only contract; the Phase E follow-through migrates it into the same `WorkshopFeedbackRun` table.

---

## 12. Tests

- **Critical:** `tests/test_workshop_no_generation_contract.py` — schema rejects any forbidden field; agent prompts never produce them in fixture runs.
- Per coach: input → expected output shape.
- Fallback on agent failure: zeros + retry note; no 5xx.
- Program-specific mode pulls program requirements; general mode skips.

---

## 13. Copy

- "Drop in an essay draft to get structured feedback."
- "Get feedback" (CTA — never "Get review" or "Generate").
- "Rubric scores" / "Structural issues" / "Missing elements".
- "We couldn't analyze this draft in depth. Showing rule-based result." (fallback).
- "These are practice questions, not answers." (sub-line in Interview practice-questions mode).
- "Workshops give you feedback. We never write your essay for you." (one-time disclosure at first visit).

---

## 14. Open questions

- **Resume workshop migration.** Currently lives in the legacy `ResumeWorkshopPage.tsx`. Spec aligns it under §3 essay-like contract: same rubric/structural/missing-elements output, with rubric criteria specific to resume (impact metrics, action verbs, conciseness, alignment).
- **Audio interview input.** Future: accept audio file → transcribe → score. MVP: transcribed text only.
- **Workshop diff history.** Show how feedback changes across drafts? Defer; useful but not MVP-critical.
- **Coach vocabulary per program.** Some programs have idiosyncratic rubric language (e.g., "fit" vs "match"). Per-tenant prompt overlay defer.
