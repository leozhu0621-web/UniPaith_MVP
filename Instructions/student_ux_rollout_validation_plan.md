# Student UX Rollout and Validation Plan

## Rollout Strategy

## Phase 1: Shell + Messaging Tone
- Apply IA grouping and supportive copy in layout and dashboard.
- Add non-disruptive feature flags for student shell redesign.

## Phase 2: High-Stress Surfaces
- Roll out deadlines and application detail emotional reframing.
- Add clearer status language and supportive urgency labels.

## Phase 3: Counselor Chat Layer
- Ship chat tone + error resilience improvements.
- Align quick actions with counselor coaching language.

## Phase 4: LLM Trust Expansion
- Enforce explanation and confidence disclosure patterns in assistant responses.
- Validate consistency across dashboard prompts and chat.

## Instrumentation

Track:
- `student_next_action_clicked`
- `student_deadline_focus_opened`
- `student_submit_readiness_checked`
- `student_chat_supportive_prompt_used`
- `student_chat_send_failed`
- `student_recommendation_explain_opened`

## Success Metrics

Primary:
- Drop in abandonment at profile completion and pre-submit stages.
- Improved completion rate for draft applications.
- Reduced retry/error loops in student chat and recommendations.

Perception (qualitative):
- “I know what to do next.”
- “The experience feels calm and trustworthy.”
- “The AI feels like a counselor, not a bot.”

## Experiment Design

- A/B test old vs redesigned emotional framing on:
  - dashboard,
  - deadlines,
  - application detail.
- Compare:
  - completion funnels,
  - time-to-next-action,
  - support-trigger events.

## Exit Criteria

- Statistically meaningful improvement in next-action completion.
- No regression in core conversion (application submit rates).
- Positive qualitative sentiment from student interviews.
