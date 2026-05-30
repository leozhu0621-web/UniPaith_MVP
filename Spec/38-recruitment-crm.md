# 38 · Recruitment CRM (Pre-Applicant)

> The top-of-funnel workspace: managing **prospects before they become applicants**. Travel calendar, high-school / college-fair scheduling, territory management, and prospect nurturing. Extends the marketing surfaces (`23` campaigns, `24` segments, `25` events) upstream into structured recruiting operations.
>
> Status: **draft v1.0 · Phase-2** · 2026-05-29 · Route: `/i/recruitment` (tabs: `?tab=prospects|travel|territories|fairs`). Scope: enterprise recruiting depth, beyond the launch beachhead (`06` §3); sequenced after MVP.

---

## 1. Purpose

Before a student applies (`30`) or even inquires (`30` inquiries), they're a **prospect** — someone an institution wants to reach. Recruitment CRM is where admissions/recruitment staff manage that pre-applicant relationship: who to target, where to travel, which schools/fairs to visit, and how prospects progress toward applying.

This is the institution mirror of the student's pre-application discovery — and the structured layer above campaigns (`23`) and segments (`24`).

---

## 2. Sub-modules

### 2.1 Prospect management
- Prospect records: name, contact, location, interests, source (fair, list purchase, inquiry, referral, web), stage (`suspect → prospect → engaged → inquiry → applicant`).
- Prospects convert to applicants when they start an application (`30`) — the record links forward; no data loss.
- Bulk import (`22` data-upload) of prospect lists with dedup + suppression (consent-respecting, `43`).
- Prospect → segment (`24`) for campaign targeting.

### 2.2 Travel calendar
- Plan recruiter travel: trips with dates, region, budget, assigned recruiter.
- Each trip groups visits (schools, fairs) + outcomes (prospects met, leads captured).
- Conflicts/overlaps flagged; integrates with the institution events module (`25`) for hosted events.

### 2.3 High-school / college-fair scheduling
- Directory of high schools + fairs (with contacts, prior-year yield from this source).
- Register for fairs; schedule HS visits; track confirmations.
- Post-visit: capture prospects met → prospect records, tagged with the source for attribution (`26`).

### 2.4 Territory management
- Divide prospect geography into territories; assign recruiters/owners.
- Territory dashboards: prospect count, conversion rate, yield-from-territory, travel coverage.
- Workload balancing across recruiters.

---

## 3. Nurturing & conversion

- Prospects flow into campaigns (`23`) and operational messaging (`27`).
- Stage-based nurture: automated sequences per prospect stage (consent-gated marketing, `43`).
- Conversion analytics: source → prospect → inquiry → applicant → enrolled, feeding the broader funnel (`26`) and yield (`33b`).

---

## 4. Data shape

```ts
type Prospect = {
  id: string;
  name: string; email: string | null; phone: string | null;
  location: { city: string; region: string; country: string };
  interests: string[];           // program areas
  source: 'fair' | 'list' | 'inquiry' | 'referral' | 'web' | 'visit';
  stage: 'suspect' | 'prospect' | 'engaged' | 'inquiry' | 'applicant';
  territory_id: string | null; owner_id: string | null;
  converted_application_id: string | null;
  consent: { outreach: boolean };   // 43
};

type RecruitmentTrip = {
  id: string; region: string; start: ISO8601; end: ISO8601;
  recruiter_id: string; budget: number | null;
  visits: Array<{ kind: 'school'|'fair'; name: string; date: ISO8601; prospects_met: number; status: 'planned'|'confirmed'|'done' }>;
};

type Territory = { id: string; name: string; geo: object; owner_id: string | null; prospect_count: number; conversion_rate: number };
```
Endpoints: `GET/POST /i/prospects`, `POST /i/prospects/import`, `POST /i/prospects/:id/convert`, `GET/POST /i/recruitment/trips`, `GET/POST /i/recruitment/fairs`, `GET/PATCH /i/territories`.

---

## 5. AI integration

| Agent | Trigger | Output |
|---|---|---|
| `ProspectPrioritizer` | Prospect list load | Ranks prospects by apply-likelihood (uses `40` §4.15-style propensity on available signals) |
| `TerritoryOptimizer` | Travel planning | Suggests high-yield schools/fairs per territory from historical conversion |

Falls back to manual sorting. No selection decisions — prioritization + planning only.

---

## 6. States

- **Empty:** "Import a prospect list or capture leads at a fair to start."
- **Prospect converted:** badge + link to the application (`30`).
- **Trip over budget:** warning.
- **Unassigned territory:** nudge to assign an owner.

---

## 7. Brand compliance

- Operational CRM density; charts per `26` palette; no gold.
- Consent state visible on every prospect (marketing outreach gated, `43`).

---

## 8. Gaps / dependencies

- Builds on `22` (import), `24` (segments), `23` (campaigns), `26` (attribution), `27` (messaging), `30` (applicant conversion), `43` (consent).
- List-purchase ingestion must respect consent + suppression law (CAN-SPAM / GDPR) — legal review.

---

## 9. Tests

- Prospect import dedups + applies suppression; consent defaults respected.
- Prospect converts to applicant with forward link; no duplicate person record.
- Fair visit captures prospects tagged with source → shows in attribution (`26`).
- Territory dashboard math (conversion, yield) correct.

---

## 10. Copy

- "Import prospects" / "Capture a lead".
- "Converted to applicant ✓".
- "This territory has no owner — assign one."

---

## 11. Open questions

- **Overlap with inquiries (`30`).** Inquiries are inbound; prospects are outbound-targeted. Keep distinct but linked.
- **List-purchase compliance** — which sources are permitted; default to opt-in only.
- **Depth vs MVP CRM.** Full territory optimization is heavy; ship prospect + travel first, territory analytics later.
