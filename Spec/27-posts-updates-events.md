# 27 · Posts, Updates & Events

> Unified publishing + distribution module for institutions. Posts, updates, events — with media, targeting scopes, promotion controls, and performance tracking.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: `/i/posts`, `/i/events`, `/i/promotions`.

---

## 1. Purpose

One workspace for everything an institution publishes that reaches students. Posts (text updates), events (with RSVP), promotions (time-boxed featured placements).

---

## 2. Posts

### 2.1 Compose
- Title + body (markdown).
- Optional media (S3-uploaded).
- Tag to institution overall OR specific programs.
- Tag to specific intakes / rounds.
- Schedule send (immediate / scheduled).
- Reuse post templates.

### 2.2 Lifecycle
`draft → scheduled → published → archived` (+ optional `pinned` toggle).

### 2.3 Visibility scope
- Public on institution / program pages (default).
- Distributed into targeted student feeds (audiences).
- Limited to selected regions / interest areas.

### 2.4 CTAs attached
- View program.
- RSVP event.
- Request info.
- Start application.
- Add-to-calendar.

---

## 3. Events

### 3.1 Compose
- Type: info session / webinar / Q&A / portfolio review / campus visit / fair.
- Linked institution + optional program(s) + intake/round.
- Date/time, location or meeting link, capacity, notes.
- RSVP management (list, capacity, waitlist).
- Attendance capture (scheduled / completed / no-show).

### 3.2 Lifecycle
`draft → scheduled → live → completed → archived`.

### 3.3 Follow-ups
- Scheduled reminders for upcoming events.
- Post-event follow-ups segmented by attended vs no-show.
- Reuse follow-up templates across repeated event series.

---

## 4. Promotions

### 4.1 Setup
- Title + description.
- Link to a program OR institution OR custom landing.
- Date range.
- Target regions / countries / degrees / interest areas.
- Type: spotlight / featured / banner.

### 4.2 Eligibility checks (minimal)
- Page published.
- Deadlines present (if applicable).

### 4.3 Promotion controls
- Campaign tags (launch, scholarship, recruitment season).
- Spotlight/featured time-boxed.
- Targeting scopes (region, degree level, modality, interest area).

### 4.4 Lifecycle
`draft → scheduled → active → paused → expired`.

---

## 5. Performance tracking

Per post / event / promotion:
- Impressions / views.
- Clicks.
- Saves.
- RSVPs.
- Attendance rate (events).
- Request_info.
- Apply_started.

Breakdown by program / intake + audience segment + time window. Feeds `28-attribution-funnel-analytics.md`.

---

## 6. Data shape

```ts
type Post = {
  id: string;
  institution_id: string;
  title: string;
  body: string;
  media_urls: string[];
  tagged_program_ids: string[];
  tagged_intake_id: string | null;
  status: 'draft' | 'scheduled' | 'published' | 'archived';
  pinned: boolean;
  scheduled_for: ISO8601 | null;
  published_at: ISO8601 | null;
  visibility: { public: boolean; targeted_segment_ids: string[]; region_scopes: string[] };
  ctas: Array<{ type: CtaType; label: string; target: string }>;
};

type Event = {
  id: string;
  institution_id: string;
  name: string;
  type: EventType;
  start_at: ISO8601;
  end_at: ISO8601;
  location: string | null;
  meeting_link: string | null;
  capacity: number | null;
  description: string;
  tagged_program_ids: string[];
  tagged_intake_id: string | null;
  status: 'draft' | 'scheduled' | 'live' | 'completed' | 'cancelled';
  rsvp_count: number;
  waitlist_count: number;
  attendees: Array<{ student_id: string; status: 'rsvp' | 'attended' | 'no_show' }>;
};

type Promotion = {
  id: string;
  institution_id: string;
  title: string;
  description: string;
  type: 'spotlight' | 'featured' | 'banner';
  target_kind: 'program' | 'institution' | 'landing';
  target_id: string;
  start_at: ISO8601;
  end_at: ISO8601;
  scope: { regions: string[]; countries: string[]; degrees: DegreeType[]; interest_areas: string[] };
  status: 'draft' | 'scheduled' | 'active' | 'paused' | 'expired';
};
```

Endpoints:
- `GET /i/posts`, `POST /i/posts`, `PATCH /i/posts/:id`, `POST /i/posts/:id/publish`, `POST /i/posts/:id/pin`, `DELETE`.
- Similar for events + promotions.
- `POST /i/posts/media-upload-url` — pre-signed.
- `GET /i/events/:id/attendees`.

---

## 7. States

- **Empty:** "No posts yet." / "No events scheduled." / "No active promotions."
- **Scheduled-for-future:** banner showing scheduled time.
- **Cancelled event:** badge + RSVP'd students notified.

---

## 8. AI integration

- `CampaignAudienceCopySuggester` (`45` §16) — drafts post body + subject lines.

---

## 9. Brand compliance

- Pin badge in `--primary` (the one earned accent).
- Status badges per `02` §11.
- Event card layout consistent across student-facing surfaces.

---

## 10. Gaps (from `47`)

- Templates page integration: posts can start from a template (Templates page already exists).
- Promotion targeting scope vs Audience Segmentation: spec recommends sharing the segment infrastructure.

---

## 11. Tests

- Post draft → schedule → publish → pinned displays correctly.
- Event RSVP → student Calendar item + Inbox confirmation.
- Promotion display on the right surfaces per scope.
- Performance metrics roll up correctly per object.

---

## 12. Copy

- "Publish post" / "Schedule post" / "Save draft".
- "Pin to top" / "Unpin".
- "RSVP'd: 42 / 50".
- "Attendees: 38 of 42 RSVPs".

---

## 13. Open questions

- **Post → email digest.** Should we auto-email pinned posts as part of the weekly digest? Defer.
- **Live event integration.** Embed Zoom/Webex meeting links cleanly with capacity sync. Defer.
- **A/B testing on post titles.** Defer.
