# 20 · Institution Profile Page (Public-Facing)

> The school/college's public presence on UniPaith. Standardized institutional fields, updates feed, events, program directory — built from the same display card schema as everywhere else.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: `/s/institutions/:institutionId` (authenticated), `/school/:institutionId` (public). Mirrors student-side `14-detail-pages-school.md`.

---

## 1. Purpose

The institution's primary public destination on the platform. Where students arrive after seeing the institution in Discovery, an event invite, a campaign link, or a referral.

Editorial; not marketing. Text-driven. The institution writes their story; the platform standardizes how it's presented.

---

## 2. Card-consistent identity

Single `SchoolCard` display schema (`02-design-system.md` §5). Core fields edited once on the institution side; reflected on every surface students see.

---

## 3. Profile sections (institution-edited)

Editor at `/i/settings`. Fields:

| Section | Fields |
|---|---|
| Identity | name, type (public/private/community/vocational), country, region, city, founded, accreditation. |
| Campus | campus_setting (urban/suburban/rural), student_body_size, optional media gallery (text-only logos per brand). |
| Web presence | website, contact email/phone, social_links. |
| Story | description, campus_description, support_services overview. |
| Policies | general admissions policies, test policies, transfer pathways, international_info. |
| Outcomes | school-level outcome summaries (placement aggregates, separated from program-specific). |
| Inquiry routing | where "Request info" inquiries from this institution's page route to. |

---

## 4. Updates feed

Institution publishes posts. Per post:
- Title + body (markdown).
- Optional media attachments.
- Tag to institution overall OR specific programs.
- Pin featured posts.
- Edit/delete by authorized contributors.

Editor at `/i/posts` (see `25-posts-updates-events.md`).

---

## 5. Events module

Institution publishes events:
- Info session, webinar, campus visit, portfolio review, etc.
- Date/time, location or meeting link, capacity, notes.
- RSVP + waitlist management.
- Per-event attendees view for institution.
- Add-to-calendar for students.

Editor at `/i/events`. Each event creates a calendar item (`18-calendar.md`) for RSVP'd students.

---

## 6. Program directory

Lists all published programs under the institution. Filters/sort to browse within. Each entry: standardized `ProgramCard`. Click-through → program detail page (`13-detail-pages-program.md`).

---

## 7. Inquiry entry points

Request-info actions from the institution page route to the institution's defined inquiry destination (email / form / internal workflow queue). Per `30-admissions-intake.md` inquiry queue.

---

## 8. Public vs authenticated rendering

- Public version: actions ("Save school", "RSVP") replaced by "Sign in" CTAs.
- Authenticated version: full actions; engagement events logged.

---

## 9. Data shape

See `14-detail-pages-school.md` §6 — same `SchoolDetail` type, edited via `PATCH /institutions/:id`.

Editor endpoints:
- `GET /i/institution`.
- `PATCH /i/institution`.
- `POST /i/institution/media` — uploads (logo, optional gallery).

---

## 10. States

Standard loading / error. Empty content states: "Posts arrive here once you publish your first." / "No events scheduled."

---

## 11. AI integration

None directly on the public page. Editor uses `CampaignAudienceCopySuggester` for post drafting (Phase 2).

---

## 12. Brand compliance

- Text-driven; no decorative imagery beyond institutional logo.
- Same component reuse pattern across `13`, `14`, `20`.

---

## 13. Gaps (from `90`)

- G-I1 (major): editor uses raw JSON textareas for `social_links`, `inquiry_routing`, `support_services`, `policies`, `international_info`, `school_outcomes`. Spec says guided form-based.

---

## 14. Tests

- Public and authenticated render parity (action set differs).
- Pin/unpin reflects on public page.
- RSVP shows up in student Calendar.
- Program directory uses canonical `ProgramCard`.

---

## 15. Copy

- "Request info" (CTA on public page).
- "Sign in to save" (public, unsave action replacement).
- "Posts arrive here once you publish your first."

---

## 16. Open questions

- **Cover image / hero.** Brand spec disallows decorative imagery on program detail pages — does this extend to institution pages? Recommendation: text-driven institution pages too; campus media in a separate "Campus" tab if at all.
- **Follow institution UX.** New action — see `14` §10.
