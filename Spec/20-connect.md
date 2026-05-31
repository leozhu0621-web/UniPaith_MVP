# 20 · Connect (Student — Stage 3a)

> Stage 3a — Connection & Outreach. The student-facing feed of everything institutions they follow publish: **Updates** (posts), **Events** (RSVP-able), and **Peers** (opt-in connection with other applicants/admits). The consumption mirror of the institution authoring side (`27-posts-updates-events.md`). Lives at `/s/posts`, labeled **Connect** in the top nav.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s/posts` (tabs: `?tab=updates|events|peers`). Closes the gap flagged in `05` §4.1 (Connect was mis-pointed at `22`) and `27` §9.

---

## 1. Purpose

After a student saves programs and starts applying, the relationship with an institution becomes ongoing. Connect is the surface where that relationship lives:
- **Updates** — stay current on the institutions/programs you follow (deadline reminders, scholarship news, program changes).
- **Events** — discover and RSVP to info sessions, webinars, Q&As, portfolio reviews, campus visits.
- **Peers** — opt-in connection with other applicants and admitted students for the same programs.

Connect is **read/respond**, not authoring. Every item originates from an institution (`27`) or another student (Peers). It is the demand-side endpoint of the institution Outreach module.

---

## 2. Following model

Connect's feed is scoped to what the student **follows**.

| Trigger | Effect |
|---|---|
| Save a program (`13`) | Auto-follows that program's institution (toggle in Settings to disable auto-follow). |
| Start an application (`15`) | Auto-follows (cannot disable while application is active). |
| Explicit "Follow" on a program/school detail page (`11`/`12`) | Follows. |
| Unfollow from Connect or detail page | Removes from feed (blocked while an active application exists — explains why). |

`student_follows` table: `{student_id, institution_id, program_id|null, source: 'saved'|'application'|'explicit', created_at, muted: bool}`. Muting keeps the follow (so application context stays) but suppresses feed items.

---

## 3. Visual layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [Wordmark]   Discover · Match · Apply · Connect              [avatar]      │
├────────────────────────────────────────────────────────────────────────────┤
│  CONNECT                                                                     │
│  From the institutions you follow                                           │
│                                                                             │
│  [ Updates ]  [ Events ]  [ Peers ]            [Manage following (12) ▾]    │← tabs
│  ──────────                                                                  │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ University of Foo · CS MS · 2 days ago                       [follow]│   │← Update card
│  │ Spring scholarship deadline extended to Jan 15                       │   │
│  │ We've extended the merit-scholarship deadline…                      │   │
│  │ [View program]  [Add deadline to calendar]                         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Bar Institute · 5 days ago                                          │   │
│  │ Virtual info session — Thu Dec 12, 5pm ET           [RSVP] [☆ Save] │   │← Event-in-feed
│  └────────────────────────────────────────────────────────────────────┘   │
│  …                                                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

The three tabs share the page chrome. "Manage following" opens a panel listing followed institutions/programs with mute/unfollow toggles.

---

## 4. Updates tab

A reverse-chronological (default) or relevance-ranked feed of posts from followed institutions.

### 4.1 Update card
Uses the canonical display card (`02` §5). Fields:
- Institution + program tag + relative timestamp.
- Title + truncated body (expand inline).
- Media (if present).
- CTAs the institution attached (`27` §2.4): View program · RSVP event · Request info · Start application · Add-to-calendar.
- Follow/mute control (top-right).

### 4.2 Ranking
- Default: reverse-chronological.
- Toggle: "Most relevant" → `ConnectFeedRanker` (`45`, see §8) orders by relevance to the student's active applications + saved programs + deadlines approaching.
- Pinned institution posts (`27` §2.2 `pinned`) surface at the top of their institution's items, not the whole feed.

### 4.3 Item types in the Updates feed
- Institution post.
- Deadline reminder (system-generated from a followed program's `application_deadline`).
- Program change notice (e.g., a requirement changed on a saved/applied program — high priority, never muted).

---

## 5. Events tab

Upcoming + past events from followed institutions.

- **Upcoming** (default) / **Past** / **My RSVPs** sub-filters.
- Event card: type badge (info session / webinar / Q&A / portfolio review / campus visit / fair), title, institution, date/time in the student's timezone, location or "Online", capacity/RSVP count.
- **RSVP** → creates a Calendar item (`16`) + an Inbox confirmation (`17`) + writes `attendees` on the institution event (`27` §3.1). Waitlist if at capacity.
- **Cancel RSVP** → removes calendar item + notifies institution.
- Reminders fire per the institution's follow-up schedule (`27` §3.3) → land in Calendar + Inbox.
- Add-to-calendar without RSVP (for public events).

Event detail opens a sheet (mobile) / modal (desktop) with full description, meeting link (revealed to RSVP'd students near start time), and "Who else is going" (count only, unless Peers opt-in reveals names).

---

## 6. Peers tab (opt-in, privacy-gated)

Connect students with shared application context. **Off by default** — requires explicit opt-in, consent-gated per `46`.

### 6.1 Opt-in gate
First visit shows an explainer + toggle: *"Connect with other applicants. Others can find you by shared programs and see only what you choose to share."* Writes `consent.peer_connect=true` (a new consent dimension; default false; revocable). No peer data is read or shown until opted in.

### 6.2 What's shared (student-controlled)
A peer-visibility sub-profile, separate from the application profile. Student picks fields to expose: display name or alias, target programs/schools (from saved/applied), intended major, general location (country/region, never address), a short bio. **Never** exposed: scores, GPA, documents, decisions, financials.

### 6.3 Discovery + connection
- "Applicants to programs you're considering" + "Admitted students at schools you applied to" (admits opt-in separately to mentor).
- Send connect request → on accept, a peer thread opens in Inbox (`17`) as a `peer` thread type (distinct from `human`/`system`).
- Block/report controls on every peer card. Reports route to a moderation queue.

### 6.4 Safety
- Rate-limit connect requests (anti-spam).
- No minors-to-adults peer matching (gate on `adult_minor_status`, `42` §3.2).
- All peer messaging subject to the same content moderation as Inbox.

---

## 7. Data shape

```ts
type ConnectFeedItem =
  | { kind: 'post'; post: Post; institution: InstitutionRef; program: ProgramRef | null }
  | { kind: 'event'; event: Event; rsvp_state: 'none'|'rsvp'|'waitlist'|'attended' }
  | { kind: 'deadline'; program: ProgramRef; deadline: ISO8601 }
  | { kind: 'program_change'; program: ProgramRef; change_summary: string };  // never muted

