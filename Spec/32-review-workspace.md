# 32 · Review Workspace

> The per-applicant deep-dive for institution reviewers. AI packet summary (Opus), per-reviewer rubric scoring, side-by-side reviewer view, cohort comparison.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: `/i/pipeline/:studentId`, `/i/cohort-compare`.

---

## 1. Purpose

Where institution staff actually review and score applicants. The current `StudentDetailPage` is comprehensive; this spec captures the contract.

---

## 2. Per-applicant review packet

```
APPLICANT · Sienna Chen · CS MS Fall 2027 Round 1

[ Overview · Scores · AI Summary · Integrity · Timeline · Documents · Essays ]

AI PACKET SUMMARY                            (Opus)
─────
Sienna comes from NYU's senior class with a 3.8 GPA…

SIGNAL STRENGTHS
  ★ Strong research signal: two co-authored papers in ML systems.
  ★ Leadership: led a 12-person hackathon team to 1st in regional.
  ★ Match to program: 91/100 fit; 84/100 confidence.

SIGNAL WEAKNESSES
  ✖ No formal industry internship (intern at academic lab only).
  ✖ Test scores not submitted (program is test-optional).

RUBRIC NOTES (AI-prefilled, editable)
  Academic readiness: 4/5 — "Strong GPA with rigorous course load…"
  Leadership: 4/5 — "Hackathon win demonstrates clear leadership."
  Research potential: 5/5 — "Co-authored publications at undergrad."
  Fit to program focus: 5/5 — "ML + systems aligns to HCI track."
  Diversity contribution: 3/5 — "First-gen student; underrepresented in CS."

[Score this applicant]  [Generate AI draft message]  [Mark for committee]
```

---

## 3. Scoring rubric

Per program, defined in `/i/settings?tab=rubrics`. Per criterion: name + weight. At scoring time:
- Per-reviewer score 0–5.
- Per-reviewer note.
- AI-prefill if `ai_review_v2_enabled`.

Score view: list per applicant; side-by-side per applicant across reviewers.

---

## 4. Side-by-side reviewer view

When 2+ reviewers have scored the same applicant:
- Per criterion: each reviewer's score in a column.
- Variance highlighted (Δ ≥ 1.5).
- Reviewer notes side-by-side.
- Synthesized recommendation (AI assist — Sonnet).

---

## 5. Cohort comparison

`/i/cohort-compare` — sort cohort by total score; expand per-criterion view; decision-colored chips.

Used by admissions committees to make rolling decisions.

---

## 6. AI assistive layer (per `37-ai-extensibility.md`)

| Surface | Agent | Notes |
|---|---|---|
| AI packet summary | `DraftSummarizerForReview` (`45` §14, Opus) | One Opus call per applicant; cached per `(profile_v, program_v, intake_id)`. |
| Rubric pre-fill | `AIPrefillForRubric` (Sonnet) | Pre-fills notes; reviewer edits before saving. |
| AI draft message | `InboxReplyDrafter`-equivalent for institution (Sonnet) | Drafts missing-items / interview-invite / clarification / decision-notice. |
| AI assistant chat | Sonnet | Q&A about the applicant ("What's their strongest signal?"). |

**Rule:** humans keep final action. AI generates drafts. Status changes, communications, decisions all require explicit human action.

---

## 7. Per-applicant integrity tab

Per `31-admissions-intake.md` §6 integrity signals. Per applicant:
- Document authenticity confidence.
- Duplicate identity likelihood.
- Essay authenticity flags.
- Login risk events.

Reviewer can `acknowledge / clarify / reject_application` per signal. Each action audit-logged.

---

## 7A. Reviewer fairness & rigor tools (MVP-extend, `49` §3)

Tools that make review fairer and more consistent — all MVP-class, all wired to the fairness harness (`46` §6).

### 7A.1 Blind review mode
Per-institution (or per-round) toggle that **redacts identity-revealing fields** from the packet during scoring: name, photo, gender, age, address/geography precision, optionally school name. Reviewers score on substance; identity reveals only after the score commits (or never, per policy).
- Redaction map is explicit + audit-logged (`36`); a post-score "reveal" action is logged with reason.
- A stronger profile of the asymmetric-rationale principle (`06` §3).

