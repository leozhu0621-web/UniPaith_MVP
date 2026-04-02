# Student Screen Redesign Specs (Hybrid, Anti-Stress)

## Scope

These specs redesign interaction and emotional framing without removing features:
- `StudentLayout`
- `DashboardPage`
- `DeadlinesPage`
- `ApplicationDetailPage`
- `ChatPage`

## 1) StudentLayout

### Changes
- Group left navigation into journey sections: Plan / Discover / Apply / Utility.
- Keep compact icon style but add section labels for orientation.
- Route brand click to `/s/dashboard` (home anchor).
- Keep progress bar, but rename to “Profile support progress”.

### UX Objective
- Lower navigation anxiety and improve process orientation.

## 2) DashboardPage

### Changes
- Reframe header to “Today with your admissions counselor”.
- Replace high-metric emphasis with:
  - one primary next action,
  - one confidence checkpoint,
  - one recommended weekly focus.
- Keep matches/applications/deadlines cards but soften wording.
- Keep deadlines visible, reduce panic labels.

### UX Objective
- Make dashboard feel like guided briefing, not performance board.

## 3) DeadlinesPage

### Changes
- Replace “urgent alert” with “Focus this week” supportive card.
- Retain timeline and badges but use calmer labels:
  - Focus now (0–7 days),
  - Plan this week (8–30),
  - Upcoming.
- Add explicit action CTA in urgent card (open target item).

### UX Objective
- Preserve urgency while reducing anxiety spikes.

## 4) ApplicationDetailPage

### Changes
- Translate status timeline labels to plain language:
  - Drafting, Submitted, Under Review, Interview Stage, Decision.
- Add reassurance copy near submission action.
- Keep readiness modal but introduce “You are closer than you think” framing.
- Keep checklist behavior unchanged.

### UX Objective
- Improve trust and reduce fear during high-stakes steps.

## 5) ChatPage

### Changes
- Shift from generic AI label to counselor framing.
- Add supportive starter copy and explicit capability framing.
- Show graceful error recovery for send failures.
- Keep quick actions but prioritize calming advisor prompts.

### UX Objective
- Make chat feel personal, safe, and genuinely helpful.

## Implementation Notes

- Keep API endpoints and feature capabilities unchanged.
- Prioritize copy hierarchy and information architecture first.
- Add empathetic error states for all query/mutation failures on these screens.
