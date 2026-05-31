# 57 · Realtime & Notifications

> Real-time delivery (SSE for notifications, WebSocket for messaging) + the notification service, multi-channel fan-out, notification center, and digest/batching. Delivers the `53` realtime bar on the `55` substrate.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Pairs with `17`/`29` (messaging), `21` (notification prefs/center), `19` (chat streaming), `56` (alerts), `60` §3B (change routing).

---

## 1. Transport choice

- **SSE** for one-way server→client streams: notification bell, feed "new posts", chat token streaming (`19`/`45` §25). Simple, proxy-friendly, auto-reconnect.
- **WebSocket** for bidirectional messaging (`17`/`29`): typing indicators, read receipts, instant delivery.
- One reconnecting client (`54` §6) with backoff; updates patch the TanStack cache, not full refetch.

## 2. Notification service

- Central `NotificationService`: an event (decision released, message received, deadline approaching, application missing-item, change_event `60`) → resolve recipients → write `notifications` row → fan out to channels.
- Idempotent (event id dedup); typed event catalog mapped to copy + deep-link (`05` §12).

## 3. Channels + delivery

- **In-app** (bell + center), **email** (SES), **push** (web push, later SMS/WhatsApp — Phase-2 `49`).
- Per-user, per-type, per-channel preferences (`21` §2.4); transactional/active-application events can be down-ranked but not fully silenced (safety).
- **Delivery reliability**: queue-backed (`55` §3), retry with backoff, DLQ + alert; record sent/delivered/opened.

## 4. Notification center (`21`)

- Bell with unread count (real-time), grouped by type/time, mark-one/all-read, deep-link to source, infinite scroll.
- Read-state syncs across devices/tabs.

## 5. Digest & batching

- High-frequency, low-urgency events (feed updates, non-urgent changes) → batched digest (daily/weekly per pref) instead of per-event spam.
- Urgent (decision, interview invite, applied-program deadline/policy change) → immediate.
- Materiality from `60` §3B gates urgent vs digest.

## 6. Acceptance

- [ ] SSE bell + WS messaging live; client reconnects; updates patch cache.
- [ ] NotificationService idempotent; event→recipient→row→channel fan-out.
- [ ] Per-type/channel prefs honored; transactional not fully silenceable.
- [ ] Center: real-time unread, grouped, mark-read syncs, deep-links.
- [ ] Digest batches low-urgency; urgent immediate; queue retries + DLQ.
- [ ] Notifications loop verified end-to-end (`52` §4).

## 7. Open questions

- WS infra on ECS (sticky sessions / Redis pub-sub) — recommend Redis pub/sub fan-out across tasks.
- Web push provider + VAPID setup — Phase-A in-app+email, push fast-follow.
