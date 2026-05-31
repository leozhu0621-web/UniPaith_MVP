# 16 · Calendar

> Admissions-related events + deadlines on a unified timeline. Application-linked navigation. Student-created reminders + work blocks. Lives at `/s/manage?tab=calendar`.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s/manage?tab=calendar`.

---

## 1. Purpose

Aggregate every time-sensitive thing across the active application set in one place. Each admissions item links back to its application workspace. Add personal work blocks and reminders alongside.

---

## 2. Visual layout

```
CALENDAR
Your admissions timeline

View: [ Month  Week  Agenda ]
Filter: [ All applications ▾ ]  [ All item types ▾ ]

─── DECEMBER 2026 ───
Mon Dec 8
  10:00  Interview · University of Foo · 30 min · Zoom
                  ← linked to Foo application

Wed Dec 10
  Essay draft session (you set this) · 2h
                  ← linked to Bar application

Fri Dec 12
  ⚠ Submission deadline · Bar CS MS · 11:59 PM EST

... month grid below

[+ Add reminder] [+ Add work block]
```

---

## 3. Views

- **Month** — calendar grid with admissions items dotted; click date → day detail.
- **Week** — hour grid; admissions items + work blocks placed.
- **Agenda** — list of upcoming items grouped by date.

---

## 4. Item types

| Type | Source | Visual |
|---|---|---|
| Live interview | Institution-scheduled | Blue dot, time, "Live" |
| Recorded/async interview window | Institution-scheduled | Orange dot, window |
| Campus visit | Institution-event RSVP | Blue dot |
| Info session | Institution-event RSVP | Blue dot |
| Portfolio review / audition | Institution-scheduled | Orange dot |
| Submission deadline | Application | Red dot, time |
| Document deadline | Application | Red dot |
| Recommendation deadline | Application | Red dot, recommender chip |
| Interview submission deadline | Application (recorded interview) | Orange dot |
| Deposit deadline | Offer | Red dot |
| Reminder (student-created) | User | Gray dot |
| Work block (student-created) | User | Gray block |

---

## 5. Per-item actions

- **Open application** — deep-link to `/s/applications/:appId` (or `?tab=interviews|documents|essays|...` as relevant).
- **Mark complete** — for deadlines and reminders.
- **Reschedule** — for items that allow rescheduling (interview status = `requested` or `confirmed`).
- **Decline** — for interview invites.
- **Attach confirmation** — upload screenshot of off-platform completion.

---

## 6. Data shape

```ts
type CalendarItem = {
  id: string;
  type: 'interview_live' | 'interview_recorded_window' | 'campus_visit' | 'info_session' |
        'portfolio_review' | 'audition' | 'submission_deadline' | 'document_deadline' |
        'recommendation_deadline' | 'interview_submission_deadline' | 'deposit_deadline' |
        'reminder' | 'work_block';
  title: string;
  start_at: ISO8601;
  end_at: ISO8601 | null;
  location: string | null;
  meeting_link: string | null;
  application_id: string | null;
  status: 'scheduled' | 'completed' | 'cancelled' | 'overdue';
  notes: string | null;
  reminder_settings: { lead_time_minutes: number; channels: ('email' | 'push' | 'in_app')[] } | null;
};
```

Endpoints:
- `GET /me/calendar?from=...&to=...` — items in range.
- `POST /me/calendar/reminders` — create.
- `POST /me/calendar/work-blocks` — create.
- `PATCH /me/calendar/:id` — update (status, notes, etc.).

---

## 7. States

- **Empty:** "Your calendar is clear. Set a work block or RSVP to an event to get started."
- **Filtered to nothing:** "No items match. Clear filters?"
- **Overdue items:** highlight in red across all views.

---

## 8. AI integration

None directly. Future: schedule-suggestion agent that proposes work-block placement based on deadlines + the student's planned weekly time budget. Defer.

---

## 9. Brand compliance

- Color usage: blue dots = cobalt; orange dots = `--warning`; red dots = `--error`; gray = `--text-mut`. No gold on calendar items (gold is for the brand mark, not for time).
- Today indicator: subtle `--accent` underline on the day cell.
- Overdue badge: `error-soft` background, `--error` text.

---

## 10. Gaps (from `47`)

- Calendar item polling vs push: currently polling on view. Push notifications via WebSocket would improve.
- iCal/ICS export per application set so students can sync to Google Calendar / Outlook. Not yet.

---

## 11. Tests

- Items appear in all 3 views.
- Application-linked navigation works.
- Reminder creation persists.
- Overdue computation correct based on `start_at` < now AND status != completed/cancelled.

---

## 12. Copy

- "Your admissions timeline" (H1).
- "+ Add reminder" / "+ Add work block".
- "Your calendar is clear. Set a work block or RSVP to an event to get started."
- "Overdue" badge.

---

## 13. Open questions

- **Sync with external calendars (Google/Outlook).** ICS export MVP-ok; OAuth-based two-way sync defer to Phase 2.
- **Time zone handling.** Store UTC; display in student's `current_address.time_zone`. Confirm round-trip clean.
- **Work-block recurrence.** Support recurring reminders (daily essay session). MVP: one-time; recurrence defer.
