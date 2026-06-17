# Uni chat → rich, widget- & picture-forward conversation (design brief)

**Date:** 2026-06-14 · **Status:** Brainstorm complete, HANDED OFF to the Uni QA session · **Reference app:** Imprint (founder's stated UX/visualization/animation north star).

## Why

The Uni discovery chat (`/s`, `pages/student/discover/UniConversation.tsx`) replies in **plain text only**. The founder finds this "childish" — not because it's too playful, but because a wall of back-and-forth text feels low-effort and unsophisticated. Direction (founder, verbatim intent):

> "Apart from direct text conversation, widgets and pictures should be the main form of communicating information." · "Focus on one topic at a time." · "Delete this 'Uni' thing — the name doesn't need to appear everywhere."

## Non-negotiable principles

1. **Widgets + pictures are the PRIMARY medium.** Text is connective tissue, not the whole experience. Every turn that *can* be a widget/card/picture should be.
2. **One topic per turn.** Never stack multiple widgets. The active question owns the view; answered turns **collapse into a tidy trail** (compact "✓ Interests · Building · Creating  [edit]" rows). Imprint-like focus.
3. **De-brand.** Remove the "Uni"/"U" monogram avatar and the per-message name label everywhere. The assistant stays **unnamed** in the UI. Audit other surfaces for redundant "Uni" / "Talk to Uni" name repetition.
4. **Mature, not gimmicky.** One widget per turn; always a **plain-text escape hatch + attach** (the paperclip already wired for material-ingest); widgets only when they genuinely beat typing — never decoration.

## Widget catalog (40 ideas, founder to pick the "yes" set)

**A · How you answer:** 1 Option cards · 2 Multi-select cards · 3 Importance slider · 4 Priority ranking (drag) · 5 This-or-that · 6 Range slider · 7 Two-axis "place yourself" pad · 8 Split-100-points · 9 Region chips · 10 Term picker

**B · What it reflects back:** 11 "What I'm hearing" summary (editable) · 12 Inline match card · 13 Mini comparison · 14 Insight stat · 15 Saved confirmation · 16 Next-step · 17 Upload · 18 Strategy snapshot

**C · Picture-forward:** 19 Photo-vibe picker · 20 Campus photo gallery · 21 Program hero w/ photo · 22 Day-in-the-life cards · 23 Map view w/ pins · 24 Visual comparison

**D · Data as pictures:** 25 Dual fit+confidence ring · 26 Admission odds bar · 27 "Where you land" range · 28 Net cost bar · 29 Timeline ribbon · 30 Discovery progress ring

**E · Interaction & guidance:** 32 Swipe triage · 33 Confidence meter · 34 Deadline picker · 37 Checklist card · 38 Coaching tip · 39 "Your type" reveal

**F · Simple (not mocked):** 31 Profile-strength bars · 35 Number stepper · 36 Toggle list · 40 Reaction check

### Cautions raised
- **#32 swipe triage** and **#39 "your type" reveal** risk reading as dating-app / BuzzFeed — the two most likely to tip back into "childish." Use with restraint or defer.
- **Picture-forward (19–24)** needs real, **credited** images. We already store `school_outcomes.campus_photos` (verified Wikimedia-style credits) → match/campus imagery (20, 21, 24) is real. **22 day-in-the-life** and **19 photo-vibe** need a sourced image library we don't have — defer or source first.

## Architecture context (so the build is grounded)

- Uni runs as a **managed agent on platform.claude.com** (flag `ai_uni_managed_agent_v1`, ON in prod). Host: `services/uni_agent_host.py` + `services/uni_tools.py`. The agent's `suggest_replies` host tool already stamps `{suggested_options, suggested_input{kind: choice|multi|scale}}` onto the assistant message's `extracted_signals`; `extracted_signals` also carries "noticed" items.
- Frontend renders this in `UniConversation.tsx` + `discover/AnswerChoices.tsx` (chips/multi/scale today) + `NoticedCard.tsx` + `FirstLookCard.tsx`. **The structured affordance channel already exists — extend it, don't invent a parallel one.**
- Reuse: `match/MatchCard`/`FirstLookCard`, `match/DualRing`, the `campus_photos` gallery, the material-ingest paperclip.

## Recommended build approach (founder leaned "frontend-first, then extend Uni")

1. **Frontend-first slice** — richen rendering of what Uni *already* emits: option cards (replace chips), real slider/multi-select widgets, "what I'm hearing" summary card, inline match card, a card-based de-branded welcome, AND the **one-topic-per-turn shell** (collapsed answered-trail, slim progress, back/skip/Continue, no name/avatar). Big visual lift, no agent change, graceful fallback.
2. **Extend the Uni agent contract** (fast-follow) — add richer `suggest_replies` kinds (e.g. `cards`, `ranking`, `range`, `region`, `term`, `program_picker`, plus content-card directives) in `agents/uni.agent.yaml` + `uni_tools.py` so Uni *intentionally* composes widgets per turn. Needs eval before trust.

## Process for the Uni session

Confirm the "yes" widget set with the founder (the 40-item index above), then: spec → plan → implement → verify (`tsc -p tsconfig.app.json` 0 · `vite build` 0 · `vitest` green · preview walkthrough) → ship to prod per the standing "ship every time" rule. Keep the `workshop_no_generation` / feedback-only invariants intact.
