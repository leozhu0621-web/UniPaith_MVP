# 25 · Campaigns — Institution Outbound

> Institution's outbound marketing workspace. Two channels: internal platform messaging to UniPaith users, and external email to uploaded lists. Trackable links route back into institution / program pages with attribution.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/i/campaigns` (also under `/i/outreach?tab=campaigns`).

---

## 1. Purpose

Plan, launch, and measure outreach campaigns tied to a specific institution / program / intake round. Build audiences (platform segments + uploaded lists); deliver messages (internal / external email); route recipients to destination pages; attribute downstream actions.

---

## 2. Campaign lifecycle

`draft → scheduled → active → paused → completed` (+ optional approval step before scheduled).

---

## 3. Campaign setup

| Field | Value |
|---|---|
| `name` | Free-text. |
| `objective` | enum<application_open, event_promotion, scholarship_announcement, deadline_reminder, nurture, general> |
| `owner` | institution user. |
| `timeline` | start date, optional end date. |
| `associate_institution_id` | always set. |
| `associate_program_ids` | 0..N. |
| `associate_intake_round_id` | optional. |
| `destination_type` | enum<institution_page, program_page, campaign_landing_page, external_url> |
| `cta_type` | enum<learn_more, rsvp_event, request_info, start_application> |
| `audience_segment_ids` | list of segment ids. |
| `uploaded_list_segment_ids` | list of uploaded-list segments. |
| `channels` | internal_messaging / external_email / both. |

---

## 4. Audience selection

Per `26-audience-segmentation.md`. Combine multiple segments + uploaded lists; deduplicate by email; apply suppression/opt-out lists.

---

## 5. Channels

### 5.1 Internal messaging
- Compose UniPaith-platform messages (student receives in their Inbox).
- Schedule sends.
- Templated messages (reusable across campaigns).
- Deep links to destination pages.

### 5.2 External email
- Compose subject + body.
- Personalization variables (`{{first_name}}`, `{{program_name}}`, `{{event_link}}`).
- Schedule sends.
- Unsubscribe handling + bounce handling.
- AWS SES under the hood.

---

## 6. Link routing + attribution

- Auto-generate trackable links per campaign × destination.
- Route clicks into the platform.
- Attribute downstream actions: view → save → RSVP → request_info → apply_started → apply_submitted → decision.

Attribution table:

```ts
type CampaignAttribution = {
  campaign_id: string;
  link_id: string;
  user_id: string | null;       // when click resolved to a known student
  clicked_at: ISO8601;
  action_taken: AttributionAction | null;
  action_at: ISO8601 | null;
};
```

---

## 7. Approval step (optional)

For institutions with internal sign-off processes. Toggle in `/i/settings`. When on:
- Campaign moves to `pending_approval` status.
- Authorized approvers see in their dashboard.
- Approve / Reject + comment.

---

## 8. Data shape

```ts
type Campaign = {
  id: string;
  institution_id: string;
  name: string;
  objective: CampaignObjective;
  owner_id: string;
  status: 'draft' | 'pending_approval' | 'scheduled' | 'active' | 'paused' | 'completed';
  associate_program_ids: string[];
  associate_intake_round_id: string | null;
  destination_type: DestinationType;
  cta_type: CtaType;
  channels: Array<'internal_messaging' | 'external_email'>;
  audience: { segment_ids: string[]; uploaded_list_ids: string[]; deduped_count: number };
  subject: string | null;            // for email
  body: string;                       // markdown
  scheduled_at: ISO8601 | null;
  sent_count: number | null;
  metrics: CampaignMetrics | null;
};

type CampaignMetrics = {
  sent: number;
  delivered: number;
  opens: number;                    // external email only
  clicks: number;
  conversions: Record<AttributionAction, number>;
  unsubscribes: number;
  bounces: number;
};
```

Endpoints:
- `GET /i/campaigns`.
- `POST /i/campaigns` / `PATCH /i/campaigns/:id`.
- `POST /i/campaigns/:id/send` (kicks off send for scheduled or active).
- `POST /i/campaigns/:id/preview-audience` — returns deduped count + 10-row sample.
- `GET /i/campaigns/:id/metrics`.
- `GET /i/campaigns/:id/attribution`.
- `GET /i/campaign-links/:id` — link metadata.

---

## 9. States

- **Empty:** "No campaigns yet. Plan your first outreach."
- **Audience preview:** "0 recipients" warning if segments yield zero after dedup/suppression.
- **Send in progress:** progress bar; send is async; metrics update over time.
- **Failure:** per-recipient failures shown in attribution view.

---

## 10. AI integration

| Agent | Trigger | Purpose |
|---|---|---|
| `CampaignAudienceCopySuggester` (`45` §16) | "Draft with AI" button | Subject + body draft |

---

## 11. Brand compliance

- Status badges for lifecycle states.
- Audience-count preview chip prominent.
- "Send" button cobalt; never gold.
- "Mark active" toggle in `--success` after schedule executes.

---

## 12. Gaps (from `47`)

- Templates page (`/i/templates`) already exists; integrate as "Start from template" CTA in campaign editor.
- Internal vs external metrics differ (opens only meaningful externally); current Analytics may not separate.

---

## 13. Tests

- Audience preview returns correct dedup.
- Internal send drops into student inboxes per consent.
- External send respects opt-out lists + suppression.
- Click → attribution row created → downstream action attributed.

---

## 14. Copy

- "Plan your first outreach."
- "Send" / "Schedule" / "Pause".
- "0 recipients after filtering. Adjust your audience."
- "Draft with AI" (button).

---

## 15. Open questions

- **Per-recipient send-time optimization.** Defer.
- **A/B test on subject.** Defer; route via two trackable links and compare clicks.
- **Internal-vs-external send compliance.** Internal respects `consent.outreach`; external respects opt-out + uploaded-list source consent. Spec'd in `46-data-rights-privacy.md`.
