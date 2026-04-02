# Student Emotional Design System (Admission Experience)

## Objective

Deliver an anti-stress admission experience where:
- the **platform feels confident** (clear, structured, dependable),
- the **LLM feels warm and reassuring** (empathetic, practical, personal),
- students always know what to do next without feeling judged.

## Emotional Principles

1. **Steady confidence over urgency panic**
- Replace alarm-heavy framing with calm, action-oriented wording.
- Use urgency only to clarify action windows, not to trigger fear.

2. **Guided progress over performance pressure**
- Show completion as support, not as a grade.
- Explain what each missing item unlocks.

3. **Trust through transparency**
- Every recommendation: why shown, confidence level, what can improve.
- Every AI inference is editable.

4. **Personal care over generic flow**
- Use student context in prompts and summaries.
- Keep counselor tone consistent across dashboard, chat, applications.

5. **Recovery-friendly interaction**
- If blocked, show one fallback path and one human-readable next step.
- Never leave blank states without concrete action.

## Tone Matrix by Journey Stage

| Stage | Platform Voice | LLM Voice | Avoid |
|---|---|---|---|
| Explore | Confident orientation | Warm curiosity | Ranking pressure language |
| Prepare | Structured checklist | Gentle coaching | Shame framing (“incomplete”) |
| Submit | Calm confirmation | Reassuring validation | High-stakes panic copy |
| Waiting | Predictable updates | Emotional regulation + practical prep | Alarm banners |
| Decide | Clear comparison | Supportive tradeoff reasoning | Overconfident certainty |

## Copy Rules

### Platform (Confident)
- Use: “Next best action”, “You are on track”, “Recommended this week”.
- Use short, declarative guidance.
- Keep numerical signals secondary to action signals.

### LLM (Warm + Reassuring)
- Start with acknowledgment, then actionable advice.
- Include a confidence statement and one improvement step.
- Use collaborative framing (“We can…”).

## Urgency Model

### Levels
- **Gentle attention** (30+ days): planning language.
- **Priority window** (8-30 days): sequencing language.
- **Focus now** (0-7 days): action-now language without alarm wording.

### Visual Rules
- Reduce red usage to true blockers.
- Prefer neutral/blue/amber for timeline visibility.
- Attach urgency labels to suggested actions.

## Reassurance Patterns

- **Micro-confirmations:** “Saved”, “You are still on track”, “This update improved your fit.”
- **Next-step anchors:** one primary action + optional secondary action.
- **Uncertainty normalization:** explain unknowns and how to resolve them.
- **Decision support:** summarize tradeoffs with student priorities.

## Trust Patterns

- “Why this appears” modules on recommendation and shortlist surfaces.
- Confidence meter with plain language explanations.
- Editable assumptions panel for inferred requirements.

## Anti-Overwhelm Patterns

- Progressive disclosure (default collapsed details).
- Task chunking by journey phase.
- Keep primary navigation focused on current phase with clear fallback paths.

## Emotion Quality Checklist

- Student can answer in <5 seconds:
  - What matters now?
  - What is next?
  - What can wait?
- No panic color treatment unless true blocking condition.
- Every high-friction action includes reassurance and recovery option.