type Follow = {
  institution_id: string;
  program_id: string | null;
  source: 'saved' | 'application' | 'explicit';
  muted: boolean;
};

type PeerCard = {
  peer_id: string;            // opaque; not the student_id
  display_name: string;       // or alias
  shared_programs: ProgramRef[];
  intended_major: string | null;
  region: string | null;
  bio: string | null;
  connection_state: 'none' | 'requested' | 'connected' | 'blocked';
};
```

Endpoints:
- `GET /me/connect/feed?tab=updates&rank=recent|relevant`.
- `GET /me/connect/events?scope=upcoming|past|mine`.
- `POST /me/connect/events/:id/rsvp` / `DELETE …/rsvp`.
- `GET /me/follows` · `POST /me/follows` · `PATCH /me/follows/:id` (mute) · `DELETE /me/follows/:id`.
- `POST /me/connect/peers/opt-in` (sets `consent.peer_connect`).
- `GET /me/connect/peers?program_id=…` · `POST /me/connect/peers/:peerId/request` · `POST …/block` · `POST …/report`.

---

## 8. AI integration

| Agent | Trigger | Output |
|---|---|---|
| `ConnectFeedRanker` (`45` — NEW, see §below) | "Most relevant" toggle / feed load | Ranked feed by relevance to applications + saved + deadlines |
| `EventRecommender` | Events tab | Suggests events on followed programs the student hasn't RSVP'd |

Both fall back to reverse-chronological / unranked if the agent fails or `consent.matching=false`. No AI reads peer data unless `consent.peer_connect` AND `consent.matching` are both true. Add `ConnectFeedRanker` + `EventRecommender` to `45` agent registry (Haiku-tier, cheap ranking).

---

## 9. States

- **No follows:** "Follow a program to see updates here." → CTA "Find programs" → `/s/explore`.
- **Follows but no items:** "You're following 12 institutions. New updates will appear here."
- **Peers not opted in:** the opt-in explainer (§6.1) is the entire tab body.
- **Peers opted in, no matches:** "No peers yet for your programs. We'll notify you as more applicants join."
- **Event at capacity:** RSVP button → "Join waitlist."
- **AI rank failure:** silently falls back to recent; no error shown.

---

## 10. Brand compliance

- Cards per `02` §5; event type badges per `02` §11.
- **Gold is reserved** for the RSVP-confirmed state and a pinned-institution marker — Connect is mostly cobalt + neutral; it's a feed, not a celebration.
- Peer cards never show numeric scores or rings (privacy).
- "Add to calendar" / "View program" CTAs cobalt; no decorative imagery (per project UI rules — editorial, not marketing).

---

## 11. Gaps (relative to current code)

- The route `/s/posts` exists in the IA but no Connect page is implemented (per `05` §4.1; this doc + `47` G-S-Connect).
- `consent.peer_connect` is a NEW consent dimension — add to `46` §2 consent set + `42` §3.2 + the Settings/Data tab.
- `student_follows` table is NEW.
- Peer threads are a NEW `17` thread type (`peer`).
- `ConnectFeedRanker` + `EventRecommender` agents NEW in `45`.

---

## 12. Tests

- Saving a program auto-creates a follow; unfollow blocked while application active.
- Feed shows items only from followed institutions; muted institutions suppressed; `program_change` items never suppressed.
- RSVP → Calendar item + Inbox confirmation + institution `attendees` row; capacity → waitlist.
- Peers tab shows nothing until `consent.peer_connect=true`.
- Peer card never includes score/GPA/financial fields (contract test).
- Minor cannot receive adult peer requests.
- Relevance rank falls back to recent on agent failure.

---

## 13. Copy

- "From the institutions you follow" (H1 sub).
- "Follow a program to see updates here." (empty).
- "Connect with other applicants" (peers opt-in).
- "Others can find you by shared programs and see only what you choose to share."
- "Join waitlist" / "RSVP'd ✓" / "Add to calendar".
- "This program changed a requirement" (program_change item).

---

## 14. Open questions

- **Peer connection scope for MVP.** Full peer messaging may be heavier than MVP needs. Option: ship Updates + Events for MVP, gate Peers behind a flag (`connect_peers_enabled`) and launch after moderation tooling is ready. Recommend: **Updates + Events MVP; Peers fast-follow.**
- **Deadline items vs Calendar.** Deadline reminders appear in both Connect and Calendar (`16`). Confirm that's desired (redundancy aids recall) vs Calendar-only.
- **Following without saving.** Should a student be able to follow an institution they haven't saved a program from? Yes — explicit follow from the school page (`12`).
- **Admit-mentor program.** Admitted students mentoring applicants is high-value but needs its own light spec (verification that they're actually admitted). Defer to a Phase-2 note.
