# Profile refinement — inline Basic info · drop header/ring · Identity redesign (design)

**Date:** 2026-06-16 · **Status:** Approved by founder (mockup approved) · **Scope:** frontend-only, no API/schema change

## 1. Basic info — inline editable
`profile/OverviewTab.tsx` (the `overview` / "Basic info" tab) stops being a read-only
card + "Edit personal info" modal. It renders the `BasicInfoForm` **inline**: a small
avatar + name/email header, then the live form (first/last name, pronouns, DOB,
nationality, country, bio, goals) with its own **Save**. `updateProfile` on submit
(unchanged); no modal.

## 2. Delete the shared profile header + completion ring
`ProfilePage.tsx` drops the `<PageHeader eyebrow="My Space" title="Your record"
sub=… actions={<CompletionRing/>}>` block shown above every profile tab. The rail
already names the active tab and the top nav shows "My Space", so the header is
redundant. Remove `CompletionRing` + `lastUpdatedLabel` usage and the
`useCompletion` reads that only fed it (keep `useCompletion` only if still needed
elsewhere; otherwise drop).

## 3. Identity tab — summary-led, compact (presentation only)
`profile/IdentityTab.tsx`. Direction unchanged (Core values · Worldview ·
Self-awareness + AI summary; same backend). New presentation:
- **"Who you are" AI summary leads** — a hero card at the top (eyebrow + `AIBadge` +
  Regenerate) with the synthesized paragraph, or a one-line prompt when empty. Moved
  up from the bottom.
- **Three layers as compact cards in a grid** — `grid lg:grid-cols-2`; Core values and
  Worldview side by side, **Self-awareness spans the row** (its items go 2-up).
  Each layer is a bordered card with an icon + title + a small "+ Add"; items render
  as light **border-left rows** (title + muted evidence/context, optional quote),
  not full Cards.
- **Small empty states** — replace the big centered `EmptyState` with a one-line
  clickable hint: "Nothing yet — add a value, or let Uni surface it from your chats."
- Tighter vertical rhythm (`space-y-4`); per-section hint text dropped (less wordy).
  Add/Edit modal flow unchanged.

## Out of scope
No backend, schema, route, or IA-spec change. Only OverviewTab, IdentityTab, and the
ProfilePage header.

## Verification
tsc 0 · vite build 0 · eslint 0 errors · one quick preview screenshot of Basic info +
Identity to confirm fidelity to the approved mockup, then ship.
