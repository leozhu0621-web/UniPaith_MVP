# Phase 2.1 Conversation Engine API Contracts

## Goal

Provide implementation-ready API contracts for the student conversation engine so backend and frontend teams can work in parallel with deterministic payloads and gating logic.

## Current Surface Analysis (Insertion Points)

### Backend

- Existing student assistant entrypoint: `POST /students/me/assistant/chat` in `unipaith-backend/src/unipaith/api/students.py`.
- Existing conversational persistence primitives: `Conversation` + `Message` via `unipaith-backend/src/unipaith/api/messaging.py`.
- Existing student profile and preference structures suitable for requirement seeding in `unipaith-backend/src/unipaith/schemas/student.py`.
- No dedicated contract set yet for requirement inference, confidence reporting, or shortlist unlock.

### Frontend

- Current chat payload is minimal (`StudentAssistantChatRequest/Response` concept only: message -> reply).
- No normalized interfaces for:
  - requirement lifecycle (draft/confirmed/rejected)
  - per-domain confidence
  - conflict objects and resolution options
  - shortlist unlock gate report

## Contract Groups

- `conversation_turn`
- `requirements`
- `confidence_report`
- `shortlist_unlock`
- `session_resume`

## Endpoint Contract Draft

All endpoints are proposed under student scope:

- `POST /students/me/conversation/turn`
- `GET /students/me/conversation/session`
- `GET /students/me/conversation/requirements`
- `PATCH /students/me/conversation/requirements/{requirement_id}`
- `GET /students/me/conversation/confidence`
- `GET /students/me/conversation/shortlist-unlock`
- `POST /students/me/conversation/conflicts/{conflict_id}/resolve`

## 1) conversation_turn

### Request

```json
{
  "session_id": "uuid-or-null",
  "message": "string",
  "entrypoint": "chat|discover_shortcut|resume",
  "context_program_id": "uuid-or-null",
  "client_event_id": "string-or-null"
}
```

### Response

```json
{
  "session": {
    "session_id": "uuid",
    "student_id": "uuid",
    "current_stage": "understand_context|identify_issues|define_demand|translate_requirements|ready_for_shortlist",
    "active_domain": "academic_readiness|budget_finance|country_location|timeline_intake|career_outcome|eligibility_compliance|learning_preferences",
    "turn_count": 12,
    "last_updated_at": "2026-04-01T10:00:00Z"
  },
  "assistant_message": {
    "message_id": "uuid",
    "reply_text": "string",
    "why_asked": "string-or-null",
    "suggested_next_actions": ["confirm_requirements", "add_budget_range"]
  },
  "state_delta": {
    "updated_domains": ["budget_finance"],
    "new_requirements_count": 2,
    "new_conflicts_count": 0
  },
  "confidence_summary": {
    "global_confidence": 71,
    "global_level": "recommendation_ready"
  }
}
```

## 2) requirements

### GET response

```json
{
  "requirements": [
    {
      "requirement_id": "uuid",
      "domain": "budget_finance",
      "field": "max_annual_tuition",
      "value": 35000,
      "priority": "must_have|should_have|optional",
      "source": "student_explicit|inferred|imported",
      "confidence": 82,
      "status": "draft|confirmed|rejected",
      "evidence_turn_ids": ["uuid"],
      "updated_at": "2026-04-01T10:00:00Z"
    }
  ]
}
```

### PATCH request

```json
{
  "status": "confirmed|rejected|draft",
  "value": "any-json",
  "priority": "must_have|should_have|optional"
}
```

### PATCH response

Returns updated requirement object.

## 3) confidence_report

### Response

```json
{
  "global_confidence": 74,
  "global_level": "recommendation_ready",
  "domain_scores": [
    {
      "domain": "budget_finance",
      "status": "sufficient",
      "confidence": 79,
      "missing_fields": [],
      "conflicts": []
    }
  ],
  "blocking_issues": [],
  "computed_at": "2026-04-01T10:00:00Z"
}
```

## 4) shortlist_unlock

### Response

```json
{
  "eligible": true,
  "reasons": ["global_confidence_passed", "domain_minimums_passed"],
  "thresholds": {
    "global_min": 70,
    "domain_min": 65
  },
  "blocking_conflicts": [],
  "missing_required_fields": [],
  "recommended_next_actions": []
}
```

