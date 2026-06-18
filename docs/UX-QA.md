# UX-QA — voice & interaction

> The standard for everything a UniPaith user reads or does. Two halves: **how the words sound** (the voice) and **whether something is text when it should be a control or a visual** (show, don't tell). Enforced by `frontend/scripts/voice-lint.mjs` (CI) for the objective parts; the rest is human judgment against this guide.
>
> Reference: **Handshake** — warm, professional, action-oriented. Brand voice: editorial, restrained, earned (`Spec/01-brand-tokens.md`). Writing discipline: Strunk, *omit needless words*.

---

## Part 1 · Voice

### The six rules

1. **Name the thing, don't address the user.** Titles and labels are plain nouns — *Profile, Applications, Saved, Offers, Settings* — never *Your record / Your portfolio / Your shortlist*. (Possessive is fine *inside a sentence*: "personalize **your** matches" — just not as a standalone label.)
2. **Celebrate real milestones plainly.** Earned warmth stays — a greeting by name, *"You're in!"*, *"You're enrolled!"*. No emoji, no manufactured cheer on mundane chrome. The gold beat is the celebration; the words stay grounded.
3. **The UI is self-evident — don't explain it.** Default to **no helper line at all.** A title, its controls, and its data stand alone. **Delete** section descriptions, "what this does" sub-text under a title, the empty-state pitch, and the status explanation. Keep only a hard functional constraint (a file limit, a required marker) — never a description.
   - Section: *"WHO YOU ARE — Add a few values and beliefs below, or talk it through with Uni, and we'll synthesize a short portrait of who you are."* → **"WHO YOU ARE"** (+ the controls; no description)
   - Title sub: *"Import from a file — Upload a resume, transcript, or CV; Uni reads it and fills your profile…"* → **"Import from a file"** (the upload control says the rest)
   - Empty state: *"Nothing yet — add a value, or let Uni surface it from your chats."* → **"Nothing yet"** (a bare state label, not a sentence)
   - Status: *"1 program saved. Reach / target / safer reflects each application's fitness band."* → **"1 program saved"** (drop the explanation)
   - When a line genuinely survives (rare), hold it to a news standard: lead with the point, one tight sentence, active voice, no filler, no passive explanation where an action belongs. *"Nothing urgent right now. A good moment to get ahead."* → **"Nothing urgent right now."** · *"Match scores improve once we know your grades"* → **"Add your grades to sharpen your matches."**
4. **Talk like a counselor, not a chatbot.** No AI-speak: *dive in, delve, unlock your potential, empower, seamless, supercharge, "I'd be happy to", "Great question."* Direct and honest — "fit, not fame."
5. **Never blame; be courteous.** Keep the gesture words — *"Please try again,"* not a clipped *"Try again."* Every error and empty state ends with a way forward. (See `lib/copy.ts`.)
6. **Clarity beats brevity when an action is involved.** An action item names the real action, spells out the object, and shows the deadline when that's the urgency — *"Respond to Carthage's offer · Due Jun 24,"* never *"Respond to your offer — HCI MS."*

### Keep / Trim / Cut (the warmth line)

| | Examples |
|---|---|
| **Keep** — earned, human | "Good afternoon, Juncheng" · "You're in!" · "You're enrolled!" |
| **Trim** — keep the moment, cut the tail | "You're in! Let's get you ready. 🎓" → "You're in!" · "…two minutes, a handful of taps" → (cut) |
| **Cut** — noise, not warmth | "Let's dive in and unlock your full potential!" → "Start with your goals." · "Four views of your world" → "Discover tabs" · "Let's go" → "Get started" |

### Reference strings

- **Labels:** Discover · Applications · Saved · Messages · Profile · Settings
- **Buttons (action verbs):** Get started · Save · Apply · Message · Continue
- **Empty state:** "No saved programs yet. Save one from Discover to compare and apply."
- **Error:** "We couldn't load this. Please try again."

### Banned (the linter fails the build on these)

AI-speak: *dive in · delve · seamless · supercharge · "I'd be happy to" · "Great question" · "at the end of the day" · "needless to say" · game-changer · cutting-edge · best-in-class · unleash · revolutionize · "elevate your" · "unlock your potential" · empower.*
Wordy clichés: *in order to · due to the fact that · at this point in time · in the event that · for the purpose of · with regard(s) to.*
Emoji in product copy is a **warning** (let the words carry it), not a hard fail — because warmth is judgment, not a rule.

---

## Part 2 · Show, don't tell

**"Show and act, not read and figure out."** Wherever the app renders an *action, decision, status, number, input, or comparison* as a sentence, it makes the user parse before they can act. Replace prose with the smallest control or visual that carries the same meaning.

### The ownership rule (the guardrail)

- **Owned action** — we have a verified endpoint that performs it → render a **control** (button / chip / toggle / select). e.g. Save, Compare, RSVP, Start application, Pay fee, Nudge recommender, Set reminder, Edit a preference, mark read.
- **Inform-only** — the *school* owns the outcome (admission decisions; accepting/declining an offer happens on their portal) → **inform + view**: show the data, link to the right place, **never a fake Accept/Decline we can't honor.** (Enrollment confirm/decline/defer *are* ours, so those stay controls.)
- **Pure data** — a number, status, or percent → render a **visual** (ring, bar, badge, stat tile, stepper, timeline). Display only.

Litmus test before adding a control: *does our backend have a verified endpoint that performs this exact thing?* If no → it's inform-only or pure-visual.

### The component kit (reuse before building)

`AnswerChoices` (chips / multi-select / 1–5 scale) · `StatTile` · `DualRing` · `ProgressRing` / `ProgressBar` · `Badge` · `MatchCard` / `FundingPackageCard` · `Select` · a horizontal `Stepper` · a `StatBar` magnitude/heat util · a `TokenInput`.

### What NOT to do

- Don't widgetize dense **professional tables** that are correctly tables (cohort comparison, interview queues, prospect lists). A table is the right tool for scannable rows.
- Don't invent actions the product doesn't own. Inform-only surfaces never grow fake buttons.
- Don't turn warmth into chrome — a greeting is a sentence, not a widget.

---

## Part 3 · Enforcement

- **`npm run voice-lint`** runs in CI (`pr-checks.yml`, frontend job) and fails on the banned phrases above. It scans user-facing strings only and never polices warmth.
- **Centralize reusable strings** in `frontend/src/lib/copy.ts` so the app speaks with one voice.
- When you add or change copy, read this file. When you add a surface that's an action/decision/status/number, ask the ownership question before you write a sentence.