### 7A.2 Reader calibration  *(promoted from open question)*
- **Calibration sets** — a shared set all reviewers score; system reports **inter-rater reliability** (agreement/variance per rubric dimension).
- **Drift detection** — flags a reviewer systematically harsher/more lenient than the panel.
- **Norming view** — each reviewer's score distribution vs panel, with a recalibrate nudge.
- Coaching signals only — never auto-adjusts committed scores. (Supersedes the §14 open-question note.)

### 7A.3 Test-optional analysis
- Per applicant: `test_policy_compatibility` + `submit_vs_withhold_recommendation` (`42` §4.6) as context, never a penalty.
- Cohort view: outcomes for submitters vs non-submitters (admit/yield/success) so the committee can see whether weighting scores is justified — and detect adverse impact.
- Guardrail: non-submission must never count against an applicant; the UI states this.

### 7A.4 Holistic-review context flags
Context that informs holistic review **without becoming a selection shortcut**:
- Flags: first-generation, low-income, **legacy/development**, **athletic-recruit**, school-profile/regional context.
- **Strict fairness gating (`46` §6):** legacy/development + athletic are high-sensitivity — (a) shown only to policy-permitted roles, (b) every use audit-logged, (c) fed into the disparate-impact monitor, (d) never a positive weight in the matching/ranking model.
- Equity-positive side: school-profile + regional-opportunity context cards help read an applicant in context.

---

## 8. Data shape

```ts
type ApplicantReviewPacket = {
  application_id: string;
  student: StudentProfileSummary;
  program: ProgramCard;
  ai_packet_summary: { text: string; generated_at: ISO8601; model_id: string; cached: boolean };
  rubric_scores: Array<{
    criterion: string;
    weight: number;
    per_reviewer: Array<{ reviewer_id: string; score: number; note: string }>;
    synthesized_recommendation: string | null;
  }>;
  integrity_signals: IntegritySignal[];
  documents: DocumentRef[];
  essays: Essay[];
  decision: Decision | null;
  offer: Offer | null;
};
```

Endpoints:
- `GET /i/applications/:id/review-packet`.
- `POST /i/applications/:id/score` — body: rubric scores.
- `POST /i/applications/:id/decision` — institution decision.
- `POST /i/applications/:id/regenerate-summary` — re-run Opus.
- `POST /i/applications/:id/ai-draft` — body: `{type: 'missing_items' | 'interview_invite' | ...}` → returns draft.
- `POST /i/applications/:id/assistant-chat` — body: `{question: string}` → answer (Sonnet).

---

## 9. States

- **AI summary loading:** "Generating summary…" placeholder.
- **AI failure:** rule-based template summary (concatenation of top rubric strengths/weaknesses).
- **No scores yet:** "No one has scored this applicant yet."
- **Locked applicant:** if decision released, scoring becomes read-only.

---

## 10. Brand compliance

- AI badges per `02` §15 on every AI-generated card.
- Score sliders (0-5) in cobalt with gold fill at "Excellent" 5.
- Reject in destructive variant; tertiary "Defer" / "Waitlist" / "Mark for committee".

---

## 11. Gaps (from `47`)

- G-AI5 (major): DraftSummarizerForReview on Opus needs explicit wiring per `45` §14 (currently uses Sonnet).
- Side-by-side variance highlighting + synthesis is partial.

---

## 12. Tests

- Score persists per reviewer; aggregated correctly.
- AI summary caches by (profile_v, program_v, intake_id).
- Decision release flips status + creates Offer (via `34-decisions-offers-institution.md`).
- AI draft generation respects template style.

---

## 13. Copy

- "Generate AI summary" / "Regenerate".
- "Score this applicant" → modal.
- "Mark for committee" (defer).
- "Showing rule-based summary" (fallback banner).

---

## 14. Open questions

- **Per-institution rubric language.** As noted in `45` §27 — per-tenant prompt overlay defer to Phase 2.
- **Reviewer calibration.** Inter-rater reliability dashboard at institution level — variance > 1.5 across many applicants flags calibration need.
- **Anonymous review mode.** Reviewer doesn't see student name + identity until after scoring. Defer.