## 5) session_resume

### Response

```json
{
  "session": {
    "session_id": "uuid",
    "current_stage": "translate_requirements",
    "active_domain": "eligibility_compliance",
    "turn_count": 24
  },
  "checkpoint_summary": "string",
  "open_tasks": ["confirm_language_requirement", "set_budget_cap"],
  "last_assistant_prompt": "string-or-null"
}
```

## Error Model (All Endpoints)

```json
{
  "error": {
    "code": "validation_error|not_found|forbidden|conflict_unresolved|insufficient_confidence|rate_limited",
    "message": "Human readable",
    "details": {
      "field": "optional",
      "reason": "optional"
    }
  }
}
```

## Backend Integration Mapping

### Proposed Router

- New file: `unipaith-backend/src/unipaith/api/conversation.py`
- Prefix: `/students/me/conversation`
- Tag: `conversation`

### Proposed Schemas

- New file: `unipaith-backend/src/unipaith/schemas/conversation.py`
- Contains request/response DTOs for all 5 groups.

### Proposed Service Boundary

- New service: `unipaith-backend/src/unipaith/services/conversation_service.py`
- Responsibilities:
  - parse turn input
  - update session state
  - upsert requirements
  - compute confidence
  - evaluate shortlist unlock
  - expose resume checkpoint

### Existing Module Touchpoints

- `services/student_service.py`: profile/prefs bootstrap context.
- `services/matching_service.py`: shortlist readiness and rationale integration.
- `api/students.py`: keep `/assistant/chat` for backward compatibility during migration.

## Frontend Integration Mapping

### Type Contracts

Add conversation-specific types (new section in `frontend/src/types/index.ts`):
- `ConversationSession`
- `ConversationTurnRequest/Response`
- `ConversationRequirement`
- `ConfidenceReport`
- `ShortlistUnlockReport`
- `ConversationConflict`
- `ResumeCheckpoint`

### API Client Surfaces

Proposed new API module:
- `frontend/src/api/conversation.ts`

Functions:
- `sendConversationTurn()`
- `getConversationSession()`
- `listConversationRequirements()`
- `updateConversationRequirement()`
- `getConfidenceReport()`
- `getShortlistUnlockReport()`
- `resolveConversationConflict()`

### UI Consumption Paths

- `ChatPage`: `conversation_turn` + assistant reply + next actions.
- `MyPlan`: requirements, blockers, confidence meter.
- `DiscoverPage`: shortcut entry + unlock warnings.
- `ApplicationsPage`: enforce unresolved-conflict and missing-required gating.

## Gating and Validation Rules

### Unlock Rules

- `global_confidence >= 70`
- `budget_finance`, `timeline_intake`, `eligibility_compliance` each `>= 65`
- `blocking_conflicts` must be empty
- required fields for current stage must be complete

### Hard Blockers

- unresolved contradiction in must-have constraints
- missing eligibility minimums for selected destination/program class
- deadline infeasibility with no accepted fallback option

### QA Scenarios

- low confidence path remains conversational and non-crashing
- shortcut path unlocks provisional shortlist with warnings
- conflict resolution updates confidence and unlock report deterministically
- session resume restores stage/domain/open tasks correctly
- requirement edits invalidate stale shortlist unlock cache

## Incremental Rollout Plan

1. **Read-only foundation**
- implement `GET session`, `GET requirements`, `GET confidence`, `GET shortlist-unlock` with mocked/calculated outputs

2. **Write path activation**
- implement `POST turn`, `PATCH requirement`, `POST conflict resolve`

3. **Frontend opt-in**
- wire `ChatPage` + `MyPlan` to new contracts behind feature flag

4. **Migration bridge**
- keep `/students/me/assistant/chat` active; route internally to new service where possible

5. **Cutover**
- switch primary chat UX to conversation API
- deprecate legacy chat endpoint after stability window

## Acceptance Checklist

- Every endpoint has explicit request/response + error schema.
- Payload fields are deterministic and machine-consumable.
- Gating outcomes are explainable and testable.
- Frontend contracts map 1:1 to backend DTOs.
- Guided and shortcut paths are both supported.

