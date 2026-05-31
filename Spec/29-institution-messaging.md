# 29 · Institution Messaging & Inbox

> The institution side of the conversation. Where staff read and reply to applicant/prospect threads, send reason-coded messages, run templated + AI-drafted replies, and message segments in bulk. The mirror of the student inbox (`17-inbox.md`). Lives at `/i/communications?tab=inbox` (and direct `/i/messages`).
>
> Status: **draft v1.0** · 2026-05-29 · Closes the gap flagged in `05` §5.2 (`/i/messages` was mis-pointed at `17`) and `17` §14.

---

## 1. Purpose

Give admissions/recruitment/marketing staff one place to:
- Read and respond to threads with applicants and prospects (the other end of `17`).
- Send reason-coded outbound messages tied to an application/checklist item.
- Reply faster with templates (`/i/templates`, covered in `25`) and AI-drafted replies.
- Message a whole segment (`26`) at once for non-campaign operational comms (a campaign is marketing; this is operational/transactional).

Every institution message a student receives in `17` originates here.

---

## 2. Roles & assignment

- All `institution_admin` users see the shared inbox by default; threads can be **assigned** to a specific staff member.
- Filters: assigned to me / unassigned / all.
- Assignment is audit-logged (`36`). Reassignment notifies the new owner.
- Optional team routing rules: inquiries about a program route to that program's owner (Phase-2 nicety; MVP = manual assign).

---

