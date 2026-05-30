# 30 · Admissions Intake

> The institution's intake dashboard for the active admissions cycle. Queues, batch actions, integrity signals, executive cockpit metrics. Lives at `/i/dashboard` (executive view) + `/i/admissions?tab=pipeline` (operational queue).
>
> Status: **draft v1.0** · 2026-05-29 · Routes: `/i/dashboard`, `/i/admissions?tab=pipeline`, `/i/inquiries`.

---

## 1. Purpose

Where admissions staff start their day. Counts by stage, queue backlog, integrity alerts, new inquiries, intelligence digest, yield-risk alerts, notifications.

Per audit, the current `DashboardPage` is well-built; this spec captures the contract.

---

## 2. Executive dashboard (`/i/dashboard`)

```
DASHBOARD
University of Foo · Fall 2027 cycle

KPI ROW
  Total apps: 3,420  · Conversion: 18.4%  · Avg match: 72  · Yield (proj): 38%

PRIORITY QUEUE                                              See all →
  ★ 12 applications need reviewer assignment
  ★ 8 applications with integrity flags
  ★ 5 interview confirmations pending

INTELLIGENCE DIGEST
  Match-quality is up 7% this week vs last.
  Source: Email Campaign #14 generated 32 new applications (highest).

YIELD-RISK ALERTS
  ▾ 24 admitted students haven't responded; deadline in 6 days

INTEGRITY SIGNALS
  ⚠ 3 essay authenticity flags pending review
  ⚠ 1 duplicate-account suspicion

NEW INQUIRIES
  Last 24h: 14 (3 unanswered ≥ 4h)

NOTIFICATIONS
  ...
```

---

## 3. Pipeline page (`/i/admissions?tab=pipeline`)

Drag-and-drop Kanban OR table view:

```
PIPELINE

Filter: [Program ▾]  [Search ✏]  [View: Board · List · Needs Review · Priority]

BOARD
[ Applied (240) ] [ Under Review (180) ] [ Interview (40) ] [ Decision (24) ]

  Applicant cards (drag between columns to change status)

BATCH ACTIONS (when ≥ 1 selected)
  [Assign reviewers] [Request missing items] [Invite interviews]
  [Update status] [Release decisions]
```

---

## 4. Per-stage actions

| Stage | Common actions |
|---|---|
| Applied | Assign reviewer, request missing items, mark fraud-flag. |
| Under Review | Score, side-by-side compare, add reviewer note, advance to interview/decision. |
| Interview | Schedule, score, complete, advance to decision. |
| Decision | Release decision, generate offer, send notification. |

---

## 5. Batch actions

- Bulk assign reviewers.
- Bulk request missing items (template-driven).
- Bulk invite interviews.
- Bulk stage updates.
- Bulk decision release.

All trigger an audit-log entry per application.

---

## 6. Integrity signals queue

Per applicant:
- Document authenticity confidence band.
- Duplicate identity likelihood.
- Authenticity risk flags (essay AI-pattern detection — per `42-ai-agents-claude.md` §18).
- Anomaly category tags.

Workflow: review → resolve (acceptable / requires_clarification / reject_application). Audit-logged.

---

## 7. Inquiries queue (`/i/inquiries`)

New inquiries from "Request info" actions on institution/program pages.

Per inquiry:
- Status: new / in_progress / responded / closed.
- Response template (per `23-campaigns.md` templates).
- Quick reply box.
- Assign to staff.

---

## 8. Data shape

```ts
type IntakeDashboardSummary = {
  cycle: string;
  kpis: { total_apps: number; conversion_pct: number; avg_match: number; projected_yield_pct: number };
  priority_queue: Array<{ category: string; count: number; deep_link: string }>;
  intelligence_digest: string;       // AI-narrated
  yield_risk_alerts: Array<{ message: string; deadline: ISO8601 }>;
  integrity_signals_count: number;
  new_inquiries_24h: number;
  notifications_unread: number;
};

type Applicant = {
  application_id: string;
  student_id: string;
  program_id: string;
  status: ApplicationStatus;
  match_score: number;
  decision: Decision | null;
  reviewers_assigned: UserRef[];
  integrity_signals: IntegritySignal[];
  last_action_at: ISO8601;
};
```

Endpoints:
- `GET /i/dashboard/summary`.
- `GET /i/dashboard/priority-queue`.
- `GET /i/dashboard/intelligence-digest`.
- `GET /i/dashboard/integrity-signals`.
- `GET /i/dashboard/yield-risk-alerts`.
- `GET /i/applications?filters=...&page=...`.
- `POST /i/applications/batch-assign-reviewers`.
- `POST /i/applications/batch-request-missing-items`.
- `POST /i/applications/batch-invite-interviews`.
- `POST /i/applications/batch-update-status`.
- `POST /i/applications/batch-release-decision`.

---

## 9. AI integration

| Agent | Trigger | Purpose |
|---|---|---|
| Intelligence digest narrator | Daily | Plain-English digest (Sonnet) |
| Yield-risk alerts | Continuous | Identify admitted-no-response students |
| `AuthenticityRiskScorer` (`42` §18) | On essay submit | Flag potential AI patterns |
| Priority-queue ranker | Continuous | Score applicants for review priority |

---

## 10. Brand compliance

- KPI cards: large body weight 700.
- Priority queue badges: `--warning-soft`.
- Kanban column headers: eyebrow style.
- Drag indicator: `--accent` border.

---

## 11. Gaps (from `90`)

- G-D4 / G-I5: fairness signal not yet on dashboard.
- Daily intelligence digest currently AI but may be on GPT-4o; migrate to Claude per `03`.

---

## 12. Tests

- Dashboard KPI computation.
- Priority queue ordering.
- Batch actions per item count.
- Drag-and-drop status update.
- Integrity signal workflow (review → resolve).

---

## 13. Copy

- "12 applications need reviewer assignment".
- "Generate offer" (in decision column).
- "Resolve" (integrity signal action).

---

## 14. Open questions

- **Cycle archive.** End-of-cycle handoff — when does the dashboard "close" the cycle vs continue?
- **Dashboard customization per role.** Some admins want different KPIs by role; defer to Phase 2.
