# 28 · Attribution & Funnel Analytics

> Reporting module attributing student actions to institution content + outreach, summarizing performance across the recruitment funnel from exposure to application progress.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/i/analytics`.

---

## 1. Purpose

Where institutions see whether their content, events, and campaigns are working. Reports stage-to-stage conversion, top-performing assets, and per-segment performance.

---

## 2. Attribution model

Every student action that COULD have a source carries an attribution row. Sources:
- Institution page view.
- Program page view.
- Post / promoted placement.
- Event RSVP / attendance / follow-up engagement.
- Campaign (internal message or external email) via trackable links.

Actions:
- Impression / view.
- Click.
- Save / unsave.
- Compare.
- Request info / ask question.
- Apply_started → submitted → decision_outcome.

---

## 3. Funnel stages

Three sub-funnels institutions track:

### 3.1 Discovery funnel
Impression → View → Click → Save → Compare → Request_info.

### 3.2 Event funnel
RSVP → Attendance → Post-event engagement.

### 3.3 Application funnel
Apply_started → Submitted → Decision_outcome.

Each stage has a conversion rate to the next.

---

## 4. Visual layout

```
ANALYTICS

[ Overview · Funnel · Attribution ]

KPI ROW (Overview tab)
  Total apps · Acceptance rate · Avg match · Yield

FUNNEL CHART
  Impressions:    12,400  ──────────────────────────
  Clicks:          2,100  ────────────
  Saves:             840  ────
  Apps started:      210  ─
  Submitted:         180
  Accepted:           24

BREAKDOWN BY
  Program: dropdown
  Intake: dropdown
  Segment: dropdown
  Campaign: dropdown
  Time window: dropdown

TOP CONTENT
  By clicks
  By apply_started

DROP-OFF ANALYSIS
  Biggest drop: Saves → Apps started (75% drop). Investigate ▾
```

---

## 5. Dimensions for breakdown

- Program / intake round / campaign.
- Audience segment.
- Time window (custom range, last 7d, last 30d, last 90d, YoY).
- Source object (institution page, program page, specific post, specific event).

---

## 6. Operational metrics for outreach

Per campaign:
- Send volume.
- Delivery rate.
- Open / click (where supported — internal vs external).
- RSVP + attendance rates for events.

---

## 7. Reports + export

- Built-in dashboards.
- Per-dashboard CSV export.
- Saved views (URL state) for repeat reporting.
- Scheduled email reports (weekly digest to institution admins). Defer.

---

## 8. Data shape

Analytics is read-mostly from event-sourced data. Backend:

```ts
type AttributionEvent = {
  id: string;
  institution_id: string;
  student_id: string | null;
  source_kind: 'institution_page' | 'program_page' | 'post' | 'event' | 'campaign' | 'promotion';
  source_id: string;
  action: AttributionAction;
  campaign_id: string | null;
  program_id: string | null;
  intake_round_id: string | null;
  segment_id: string | null;
  occurred_at: ISO8601;
};

type FunnelReport = {
  filter: { program_id?, intake_id?, segment_id?, campaign_id?, time_window };
  stages: Array<{ stage: string; count: number; conversion_from_prev: number }>;
  top_sources: Array<{ source_id: string; source_kind: string; action_count: number }>;
  drop_off_alerts: Array<{ from_stage: string; to_stage: string; drop_pct: number; hint: string }>;
};
```

Endpoints:
- `GET /i/analytics/overview?...`.
- `GET /i/analytics/funnel?...`.
- `GET /i/analytics/attribution?...`.
- `GET /i/analytics/export?...&format=csv`.

---

## 9. States

- **Insufficient data:** "Not enough events in this window to plot."
- **Loading:** skeleton chart placeholders.
- **Filtered to zero:** "No events match these filters."

---

## 10. AI integration

None directly. Future: `AnalyticsInsightsNarrator` that drafts a 3-bullet "what's notable this week" summary at the top of the Overview. Defer.

---

## 11. Brand compliance

- Chart palette per `02-design-system.md` §14 (cobalt primary, gold accent, then status colors).
- Top-of-tab KPI cards: large body weight 700; eyebrow above; muted comparison ("+12% vs prior 30 days").
- Drop-off alerts surface in `--warning-soft` cards.

---

## 12. Gaps (from `47`)

- G-I2 (minor): hand-rolled CSS bar charts; migrate to `recharts` for proper rendering.
- Conversion rates per intake round not yet broken out separately.

---

## 13. Tests

- Funnel computes correctly per fixture.
- Filters apply consistently.
- Top-sources sort by clicks vs apply_started.
- Drop-off alert fires above threshold.

---

## 14. Copy

- "Not enough events in this window to plot."
- "Biggest drop: Saves → Apps started (75% drop). Investigate ▾".
- "+12% vs prior 30 days" (comparison sub-line).

---

## 15. Open questions

- **Cross-institution benchmarks.** Show "your apply_started rate is 4% vs platform median 6%"? Useful but requires careful framing to avoid leaking PII or competitive data. Defer.
- **Attribution model — first-touch vs multi-touch.** Spec defaults to last-touch attribution; multi-touch model (linear / time-decay) Phase 2.
- **Real-time vs nightly.** KPIs real-time; deep breakdowns nightly. Fairness signals (per `46`) are real-time.
