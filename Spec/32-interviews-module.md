# 32 · Interviews Module (Institution)

> Institution-side interview management: propose, schedule, score, complete. Live / recorded / async / portfolio review / technical assessment.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/i/interviews` (also under `/i/admissions?tab=interviews`).

---

## 1. Purpose

End-to-end interview management. Per applicant, per program, with status flow + rubric scoring + AI draft of communications.

---

## 2. Interview types

| Type | Notes |
|---|---|
| `live` | Real-time meeting (Zoom/Teams/in-person). |
| `recorded_async` | Student records responses to prompts within a window. |
| `portfolio_review` | Live or async portfolio walkthrough. |
| `technical_assessment` | Coding / case study / written test. |
| `third_party_platform` | Kira Talent, Watermark, etc.; UniPaith tracks but doesn't host. |

---

## 3. Flow

1. **Propose** — institution selects applicant(s) + type + time slots (or window for async).
2. **Invite** — student receives Inbox message + Calendar item.
3. **Confirm** — student accepts (or declines / reschedules).
4. **Conduct** — meeting / async submission.
5. **Score** — interviewer scores via rubric.
6. **Complete** — status flips; result feeds the per-applicant review packet (`31`).

---

## 4. UX

```
INTERVIEWS

[ Upcoming · Completed · All ]
[Filter: Program ▾] [Filter: Type ▾]

KPI: Confirmed 24 · Scheduling 12 · Completed 38

TABLE
  Applicant     Program       Type       Status       Scheduled       Actions
  Sienna Chen   CS MS         live       confirmed    Dec 8, 10:00    [Score]
  …

[+ Propose interview]
```

---

## 5. Propose modal

- Pick applicant(s).
- Pick type.
- Pick program.
- For live: 3+ proposed time slots.
- For async: window with deadline.
- Duration (live only).
- Location or meeting link.
- Notes for the student (template-driven).

---

## 6. Score modal

- Rubric per program (interviewing rubric distinct from application rubric).
- Per-criterion score + note.
- Overall recommendation (recommend / neutral / not recommend).
- Optional AI prefill (Sonnet) — "Based on the recording transcript, here's a starting score…"

---

## 7. Data shape

```ts
type Interview = {
  id: string;
  application_id: string;
  applicant: { student_id: string; name: string };
  program: ProgramCard;
  type: InterviewType;
  status: 'proposed' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  proposed_slots: ISO8601[];        // for live
  scheduled_at: ISO8601 | null;
  duration_minutes: number | null;
  location: string | null;
  meeting_link: string | null;
  async_window_end: ISO8601 | null;
  scoring_rubric: RubricRef;
  scores: Array<{ interviewer_id: string; score: number; notes: string; created_at: ISO8601 }>;
  recommendation: 'recommend' | 'neutral' | 'not_recommend' | null;
  recording_url: string | null;
};
```

Endpoints:
- `GET /i/interviews?filter=...`.
- `POST /i/interviews/propose` — body: `{applicant_ids, type, time_slots, etc.}`.
- `POST /i/interviews/:id/score`.
- `POST /i/interviews/:id/complete`.
- `POST /i/interviews/:id/cancel`.

---

## 8. States

- **No interviews:** "No interviews scheduled."
- **Awaiting student confirmation:** badge "Awaiting student" (yellow).
- **Reschedule requested:** notification to staff.
- **Async window expired without submission:** "No submission received" status; review can advance without interview.

---

## 9. AI integration

| Agent | Trigger | Purpose |
|---|---|---|
| AI prefill for score | Score modal open | Pre-fills rubric scores from transcript or notes |
| Inbox draft for invite | Send invite | Drafts the invite message |

---

## 10. Brand compliance

- Status badges per `02` §11.
- Per-interview action buttons cobalt.

---

## 11. Gaps (from `90`)

- Live meeting embed (Zoom/Teams) not native; just a link.

---

## 12. Tests

- Propose → student Inbox + Calendar items created.
- Confirm flow updates status.
- Score → feeds review packet.
- Async window expiration handled gracefully.

---

## 13. Copy

- "Propose interview" / "Reschedule" / "Cancel".
- "Awaiting student" / "Confirmed" / "Completed" / "No submission received".

---

## 14. Open questions

- **Recording transcription.** Auto-transcribe live interview recordings? Privacy concerns; opt-in flow required.
- **Async submission grading at scale.** When hundreds of async videos arrive, surface a "top 10 by AI ranking" suggestion to prioritize reviewer time.
