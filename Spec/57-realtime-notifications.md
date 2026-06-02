# 57 · Realtime & Notifications — Build Spec

> Buildable spec for real-time delivery (SSE notifications, WebSocket messaging) + the notification service, multi-channel fan-out, notification center, and digest/batching. Grounded in the real `services/notification_service.py`, the `notifications`/`notification_preferences` tables (`51`), FE `api/notifications.ts`, and the `lib/realtime.ts` client `54` §9 commits to building. Companion to `17`/`29` (messaging), `21` (prefs/center), `19` (chat streaming), `56` (alerts), `60` §3B (change routing), `55` (queue substrate).
>
> Status: **draft v2.0** · 2026-05-30 · v2 converts standards → build tasks against real modules.

---

## 1. What exists vs what to build

| Piece | Real today | Status |
|---|---|---|
| Notification model | `notifications` + `notification_preferences` tables (`51`, `models/workflow.py`) | exists |
| Notification service | `services/notification_service.py` | exists — extend to fan-out + idempotency |
| Event hooks | `services/event_hooks.py` | exists — the emit points |
| FE notifications API | `api/notifications.ts` | exists |
| SSE endpoint | — | **NEW (build)** |
| WebSocket messaging | — | **NEW (build)** |
| FE realtime client | `lib/realtime.ts` (`54` §9) | **NEW (build)** |
| Email channel | `services/campaign_email_service.py` (SES) | exists — reuse for transactional |
| Digest/batching | — | **NEW (build)** |

---

## 2. Transport (build)

- **SSE** for one-way server→client: notification bell, feed "new posts", chat token streaming (`19`, `45` §25). Proxy-friendly, auto-reconnect. Build endpoint `GET /api/v1/me/stream` (auth via bearer; `@microsoft/fetch-event-source` on FE for the header). Emits typed events `{type, payload}`.
- **WebSocket** for bidirectional messaging (`17`/`29`): typing indicators, read receipts, instant delivery. Endpoint `WS /api/v1/ws/messages`.
- **FE:** one reconnecting client in `lib/realtime.ts` (`54` §9) with exponential backoff; on event → **patch the TanStack cache** (`qc.setQueryData`), never full refetch. Consumed via `useRealtime()`.
- **Infra (ECS):** WS + SSE across multiple tasks need **Redis pub/sub fan-out** (`55` §3 Redis) so an event on task A reaches a client connected to task B. Build `core/realtime.py` (pub/sub bridge).

---

## 3. Notification service (extend `services/notification_service.py`)

- Central flow: an event (decision released `34`, message received `17`/`29`, deadline approaching `16`, application missing-item `15`, `change_event` `60`, saved-search hit `56`) → `event_hooks.py` calls `NotificationService.emit(event)` → resolve recipients → write `notifications` row → fan out to channels (§4) → publish to Redis pub/sub (§2) for live delivery.
- **Idempotent:** dedup on `event_id` (a notification is written once even if the hook fires twice) — build an `event_id` unique key.
- **Typed event catalog:** one registry mapping `event_type` → copy template + deep-link (`05` §12) + default urgency (urgent|digest). Build `services/notification_catalog.py`.

---

## 4. Channels + delivery

- **In-app** (bell + center, `21`) — the `notifications` row + live SSE push.
- **Email** (SES) — reuse `campaign_email_service.py` transport for transactional notifications (distinct from marketing campaigns `25`); templated per the catalog.
- **Push** (web push w/ VAPID) — Phase-A in-app+email, push fast-follow; SMS/WhatsApp Phase-2 (`49`).
- **Preferences** (`21` §2.4, `notification_preferences` table): per-user × per-type × per-channel. Transactional/active-application events (decision, interview, applied-program deadline) can be **down-ranked but not fully silenced** (safety) — enforce in `NotificationService` (a `silenceable: bool` on the catalog entry).
- **Delivery reliability:** channel sends run as `55` §4 queue jobs with retry/backoff + **DLQ + alert**; record `sent/delivered/opened` on the row (or a `notification_deliveries` table if per-channel tracking is needed).

---

## 5. Notification center (`21`, FE)

- Bell with **real-time unread count** (SSE); panel groups by type/time; mark-one / mark-all-read; deep-link to source; infinite scroll (cursor, `50` §5).
- Read-state syncs across devices/tabs (mark-read publishes via Redis → other sessions patch cache).
- FE: `api/notifications.ts` (`list`, `markRead`, `markAllRead`, `preferences`) + `useRealtime()` subscription patching `qk.notifications()`.

---

## 6. Digest & batching (build)

- High-frequency, low-urgency events (feed updates, non-urgent `change_events`, saved-search hits) → **batched digest** (daily/weekly per pref) instead of per-event spam. Build a digest job (`core/scheduler.py`) that aggregates pending `digest`-class notifications per user and sends one email.
- Urgent (decision, interview invite, applied-program deadline/policy change) → immediate.
- **Materiality** from `60` §3B gates urgent vs digest; saved-search caps from `56` §6 apply.

---

## 7. Build tasks (checklist)

- [ ] `GET /me/stream` SSE endpoint (typed events) + `WS /ws/messages`.
- [ ] `core/realtime.py` Redis pub/sub fan-out across ECS tasks.
- [ ] `lib/realtime.ts` + `useRealtime()` (FE; `54` §9) — patch cache on event.
- [ ] Extend `notification_service.py`: idempotent emit, recipient resolution, channel fan-out.
- [ ] `services/notification_catalog.py` (event_type → copy/deep-link/urgency/silenceable).
- [ ] Transactional email via `campaign_email_service` (SES); web-push fast-follow.
- [ ] Digest job (`core/scheduler.py`) batching digest-class; urgent immediate.
- [ ] Notification center FE wired to SSE; cross-tab read-state sync.
- [ ] Delivery jobs queue-backed with retry + DLQ + alert.

---

## 8. Acceptance

- [ ] SSE bell + feed pill live; WS messaging (typing/read/delivery) live; client reconnects; updates patch cache (no refetch).
- [ ] `NotificationService` idempotent; event→recipient→row→channel fan-out across tasks (Redis pub/sub).
- [ ] Per-type/channel prefs honored; transactional not fully silenceable.
- [ ] Center: real-time unread, grouped, mark-read syncs across tabs, deep-links.
- [ ] Digest batches low-urgency; urgent immediate; queue retries + DLQ.
- [ ] End-to-end notification loop verified (`52` §4): institution action → student notification row + live UI.

---

## 9. Open questions

- SSE vs WS for the bell — SSE (one-way) is enough; reserve WS for messaging only.
- Web-push provider + VAPID key management (Secrets Manager) — Phase-A in-app+email.
- `notification_deliveries` table vs columns on `notifications` — add the table only if per-channel open-tracking is needed.
