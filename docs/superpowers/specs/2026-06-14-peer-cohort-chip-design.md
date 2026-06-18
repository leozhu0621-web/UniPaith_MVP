# Privacy-safe peer-cohort chip (Discover review idea #5)

**Date:** 2026-06-14
**Status:** Approved (user: "approve, continue")
**Benchmark:** LinkedIn "N connections work here" / Handshake "students from your school applied here".

## Goal

Surface a privacy-safe aggregate — "**N peers open to connect**" — on program cards
(MatchCard / ProgramCard), so an opted-in student browsing programs sees where their
potential peers are, deep-linking into the Peers tab. **Zero identities, ever** — only a
k-anonymized count.

## Privacy model (the hard constraints)

The peer system is privacy-first by construction (verified against `models/peer.py`,
`services/peer_service.py`, `models/student.py`). The chip MUST preserve every existing gate:

1. **Flag** — gated on `connect_peers_enabled` (the existing `_require_peers_enabled()`),
   ON in prod today.
2. **Viewer consent** — the viewer must be opted-in (`student_data_consent.consent_peer_connect = true`).
   Per the existing contract ("No peer data is read or shown until this is true"), an
   aggregate derived from peer profiles IS peer data — so it flows only among consenting
   participants. A non-opted-in viewer gets an empty result (no counts), never the chip.
   *(Deliberately conservative. Turning the chip into an opt-in nudge for non-participants
   is a future product/privacy decision, not assumed here.)*
3. **Counted peers** — only students who are `peer_profiles.visible = true` AND
   `consent_peer_connect = true` (mirrors `discover()`), in the SAME age bucket as the
   viewer (minor↔adult blocked, §6.4), excluding the viewer and any blocked-either-direction
   peers.
4. **k-anonymity** — NEW (none exists in the codebase): a program's count is returned only
   when it is `>= PEER_COHORT_MIN` (=3). Below the floor → the program is omitted from the
   response entirely (the UI shows no chip). This prevents re-identification from a count
   of 1–2 in a small shared pool.

A peer's "target programs" are derived exactly as `discover()` does: union of
`saved_list_items.program_id` (via `saved_lists.student_id`) and `applications.program_id`.

## Backend

**`PeerService.cohort_counts(student_id, program_ids) -> dict[UUID, int]`** (new):
- If the viewer isn't opted-in (`consent_peer_connect` false) → return `{}` (no leak).
- Compute the viewer's age bucket + blocked set (reuse the existing `_age_bucket` +
  block-loading helpers `discover()` already uses).
- One query: candidate (program_id, student_id) pairs from `saved_list_items`+`saved_lists`
  and `applications` where `program_id IN program_ids` and `student_id != viewer`; join
  `peer_profiles` (visible) + `student_data_consent` (consent_peer_connect); drop blocked +
  age-mismatched. Count DISTINCT student_id per program_id.
- Return only `{program_id: count}` for counts `>= PEER_COHORT_MIN`. `PEER_COHORT_MIN = 3`
  is a module constant.

**Route** — `POST /connect/peers/cohort-counts` (in `api/connect.py`, under
`_require_peers_enabled()` + `require_student`), body `{program_ids: [UUID]}` (cap ~100),
response `{counts: {program_id: count}}`. Batch (one request for a whole card grid), not
per-card. No new table, no migration.

## Frontend

- **API** — `getPeerCohortCounts(programIds: string[]) => Promise<Record<string, number>>`
  in `api/connect.ts` (POST). Returns `{}` on any error (never blocks cards).
- **ExplorePage** — a `peerCohortByProgram` map built like `nextEventByInst`: gather the
  visible program ids (matches + search results), one query, gated on `peersEnabled &&
  peersStatus.opted_in` (skip entirely otherwise). Thread a `peerCount?: number` +
  `onPeersClick?` into MatchCard / ProgramCard.
- **Cards** — when `peerCount` is present, render a muted chip "👥 N open to connect"
  (cobalt, Users icon, no gold) next to the existing chips; click → `setTab('peers')`.
- The chip only appears for programs with `count >= 3` (backend already suppressed the rest).

## Testing

- **Backend** (`tests/test_connect_peers.py`): cohort_counts returns counts only ≥ k;
  suppresses a 1–2 peer program (omitted); excludes non-visible / non-consented / blocked /
  age-mismatched peers; returns `{}` when the viewer isn't opted-in. Route 200 + shape; 404
  when flag off.
- **Frontend**: API maps response; ExplorePage skips the query when not opted-in (no chip);
  card renders the chip when peerCount ≥ 1 (backend guarantees ≥ k).
- tsc 0 · build 0 · backend test green · vitest green; ship + verify live (route 422 w/o
  body, chip marker in bundle).

## Out of scope

Per-program pre-filtered Peers tab deep-link (the tab doesn't read a program filter from
the URL today) — chip links to the Peers tab generally; the pre-filter is a follow-up.
