# 14 · School Detail Page (Student-Facing)

> The institution-level context view — academic environment, policies, support services, cost overview, outcomes context — plus the program directory gateway. Editorial, not marketing.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s/institutions/:institutionId`.

---

## 1. Purpose

When a student wants institutional context (campus environment, support services, transfer pathways, international student considerations) separate from a specific program's deep-dive. Acts as the gateway to that school's program list.

The primary evaluation unit remains the program. The school page is context, not destination.

---

## 2. Visual layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Match · Search · University of Foo                                          │← breadcrumb
│                                                                              │
│  PRIVATE RESEARCH UNIVERSITY                                                 │← eyebrow
│  University of Foo                                                           │← H1
│  New York, NY · Founded 1831 · 51,000 students                               │← H3 muted
│                                                                              │
│  [Save school] [View all programs at this school →]                          │← actions
│                                                                              │
│  TABS:  Overview · About · Schools · Programs · Events · Updates             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tabs

### 3.1 Overview
Quick facts. Standardized institutional fields: size, campus setting, type, founded date, accreditation, top-level outcomes.

### 3.2 About
- Academic environment + student experience overview.
- Campus setting + logistical considerations.
- Support services signals relevant to common student needs (tutoring, career, counseling, disability, financial literacy).

### 3.3 Schools (default tab)
List of schools-within-institution (e.g., "School of Engineering", "Stern School of Business" for NYU). Each opens at `/s/institutions/:institutionId/schools/:schoolId`.

Each school card:
- Name + brief description.
- Program count.
- Open School view.

### 3.4 Programs
Browse all programs across all schools within this institution. Same chip + filter + sort UX as `12-discovery.md` Discovery. Default scope chip: `Institution · University of Foo`.

### 3.5 Events
Institution-level events from the institution Posts/Events feed. RSVP, add-to-calendar.

### 3.6 Updates
Institution-level posts from the social feed. Pinned posts first.

---

## 4. Sub-page — School-within-Institution (`/s/institutions/:institutionId/schools/:schoolId`)

For institutions with multiple schools (e.g., universities). Per current implementation in `SchoolSubunitPage.tsx`:

- Breadcrumb back.
- School header (name, description, optional media gallery — text-only logos per brand rule).
- Grid of programs offered by this school.
- Save / Add to Compare / Open Program on each.

---

## 5. Public + authenticated versions

- **Public** at `/school/:institutionId` — same content, but actions ("Save school", "Save program") replaced by "Sign in to save" buttons.
- **Authenticated** at `/s/institutions/:institutionId` — full functionality.

Both render the same components with an `is_authenticated` prop. Per `90` G-S9 — consolidate to single component.

---

## 6. Data shape

```ts
type SchoolDetail = {
  id: string;
  name: string;
  location: Location;
  campus_setting: 'urban' | 'suburban' | 'rural';
  size: 'small' | 'medium' | 'large' | 'very_large';
  type: 'public' | 'private' | 'community' | 'vocational';
  founded: number | null;
  student_count: number | null;
  schools: SchoolCard[];                  // sub-schools
  policies: SchoolPolicies;
  support_services: SupportServices;
  international_info: InternationalInfo;
  school_outcomes: SchoolOutcomes;
  events: Event[];
  updates: Post[];
};
```

Endpoints:
- `GET /institutions/:id` (public).
- `GET /institutions/:id/schools` — sub-schools.
- `GET /institutions/:id/programs?...` — programs (paginated, filterable).
- `GET /institutions/:id/posts` — updates feed.
- `GET /institutions/:id/events` — events.

---

## 7. States

Standard loading / empty / error. "No events scheduled" / "No updates yet" empty states.

---

## 8. AI integration

None directly on this page. Insights / similarity surface uses existing program-detail rationale agent (per `13`).

---

## 9. Brand compliance

- Text-driven; no campus photos.
- Media-gallery component normalizes input but renders text-only.
- Save / Add to Compare actions consistent with `13`.
- Tabs underline in `--accent`.

---

## 10. Gaps (from `90`)

- G-S9: public + authenticated implementations duplicated; consolidate.
- No follow / unfollow institution action — currently implicit via save-program. Spec recommendation: add explicit Follow toggle so the Connect (`/s/posts`) feed reflects student intent independent of saves.

---

## 11. Tests

- Tab routing.
- Authenticated vs public functionality differences.
- School-within-institution sub-page navigation.
- Programs tab inherits Discovery chip/filter behavior.

---

## 12. Copy

- "View all programs at this school →".
- "Save school".
- "Follow this institution" (when added).
- "No events scheduled" / "No updates yet".

---

## 13. Open questions

- **Follow vs Save.** Save is for programs; Follow could be for institutions (drives Connect feed). Confirm naming.
- **School-within-institution depth.** Some institutions have 3 levels (university → school → department). Current model handles 2. Defer 3-level support.
- **Aggregate school outcomes vs program outcomes.** Make the separation visually clear so students don't conflate a strong school average with a specific program's outcomes.
