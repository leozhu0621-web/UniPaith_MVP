# Student Hybrid IA and Navigation Spec

## Goal

Reduce cognitive load while preserving all existing student features by restructuring navigation around admission journey phases.

## Navigation Model

## Primary Journeys

1. **Plan**
- Dashboard (`/s/dashboard`)
- Profile (`/s/profile`)
- Chat (`/s/chat`)

2. **Discover**
- Discover (`/s/discover`)
- Saved (`/s/saved`)
- Recommendations (`/s/recommendations`)

3. **Apply**
- Applications (`/s/applications`)
- Calendar (`/s/calendar`)
- Deadlines (`/s/deadlines`)

## Utility

- Messages (`/s/messages`)
- Financial Aid (`/s/financial-aid`)
- Settings (`/s/settings`)

## IA Rules

- Keep all routes intact for backward compatibility.
- Show nav items grouped with labels to reinforce student mental model.
- Keep one persistent global “Next best action” signal in shell.
- Route logo/home action to dashboard (not chat) for orientation consistency.

## Global Shell Additions

- **CalmActionRail** (top-level summary):
  - primary next action,
  - blocking count,
  - nearest deadline confidence.
- **Supportive progress cue**:
  - “Profile support progress” wording instead of scorecard framing.

## Existing Route Mapping (No Feature Removal)

| Existing Route | Journey Bucket |
|---|---|
| `/s/dashboard` | Plan |
| `/s/profile` | Plan |
| `/s/chat` | Plan |
| `/s/discover` | Discover |
| `/s/saved` | Discover |
| `/s/recommendations` | Discover |
| `/s/applications` | Apply |
| `/s/applications/:appId` | Apply |
| `/s/calendar` | Apply |
| `/s/deadlines` | Apply |
| `/s/messages` | Utility |
| `/s/messages/:convId` | Utility |
| `/s/financial-aid` | Utility |
| `/s/settings` | Utility |

## Success Criteria

- Students can locate core tasks in <= 2 navigation decisions.
- Students report clearer “where I am in process” understanding.
- Fewer jumps between unrelated pages during task completion.
