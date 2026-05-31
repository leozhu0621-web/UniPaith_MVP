# 36 · Audit Log

> Append-only audit trail for compliance + operational visibility. Every consequential action records who/what/when.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/i/audit-log` (institution); student-side data-access log at `/s/profile?tab=data`.

---

## 1. Purpose

Compliance, fairness audits, incident investigation. Demonstrably proves: "we know who did what."

---

## 2. Event categories

| Category | Examples |
|---|---|
| `status_change` | Application status transition. |
| `decision_release` | Decision released to student. |
| `reviewer_assigned` | Reviewer assigned/removed. |
| `checklist_change` | Checklist item completed/blocked/overridden. |
| `document_replaced` | Document deleted, replaced, or version updated. |
| `waiver_override` | Requirement waived for an applicant. |
| `batch_*` | Any batch action — assign reviewers / release decisions / request missing items / invite interviews / update statuses. |
| `ai_generated` | AI artifact accepted / edited / rejected (per `37-ai-extensibility.md`). |
| `consent_change` | Student consent toggle flipped. |
| `data_export` | Data export download. |
| `data_deletion` | Account deletion request / completion. |
| `fairness_signal_override` | Per `46` §6 override. |
| `integrity_resolution` | Integrity signal acknowledged / resolved / rejected. |

---

## 3. Per-event fields

```ts
type AuditEvent = {
  id: string;
  institution_id: string | null;          // null for platform-wide events
  category: AuditCategory;
  action: string;                         // specific action within category
  actor_id: string;
  actor_role: 'student' | 'institution_admin' | 'system' | 'ai_agent';
  entity_type: 'application' | 'checklist_item' | 'document' | 'review' | 'interview' | 'offer' | 'consent' | 'segment' | 'campaign';
  entity_id: string;
  before: object | null;                  // state before action (diff)
  after: object | null;                   // state after action (diff)
  reason: string | null;                  // free-text rationale (required for overrides)
  ip_address: string | null;
  user_agent: string | null;
  occurred_at: ISO8601;
};
```

Append-only — never updated, never deleted.

---

## 4. Filtering UX

```
AUDIT LOG

[Filter: Action ▾]  [Filter: Entity ▾]  [Filter: Actor ▾]  [Date range]

TABLE
  Timestamp           Actor             Action                  Entity
  Dec 8 10:42         Maya Park         decision_release        Application #12
  Dec 8 10:30         system            ai_generated:summary    Application #11
  Dec 8 09:15         Sienna Chen       consent_change          consent.training
  …
```

Click row → detail panel with `before` / `after` diff + reason.

---

## 5. Endpoints

- `GET /i/audit-log?filter=...&page=...`.
- `GET /audit-log/:id` — single event with full diff.
- `GET /s/profile/access-log` — student-facing subset (who saw your data).

---

## 6. Retention

7 years per `46-data-rights-privacy.md` §5.

---

## 7. States

- **Empty (no filter matches):** "No events match your filters."
- **Loading:** skeleton rows.

---

## 8. AI integration

None. Audit log is the substrate other surfaces consume.

---

## 9. Brand compliance

- Plain table; no chrome.
- Actor badges color-coded (system = gray; student = cobalt; institution = body; AI = gold).
- Override events highlighted (`--warning-soft`).

---

## 10. Gaps (from `47`)

- G-C3 (minor): missing event types (ai_generated, consent_change, data_export, data_deletion, fairness_signal_override) — extend.

---

## 11. Tests

- Append-only enforced (no UPDATE/DELETE on `audit_events`).
- Every category writes a row from its trigger point.
- Filtering correctness.
- Pagination handles large logs.

---

## 12. Copy

- "No events match your filters."
- "Override reason: ..." (in detail panel).

---

## 13. Open questions

- **Export.** Compliance ops may need CSV exports of filtered ranges. Add `?format=csv`.
- **Long-term storage.** After 7 years, archive to cold storage and purge from primary DB.
- **Cross-institution events.** Platform-wide events visible only to platform staff (none in MVP since no platform admin role).
