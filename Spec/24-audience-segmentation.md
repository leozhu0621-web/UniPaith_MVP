# 24 · Audience Segmentation

> Segment builder for Campaigns and Outreach. Combines platform activity signals + student intent/readiness signals + uploaded contact lists. Outputs reusable saved segments.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/i/segments` (also under `/i/communications?tab=segments`).

---

## 1. Purpose

Build reusable audiences for outbound campaigns, event invites, and follow-ups. Compose from signals already in the platform; no SQL or data-engineering required.

---

## 2. Segment composition

A segment is a set of rules over student fields. Three kinds of inputs:

### 2.1 Platform activity signals
- Viewed / saved / compared institution or program pages.
- Requested info.
- Event RSVP / attended / no-show.
- Started application / started but not submitted.
- Engaged with posts / updates.

### 2.2 Intent & motivation signals
- Job-first / credential-first / research-first / exploration.
- Career switch vs career advance vs first-job intent.
- Outcome priorities (internships, employer network, placement focus).
- Tradeoff preferences (cost, location, modality, selectivity, timeline).
- Field/role interest tags.

### 2.3 Constraints & readiness signals
- Budget sensitivity bands.
- Modality preference.
- Timeline urgency (this intake / next / later).
- Prerequisites / portfolio readiness bands.
- Documentation readiness stage.

### 2.4 Fit and likelihood (platform-computed)
- Fit-to-program-family bands (high/medium/low).
- Likelihood-to-apply bands.
- Nurture-needed bands.

### 2.5 Uploaded lists
- CSV imports from `22-data-upload.md`.
- Tag contacts; track list source.
- Merge/deduplicate with platform users by email.
- Suppression / opt-out lists honored.

---

## 3. Editor UX

```
SEGMENTS

[+ New segment]  [Filter: Active ▾]

SEGMENT: "High-interest CS prospects who haven't started an app"

Rules
  Include
    · Viewed our institution page in the last 30 days
    · OR Saved any program of degree_type=master AND major=CS
    · AND fit-band ≥ high

  Exclude
    · Already started application (this institution)
    · Unsubscribed from outreach

Audience: ~342 students

[Save segment]  [Preview audience]  [Use in campaign →]
```

Rules expressed as include/exclude branches with AND/OR logic. Audience size + composition preview.

---

## 4. Plain-language rule rendering

Each rule shows as a plain sentence: "Viewed our institution page in the last 30 days" — not raw operators. Hover reveals the underlying field + operator + value.

Manual edits supported via a "raw rule editor" for advanced users.

---

## 5. Frequency caps + suppression

- Optional per-segment max-sends-per-week.
- Global institution suppression list applied automatically.
- Per-campaign suppression list (e.g., "exclude attendees of last event") composable into the segment.

---

## 6. AI assist

`SegmentBuilderNLBridge` agent (`42` §17) — convert natural language ("students who saved Engineering programs in California with budget ≤ $40k") to structured rules. Confidence + ambiguity notes shown; user edits before saving.

---

## 7. Data shape

```ts
type Segment = {
  id: string;
  institution_id: string;
  name: string;
  description: string;
  rules: SegmentRuleTree;        // nested include/exclude branches
  uploaded_list_ids: string[];
  preview_audience_count: number | null;
  preview_audience_sample: StudentSummary[];   // first 10
  frequency_cap_per_week: number | null;
  active: boolean;
  created_by: UserRef;
  updated_at: ISO8601;
};

type SegmentRuleTree = {
  op: 'AND' | 'OR' | 'NOT';
  rules: Array<SegmentRule | SegmentRuleTree>;
};

type SegmentRule = {
  field: string;                  // platform field name
  operator: 'equals' | 'in' | 'gt' | 'lt' | 'between' | 'within_days' | 'contains' | 'has_band';
  value: any;
};
```

Endpoints:
- `GET /i/segments`.
- `POST /i/segments` / `PATCH /i/segments/:id`.
- `POST /i/segments/:id/preview` — returns count + 10-row sample.
- `POST /i/segments/nl-bridge` — calls `SegmentBuilderNLBridge`.

---

## 8. States

- **Empty:** "No segments yet. Build one to target campaigns and events."
- **Preview loading:** count placeholder + spinner.
- **Zero matches:** "0 students match these rules. Try widening criteria."
- **AI ambiguity:** rule cards rendered with `?` chip on ambiguous parts.

---

## 9. Brand compliance

- Rule chips per `02` §9.
- Audience count in `--accent` to surface as the key metric.
- "Use in campaign →" CTA cobalt.

---

## 10. Gaps (from `90`)

- `SegmentBuilderNLBridge` agent doesn't exist; build per `42` §17.
- Saved segments + uploaded lists shared with Campaigns wiring already exists.

---

## 11. Tests

- Rule tree composition correctness across AND/OR/NOT.
- Preview audience count consistent with rule semantics.
- Uploaded list merge by email correct.
- Suppression list applied before preview count.
- AI NL bridge: representative cases return correct structured rules.

---

## 12. Copy

- "Build one to target campaigns and events."
- "0 students match these rules. Try widening criteria."
- "Try AI assist: type what audience you want →".

---

## 13. Open questions

- **Real-time membership update.** When does segment membership refresh? Recommend: on-demand for preview; recomputed at campaign-send time for accuracy.
- **Lookalike audiences.** "More students like the ones who attended my last event" — defer; flag as Phase 2.
- **Per-segment fairness check.** Per `43` §6 — if a segment heavily skews on a protected attribute, surface a warning before send.