## 3. Visual layout

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ [Wordmark]  Admissions · Outreach · Communications · Programs        [avatar]   │
├──────────────┬─────────────────────────────────────────────────────────────────┤
│ INBOX        │  THREAD · Sienna Park · CS MS · App #4821                        │
│ [Mine ▾]     │  ───────────────────────────────────────────────                │
│ [Unassigned] │  Sienna Park (applicant)                          2 days ago     │
│ [Reason ▾]   │  Hi — I submitted my second recommender's form but it still      │
│ [Program ▾]  │  shows as missing. Could you check?                              │
│              │                                                                  │
│ ● Sienna —   │  ↳ You (Maria, Admissions)                        replied        │
│   needs reply│  Looking into it now…                                            │
│ ● Diego —    │                                                                  │
│   doc req    │  ┌─ Context panel ──────────────────────────────┐               │
│ ○ Priya —    │  │ App #4821 · Stage: Review · Checklist 7/9    │               │
│   inquiry    │  │ Missing: Recommender 2, Mid-year transcript  │               │
│ ○ …          │  │ [Open applicant ↗]  [Open checklist ↗]       │               │
│              │  └──────────────────────────────────────────────┘               │
│              │  ─ Reply ─  [Template ▾] [✨ AI draft] [Attach] [Reason ▾]       │
│              │  [___________________________________________]  [Send]          │
└──────────────┴─────────────────────────────────────────────────────────────────┘
```

Three regions: thread list (left), conversation (center), **applicant context panel** (right rail or inline) that links to the review packet (`32`) and the checklist (`31`/`15`).

---

## 4. Thread types & reason codes

Threads mirror `17`'s action labels from the institution's vantage point. Every outbound message carries a **reason code** (the institution-side counterpart of the student's action label — this is what makes the student's inbox "reason-coded" per `06` §3):

| Reason code | Student sees (action label, `17` §5) |
|---|---|
| `request_document` | Document requested |
| `request_clarification` | Clarification required |
| `interview_invite` | Interview invite |
| `status_update` | Status update only |
| `general_reply` | Needs reply (if it asks a question) / informational |
| `decision_notice` | (decision flow, `34`) |

Reason code drives: how the student's `17` renders it, whether a due date is required, and whether it links a checklist item.

---

## 5. Composing a reply

- **Free text** with markdown.
- **Templates** — insert from `/i/templates` (`25`); variable substitution (`{{student_name}}`, `{{program}}`, `{{deadline}}`, `{{missing_items}}`).
- **AI draft** — `InboutboundReplyDrafter` proposes a reply grounded in the thread + applicant context (see §8). Staff edits before send; never auto-sends.
- **Attach** — request a specific document (creates/links a checklist item in the student's `15`), or attach a file (offer letter, instructions).
- **Reason code** — required on send.
- **Due date** — required when reason ∈ {request_document, request_clarification, interview_invite}; populates the student's thread due date and a Calendar nudge.

Sending writes to the student's `17` thread, fires their notification (Inbox + email per their prefs + push), and logs to `36`.

---

## 6. Bulk / segment messaging

Operational (non-campaign) bulk send:
- Select a **segment** (`26`) or an ad-hoc set from the Pipeline (`31`).
- Compose once (template + variables); preview per-recipient substitution.
- Reason code applies to all (commonly `status_update` or `request_document`).
- Throughput + suppression: respects each student's `consent.outreach` for marketing-class messages; **transactional/operational messages tied to an active application** (missing-item, interview, decision) are not suppressible by marketing consent but ARE governed by the student's notification prefs.
- Each recipient gets an individual thread (not a visible group thread).
- Bulk sends are audit-logged as a single batch action with per-recipient rows.

> Boundary with Campaigns (`25`): Campaigns = marketing outreach to prospects/audiences with attribution tracking. Messaging here = operational/transactional conversation tied to applications. They share templates + segments infrastructure but are distinct surfaces.

---

## 7. Data shape

```ts
type InstThread = {
  id: string;                       // same thread id space as student `17`
  application_id: string | null;    // null for pre-application inquiries
  student_ref: { id: string; name: string };
  program_ref: ProgramRef | null;
  assigned_to: string | null;       // staff user id
  reason_label: ReasonCode;
  status: 'open' | 'awaiting_student' | 'awaiting_us' | 'closed';
  due_date: ISO8601 | null;
  unread_count: number;
  last_message_at: ISO8601;
  context: {                        // denormalized for the right rail
    stage: string;
    checklist_complete: number;
    checklist_total: number;
    missing_items: string[];
  };
};
```

Endpoints:
- `GET /i/inbox/threads?filter=mine|unassigned|all&reason=…&program_id=…`.
- `GET /i/inbox/threads/:id`.
- `POST /i/inbox/threads/:id/messages` — `{body, attachments, reason_code, due_date?}`.
- `POST /i/inbox/threads/:id/assign` — `{staff_user_id}`.
- `POST /i/inbox/threads/:id/close`.
- `POST /i/inbox/threads/:id/ai-draft` — `InstitutionReplyDrafter`.
- `POST /i/inbox/bulk-message` — `{segment_id|application_ids, template_id, variables, reason_code}`.

---

## 8. AI integration

| Agent | Trigger | Output |
|---|---|---|
| `InstitutionReplyDrafter` (`45` — NEW) | "AI draft" in a thread | Reply grounded in thread + applicant context + checklist; reason-code aware |
| `CampaignAudienceCopySuggester` (`45` §16, reused) | Bulk compose | Drafts bulk message body |
| `InboundIntentClassifier` (`45` — NEW, optional) | New inbound message | Suggests a reason code + routing (which program owner) |

All fall back to manual compose on failure. AI drafts respect the applicant's `consent.matching` for using profile context; without it, the draft uses only the thread text. Every AI-assisted send is tagged in `36` (AI-assisted vs hand-written) for the audit ledger (`04` §8).

Add `InstitutionReplyDrafter` + `InboundIntentClassifier` to the `45` registry (Haiku-tier).

---

## 9. States

- **Empty:** "No conversations yet. Messages from applicants and prospects land here."
- **Unassigned queue:** badge count; "Assign to yourself to respond."
- **Awaiting student:** muted styling; SLA timer if institution tracks response SLAs.
- **Overdue (we owe a reply past SLA):** `--warning` row treatment + dashboard alert (`31` §2).
- **AI draft failure:** card hidden; staff types.

---

## 10. Brand compliance

- Reason-code chips per `02` §9, matching the student-side action-label colors so both ends speak the same visual language.
- Send button cobalt. **No gold** on the institution messaging surface (gold celebration belongs to the student receiving good news).
- Context panel uses `--surface` + `elev-subtle`; links cobalt.
- No decorative imagery — editorial, dense, operational.

---

## 11. Gaps (relative to current code)

- `/i/messages` route exists but points at a student-style inbox; this institution-specific surface is unimplemented (`05` §5.2; `47` G-I-Messaging).
- Threads share an id space + transport with student `17` — backend must serve both perspectives off the same `threads`/`messages` tables with role-scoped views.
- Reason codes are the institution-side write that produces the student's action labels — must be wired end-to-end.
- `InstitutionReplyDrafter` / `InboundIntentClassifier` agents NEW in `45`.
- SLA tracking is optional MVP; if shipped, surfaces on `31` dashboard.

---

## 12. Tests

- Outbound message with reason `request_document` + attach → creates student checklist item (`15`) + student `17` thread with "Document requested" label + due date on both ends.
- Assignment + reassignment audit-logged (`36`).
- Bulk message to a segment → one thread per recipient; marketing-consent suppression applies to marketing-class only, not to active-application transactional messages.
- AI draft renders, is editable, send tagged AI-assisted in `36`.
- Role scoping: student cannot read the institution context panel fields; institution cannot see student-private notes.

---

## 13. Copy

- "Messages from applicants and prospects land here." (empty)
- "Assign to yourself to respond."
- "AI draft" / "Insert template" / "Add reason".
- "Awaiting student" / "We owe a reply" / "Overdue".
- "Message 142 applicants" (bulk confirm) / "Preview per recipient".

---

## 14. Open questions

- **Shared vs per-user inboxes.** MVP = shared inbox with optional assignment. Per-user private inboxes are Phase-2.
- **SLA tracking.** Include response-SLA timers in MVP? Recommend optional, off by default; institutions that care turn it on.
- **Email round-tripping.** Students/staff who reply by email — ingest into the thread? Phase-2 (forwarding address per thread).
- **WhatsApp/SMS channel.** `49` defers multi-channel; this surface is in-app + email only for MVP.
- **Inbound intent auto-routing.** `InboundIntentClassifier` auto-assign is powerful but risks mis-routing; ship as a *suggestion* first.
