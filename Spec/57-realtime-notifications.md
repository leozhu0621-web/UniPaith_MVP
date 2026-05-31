# 57 · Realtime & Notifications

> The live nervous system that makes UniPaith feel as responsive as LinkedIn (notification bell, instant messaging) — realtime transport, the notification service + fan-out, multi-channel delivery, and the in-app notification center. Feature docs `17`/`21`/`29` own the surfaces; `55` owns the queue/Redis substrate; this owns how events become live UI + delivered messages.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Builds on `21` (notification prefs), `17`/`29` (messaging), `55` (queue/Redis/jobs), `54` §7 (realtime client).

---

## 1. Transport: SSE for notifications, WebSocket for messaging

Use the right tool per the comparison ([SSE vs WS](https://oneuptime.com/blog/post/2026-01-27-sse-vs-websockets/view), [why SSE for most](https://medium.com/codetodeploy/why-server-sent-events-beat-websockets-for-95-of-real-time-cloud-applications-830eff5a1d7c)):

| Need | Transport | Why |
|---|---|---|
| **Notifications + live match/status updates** (server→client, low frequency) | **SSE** | One HTTP stream, native `EventSource` auto-reconnect, no handshake — simpler, cheaper. The 95% case. |
| **Messaging** (`17`/`29` — bidirectional, typing, read receipts) | **WebSocket** | True duplex; justified by frequent two-way traffic. |
| **Mobile/background push** | **Web Push / FCM/APNs** | When the tab is closed (PWA, `03` §8). |

- The frontend client (`54` §7) abstracts both behind one `lib/realtime.ts`; on event → `setQueryData` so UI updates without refetch.
- **Pub/sub backbone**: Redis Pub/Sub (or NATS) so any ECS task can push to any connected client — required once there's > 1 backend task ([scaling](https://websocket.org/guides/use-cases/notifications/)).
- Graceful: connection drop → backoff reconnect; fall back to polling `/notifications` if realtime is unavailable (never block the app).

---

## 2. Notification service architecture (fan-out)

Standard scalable pattern ([notification architecture](https://codelit.io/blog/notification-system-architecture), [design](https://medium.com/@EshitaKhakharia/de-sign-notification-service-5cf6fac14d98)):

```
Domain event (decision released, new message, match updated,
              saved-search hit, deadline closing, RSVP confirmed)
   │  emit to event bus / queue (55 §3)
   ▼
Fan-out workers
   • resolve recipients
   • load preferences (21 — per-type × per-channel)
   • respect consent (46)
   • write to notification store (notifications table, 51)
   • enqueue per-channel delivery jobs
   ▼
Channel dispatchers (one worker per channel, with retries + DLQ)
   • in-app  → SSE push + notification center
   • email   → SES (templated)
   • push    → Web Push / FCM/APNs
   • SMS     → (opt-in, deferred)
```

- Events come from across the app: institution actions (`34` decision, `29` message), system (`56` saved-search hit, deadline alert), social (`20` RSVP, follow).
- The fan-out + dispatch run on the task queue (`55` §3) — idempotent, retryable, observable.

---

## 3. Channels & preferences (tie to `21`)

- Channels: **in-app, email, push, SMS** (SMS opt-in/deferred). Matrix per `21` §2.4: per-type × per-channel toggles + email frequency (all/digest/important/none).
- **Transactional vs marketing**: active-application/decision/interview notifications are transactional — governed by prefs but not suppressible by marketing-consent; campaign/marketing respects `consent.outreach` (`29` §6, `46`).
- **Quiet hours / timezone**: schedule non-urgent sends in the user's daytime (`21` locale/timezone).

---

## 4. Notification center (LinkedIn bell parity)

The in-app surface (`21` + a global bell):
- **Bell with unread count** in the top bar on every authenticated page; real-time increment via SSE.
- **Grouped/categorized** center: by type (applications, messages, matches, events, system) and time (today/this week).
- Each item: icon, actor/source, summary, relative time, read/unread, **deep-link to source** (`05` §8 cross-page nav).
- **Mark-all-read**, mark-one-read (auto on click), per-type filter.
- **Grouping/collapsing**: "3 programs match your saved search" not 3 rows (LinkedIn-style aggregation).
- Read state synced server-side so it's consistent across devices.

---

## 5. Digest & batching (anti-noise)

A retention feature becomes a churn feature if it spams:
- **Batch** low-urgency notifications into daily/weekly digests per `21` frequency.
- **Coalesce** duplicates (one "deadline soon" per program, not per scan).
- **Global cap** per user per day (`56` §9) — overflow → digest.
- Urgent (decision released, interview invite, new direct message) bypass batching → immediate.
- Smart timing: send digests at high-open windows.

---

## 6. Delivery reliability

- **Idempotent delivery**: each notification has a stable id; dispatch keyed so a retry never double-sends (`55` §5).
- **Retry + DLQ** per channel (`55` §3); a failed email retries with backoff, then DLQ + alert.
- **Delivery tracking**: store sent/delivered/opened/clicked per notification (powers `28` attribution + engagement signals `44` §8).
- **SES specifics**: verified sender domain, bounce/complaint handling (suppress hard-bounces), DKIM/SPF/DMARC (`58`).

---

## 7. Realtime UX hooks (what the user feels — `53`)

- **Messaging** (`17`/`29`): optimistic send, delivered/read receipts, typing indicator, unread badges, new-message toast + bell.
- **Live match updates**: when a profile edit recomputes matches (`45` §12), the Match page updates via SSE with a subtle "scores updated" pill — not a forced refresh.
- **Live pipeline** (institution `31`): new application appears in the queue in real time.
- **Presence** (optional): online dot in messaging.
- All updates land in the TanStack Query cache (`54` §7) so they're consistent with the rest of the UI.

---

## 8. Scale notes

- < 10k concurrent: SSE + WS on the app tasks with Redis pub/sub is fine ([scale](https://oneuptime.com/blog/post/2026-01-27-sse-vs-websockets/view)).
- Beyond: dedicated realtime tier (or a managed service — Pusher/Ably/Knock) so connection load doesn't compete with API serving.
- Connection limits per task; horizontal scale behind a sticky-or-pubsub setup.

---

## 9. Acceptance (extends `52` §4 notifications-loop gate)

- [ ] SSE delivers an in-app notification within ~1s of the domain event.
- [ ] WebSocket messaging: send→deliver→read receipt round-trips live across two sessions.
- [ ] Preferences honored: a disabled channel/type is not delivered; consent respected.
- [ ] Digest batches low-urgency; urgent bypasses; global cap enforced.
- [ ] Idempotent: replaying an event doesn't double-notify.
- [ ] Notification center: unread count accurate, deep-links work, mark-all-read syncs across devices.
- [ ] Graceful fallback to polling when realtime is down.

---

## 10. Open questions

- **Build vs buy realtime** — self-host SSE/WS + Redis pub/sub, or adopt a notifications platform (Knock/Courier for fan-out + prefs, Ably/Pusher for transport)? Buy accelerates parity; self-host controls cost. Recommend evaluate Knock for fan-out + self-host SSE.
- **Web Push scope** — ship with the PWA (`03` §8) or fast-follow? Recommend fast-follow after in-app + email.
- **Read-state model** — per-notification vs last-read-cursor; cursor is cheaper at scale.
- **Presence/typing cost** — nice but chatty; gate behind messaging v2 if connection cost is a concern.

Sources: [SSE vs WebSockets](https://oneuptime.com/blog/post/2026-01-27-sse-vs-websockets/view) · [why SSE for most realtime](https://medium.com/codetodeploy/why-server-sent-events-beat-websockets-for-95-of-real-time-cloud-applications-830eff5a1d7c) · [notification system architecture](https://codelit.io/blog/notification-system-architecture) · [WebSocket notifications/scaling](https://websocket.org/guides/use-cases/notifications/) · [designing a notification service](https://medium.com/@EshitaKhakharia/de-sign-notification-service-5cf6fac14d98).
