# 71 · Connection Graph & Social Activation — Follows, Peers, Institution RAG Agent

> Stage 3a is *"a semi-social media solution (similar to the **Handshake model**)"* (`Master Paper`:61) — the connection-and-outreach layer where a prospect stops reading and starts *talking* to people. The benchmark names the mechanic: Unibuddy does **"tag-based auto-matching"** of prospects to current students (`Competition_Analysis`:2343) and reports **"51% of prospects who chat ultimately apply"** (`Competition_Analysis`:2421); its Assistant **"can never make things up"** (`Competition_Analysis`:2348), and EAB's Conversation Agent hands a thread to a human when it can't answer (`Competition_Analysis`:972). The doc's own rule for building this is **"integrate, don't rebuild"** (`Competition_Analysis`:2306).
>
> And we have *mostly* integrated. Spec `20` already shipped the follow graph and the Peers tab — but the founder's roadmap row (`64` §3 R3) and `51`:148 both still describe `student_follows` as **unbuilt**. That is **stale**: `models/follow.py:17` `InstitutionFollow` *is* the `student_follows` table (Spec `20` §7 chose to extend `institution_follows` rather than fork a parallel one), `models/peer.py` ships `PeerProfile`/`PeerConnection`/`PeerReport`, `api/connect.py` serves the feed + peers, and `consent_peer_connect` is live. This spec **corrects that record** and builds the four things that are *genuinely* absent: (1) **live** chat over `57` (peers message only through the async Inbox today — `Conversation.thread_type='peer'`, `models/engagement.py:250`); (2) a **prospect→ambassador/alumni** matching layer (today `peer_service.py:118` matches applicant↔applicant by shared *saved programs* only — there is no ambassador/alumni role and no tag-based auto-match); (3) **community spaces** + ambassador-hosted events (the `events` table has no student host, `models/institution.py:472`); (4) the **institution-facing conversational RAG agent** bounded to that institution's content — which does **not exist** (`advisor_matcher.py` is Spec `41` faculty matching; `orchestrator.py` is the *student* discovery chatbot).
>
> Build anchor: extend `models/follow.py`, `models/peer.py`, `models/engagement.py` (conversations), `services/peer_service.py`, `api/connect.py`, `core/realtime.py` (`57` broker), `models/institution.py` (events), and the `60`/`69` `KnowledgeDocument` index (`models/knowledge.py:55`). New: `ai/prospect_assistant.py` (Claude RAG, grounded by Qwen retrieval per `63` §1/§3). Pairs with `20`, `27`, `29`/`17`, `57`, `46`, `58`, `61`, `60`/`69`, `63`.
>
> Status: **draft v1.0** · 2026-06-02 · corrects the stale "`student_follows` unbuilt" record (`64`/`51`); adds the social graph's missing live layers — ambassador matching, live chat, community spaces, and the bounded institution RAG agent. Rule-based / async fallback stays default (`tests/test_plan2_integration.py`).

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Follow graph (`student_follows`) | `models/follow.py:17` `InstitutionFollow` (`source`, `muted`, `program_id`) | **exists — keep** (the row in `64`/`51` calling it "unbuilt" is stale; §2 corrects) |
| Follow/unfollow + active-app block | `services/follow_service.py:44,129` · `api/connect.py:124,153` | exists — keep |
| Connect feed (Updates/Events/Peers) | `api/connect.py:50` `get_feed` | exists — keep |
| Peer opt-in + sub-profile + consent | `models/peer.py` · `consent_peer_connect` (`student_service.py:1082`) | exists — keep |
| Peer discovery (shared programs) | `peer_service.py:118` `discover()` | exists — **extend (add ambassador/alumni + tags, §3)** |
| Peer messaging | async Inbox `Conversation.thread_type='peer'` (`engagement.py:250`) | exists — **make live over `57` (§4)** |
| **Ambassador / alumni role + tag-matching** | none | **NEW (build): §3** |
| **Live chat transport (1:1 + group)** | `57` broker carries notifications only | **NEW (build): §4** |
| **Community spaces** | none | **NEW (build): §5** |
| **Ambassador-hosted live events** | `Event` has no student host (`institution.py:472`) | **NEW (build): extend `27`, §5** |
| **Institution-facing prospect RAG agent** | none (`advisor_matcher.py`=Spec `41`; `orchestrator.py`=student) | **NEW (build): §6** |
| Crisis-safety floor on student chat | `ai/safety.py:207` `screen()` (used in discovery) | exists — **reuse on all student-facing chat (§7)** |

## 2. The follow graph — correct the record, don't rebuild

`64` §3 R3 and `51`:148 list `student_follows` as not-present. **It is present.** Spec `20` §7 made a deliberate naming call: rather than fork a `student_follows` table, it extended the existing `institution_follows` — `models/follow.py:17` `InstitutionFollow` carries exactly the documented shape (`student_id`, `institution_id`, `program_id|null`, `source ∈ {saved, application, explicit}`, `muted`). `services/follow_service.py` enforces the auto-follow-on-save and the unfollow-block-while-application-active rule; `api/connect.py:109-153` serves `list/follow/mute/unfollow`. This spec's only follow-graph work:

- **Reconcile the docs** — annotate `student_follows` as **shipped (= `institution_follows`)** in `51` §data-model and `64` §3 R3; the table is the substrate the rest of `71` builds on, not net-new.
- **One additive column** for the ambassador layer (§3): `InstitutionFollow.notify_peers` (bool, default true) — whether this follow makes the student discoverable to *that institution's* ambassadors (consent-scoped, §7). Migration: Alembic, expand→contract, single head (122 revisions today).
- Notification fan-out on a new follow already routes through `57` (`services/notification_service.py`); ambassador/space events (§3–§5) reuse that same idempotent emit — no new transport.

## 3. Peer-to-ambassador & alumni — the tag-matching the papers name

Today `peer_service.py:118` `discover()` matches **applicant ↔ applicant** by *shared saved programs* only. The Handshake/Unibuddy mechanic is **prospect → current-student/alumni ambassador**, auto-matched on **course / country / interest tags** (`Competition_Analysis`:2343). Build it as a *focused layer on the existing peer scaffold* (`Competition_Analysis`:2306 "integrate, don't rebuild") — not a parallel system:

- **Ambassador role** — extend `PeerProfile` (`models/peer.py:36`) with `role ∈ {peer, ambassador, alumni}` (default `peer`), `verified_institution_id` (FK, nullable — the school they represent), `ambassador_tags` JSONB (`fields`/`countries`/`interests` — the same taxonomy as student signals `42`/`44`), and `accepting_chats` (bool). An **ambassador is institution-verified** (the institution invites/approves them via a new `/institutions/me/ambassadors` surface, reusing `require_institution_admin` + `36` audit) — a prospect must never be misled about who's official (`58` UGC trust).
- **Tag auto-match** (`services/peer_service.py`, new `match_ambassadors()`) — deterministic overlap score over (course/country/interest) tags between the prospect's signals and ambassador tags, **same shape as `advisor_matcher.py:research_alignment`** (calibrated overlap; the seam an embedding cosine slots into per `63` §2). Returns ranked ambassadors **for the institutions the prospect follows** (§2 `notify_peers` gate). Pure + deterministic — never 5xx; the AI flag only enriches a one-line "why this ambassador" rationale (Claude, `63` §3).
- **Reuse the connection state machine** — an ambassador chat is a `PeerConnection` (`models/peer.py:74`) with `role='ambassador'`; accept opens the live thread (§4). Block/report (`PeerReport`) and the **no-minor-to-adult** gate (`peer_service.py:212`) + rate-limit (`:366`) apply unchanged. Alumni-as-mentor is the `20` §14 "admit-mentor" deferral, now concrete: `role='alumni'`, institution-verified.

## 4. Live chat — make the `peer` thread real-time over `57`

Peers/ambassadors message today only through the **async** Inbox (`Conversation.thread_type='peer'`, `models/engagement.py:250`; the WS endpoint `api/realtime.py:183` `/ws/messages` exists but carries *notifications*, not a live peer transport). Add live delivery **without a new transport** — the `57` broker (`core/realtime.py:72` `RealtimeBroker.publish`/`subscribe`, Redis cross-task bridge) already fans messages to every participant's stream:

- **1:1 live chat** — on a peer/ambassador message write, `publish` a `peer_message` event to the *other* participant's channel (`_other_participants`, `api/realtime.py:123`); the existing `useMessageStream` (`57`) patches the thread cache. Typing/presence are ephemeral `peer_typing`/`presence` events (never persisted). The Inbox row remains the durable record — live is an overlay, not a replacement.
- **Group chat** — extend `Conversation` with `is_group` (bool) + a `conversation_participants` join table (`conversation_id`, `student_id`, `role`, `joined_at`); group messages fan out to all participants' channels. Group threads back the community spaces (§5) and ambassador-hosted sessions.
- **Fallback (the invariant):** broker/Redis unavailable → message still **persists** to `messages`; the recipient sees it on next poll/SSE-reconnect. **Live is best-effort; delivery is durable.** No path 5xxes (`tests/test_plan2_integration.py`).
- Gate the live overlay behind **`social_live_chat_enabled`** (net-new flag, default off; async Inbox is the floor). Consent: live peer/ambassador chat requires `consent_peer_connect` exactly as the async path does (`peer_service.py:69` `require_opted_in`).

## 5. Community spaces + live events

A **community space** is a topic- or cohort-scoped group thread (e.g. "CS MS applicants — Fall 26", "International students — UK") that an institution or a verified ambassador hosts. Built on the §4 group primitive, not a new chat stack:

- **New `community_spaces` table** — `id`, `institution_id` (FK, nullable for cross-institution interest spaces), `kind ∈ {program, cohort, interest, event}`, `name`, `description`, `host_student_id` (ambassador, nullable), `visibility ∈ {public, followers, invited}`, `conversation_id` (the backing group thread), `member_count`, timestamps. Membership = `conversation_participants` (§4).
- **Discovery & join** — spaces surface in Connect (`api/connect.py`) scoped to followed institutions (§2) + matched interests (§3 tags); join is consent-gated (`consent_peer_connect`) and visibility-gated. A `followers`-visibility space is open to anyone following the institution; `invited` requires an ambassador/institution invite.
- **Ambassador-hosted live events** — extend `models/institution.py:472` `Event` with `host_student_id` (nullable FK → ambassador) and `space_id` so a verified ambassador can host an AMA / live Q&A. RSVP (`EventRSVP`, `institution.py:510`) and the calendar/inbox fan-out (`27` §3.1 / `20` §5) are **unchanged** — this is one nullable host column, not a new events system. During a live event the space's group thread is the chat backchannel (§4).
- **Moderation (`58`):** every space message and event-chat message passes the same UGC moderation hook as peer DMs (§7); spaces have an ambassador/institution moderator who can mute/remove; reports route to the existing `PeerReport` moderation queue.

## 6. Institution-facing prospect RAG agent — bounded, never invents, human handoff

The one genuinely net-new *agent*. A prospect on an institution's space/page can ask "what's the average class size?" / "is there funding for internationals?" and get an **immediate, grounded** answer — Unibuddy Assistant **"can never make things up"** (`Competition_Analysis`:2348,2352); EAB's agent **hands off to a human** when unsure (`Competition_Analysis`:972). Per `63` §1/§3 this is **human-facing → Claude**, grounded by **Qwen RAG** over the `60`/`69` knowledge index.

- **`ai/prospect_assistant.py` (Claude, `63` §3).** Retrieval-augmented over **only that institution's** `KnowledgeDocument`s (`models/knowledge.py:36`, `embedding Vector(1536)`) + its public programs/outcomes (`68`) — a hard `institution_id` filter on retrieval is the bound. The prompt is **strictly grounded**: answer only from retrieved chunks, cite the source, and **if the retrieved context doesn't cover the question, say so and offer a human** — no parametric fabrication (the same groundedness contract as `ai/rationale.py` and the `60` "never invents" extractor; reuse the constitution + safety-floor pattern from `61`).
- **Confidence gate → automatic human handoff.** Each answer carries a retrieval-grounded confidence (chunk relevance × coverage). **Below threshold → the agent does not answer; it opens (or routes to) an institution Inbox thread** (`29` `Conversation`, `waiting_on='institution'`) and tells the prospect a person will follow up. Above threshold → answer + cite + "was this helpful / talk to a person" escape hatch. The threshold is per-institution config (mirrors `37` AI-config thresholds).
- **Conversation → CRM summary.** On thread close/handoff, summarize the exchange (intent, questions asked, programs of interest) into a CRM note on the prospect's `crm_records` (`models/engagement.py:202`) / recruitment prospect (`40`) — the §2421 funnel signal ("prospects who chat apply"). Summary is a Claude call (`45`-tier), grounded in the transcript, **no fabrication**; falls back to a structured transcript dump if the LLM call fails.
- **Knowledge-retrieval helper.** `60`'s index has the embeddings but no semantic-search helper yet (`services/crawler/engine.py` only does exact-URL lookups). Add a shared `knowledge_search(institution_id, query, k)` (pgvector `<->` over `KnowledgeDocument.embedding`) — **shared with `65`/`69`** (one retrieval path, not three). Embeddings are Qwen (`63` §8, 1536-d, no migration).
- **Flag + fallback:** `ai_prospect_assistant_v2_enabled` (net-new, default off). Disabled, or any retrieval/LLM failure → **no answer is fabricated**; the prospect is routed straight to the human Inbox thread (the safe default *is* the handoff). Never 5xx.

## 7. Consent, safety & moderation (the floor on a social surface)

A social graph is the highest-risk surface in the product — every student-facing message gets the safety floor, every visibility is opt-in (`46`), every piece of UGC is moderatable (`58`).

- **Consent (`46`).** Peer/ambassador visibility and live chat require `consent_peer_connect` (live today). Ambassador discoverability adds the §2 `notify_peers` per-follow toggle. The AI prospect assistant (§6) reads **only public, non-personal** institution knowledge (`60` scope) — it never reads a prospect's profile without `consent.matching`, and its CRM summary is consent-scoped like `29` §8.
- **Crisis-safety floor (`61`).** **Reuse `ai/safety.py:207` `screen()`** (already wired into discovery, `services/discovery_service.py`) on **all student-facing chat** — peer DMs, ambassador chats, space messages. A crisis signal short-circuits to the escalation resource (`safety.py:167` `CRISIS_RESPONSE`); favours recall (over-escalate). This is a **hard floor**, flag-independent, identical to the chatbot contract.
- **UGC moderation (`58`).** Every peer/ambassador/space message runs a moderation hook before fan-out; flagged content is withheld + queued. Block/report (`PeerReport`) and the no-minor-to-adult gate (`peer_service.py:212`) apply to ambassadors and spaces unchanged. Ambassadors are institution-verified (§3) so a prospect can trust who's official.
- **Privacy invariant preserved.** The `models/peer.py` contract test (`tests/test_connect_peers.py`) asserts the peer sub-profile **structurally excludes** scores/GPA/documents/decisions/financials — ambassador/space additions must keep that test green (no score/GPA field may appear on any §3–§5 model).

## 8. Build tasks (checklist)

- [ ] Docs reconcile: mark `student_follows` **shipped (= `institution_follows`)** in `51` + `64` §3 R3; `InstitutionFollow.notify_peers` column (migration, expand→contract, single head).
- [ ] `PeerProfile` extended: `role ∈ {peer, ambassador, alumni}`, `verified_institution_id`, `ambassador_tags` JSONB, `accepting_chats`; `/institutions/me/ambassadors` invite/approve (audit `36`).
- [ ] `peer_service.match_ambassadors()` — deterministic tag-overlap (course/country/interest), scoped to followed institutions; AI flag enriches rationale only; never 5xx.
- [ ] Live chat over `57` broker: `peer_message`/`peer_typing`/`presence` publish on write; `social_live_chat_enabled` flag; **message persists even if broker down** (durable floor).
- [ ] Group chat: `Conversation.is_group` + `conversation_participants` join table; fan-out to all participants.
- [ ] `community_spaces` table + Connect discovery/join (visibility + consent gated); moderator controls.
- [ ] `Event.host_student_id` + `space_id` — ambassador-hosted live events; RSVP/calendar fan-out unchanged (`27`/`20`).
- [ ] `ai/prospect_assistant.py` — Claude RAG bounded by `institution_id` over `KnowledgeDocument`; grounded/cited; **confidence-gated auto-handoff** to Inbox; `ai_prospect_assistant_v2_enabled` flag.
- [ ] Shared `knowledge_search(institution_id, query, k)` pgvector helper (shared with `65`/`69`); register `prospect_assistant` in `ai/agent_registry.py` + `ai/consent.py`.
- [ ] Conversation→CRM summary on handoff/close → `crm_records` / `40` prospect; fallback to transcript dump.
- [ ] Safety: `ai/safety.py:screen()` on every student-facing chat path; UGC moderation hook before fan-out; minor/adult + rate-limit gates extended to ambassadors/spaces.
- [ ] Fallbacks tested: assistant failure → human handoff (no fabrication); broker down → durable async delivery; flags off → exact current async Inbox behavior (`tests/test_plan2_integration.py`).

## 9. Acceptance

- [ ] `51`/`64` no longer describe `student_follows` as unbuilt; the engine reads `InstitutionFollow` as the live follow graph.
- [ ] A prospect following an institution is auto-matched to a **verified ambassador** of that institution by course/country/interest tags (deterministic, fairness-clean — no protected attributes in the match, `46` §6).
- [ ] A peer/ambassador message is delivered **live** when the broker is up and **still arrives** (persisted) when it is down; flag off = exact async Inbox behavior.
- [ ] A community space is a joinable group thread gated by visibility + `consent_peer_connect`; an ambassador can host a live event with RSVP/calendar fan-out intact.
- [ ] The prospect assistant answers **only** from the asking institution's knowledge, **cites** sources, and **never fabricates**; an unanswerable question opens a human Inbox thread; the exchange lands as a CRM note.
- [ ] Disabling `ai_prospect_assistant_v2_enabled` routes prospects straight to a human — no degraded or invented answer; no 5xx.
- [ ] A crisis signal in any student-facing chat short-circuits to the `61` escalation resource regardless of flags.
- [ ] No ambassador/space/event model exposes a score/GPA/document/decision/financial field (`tests/test_connect_peers.py` stays green).

## 10. Open questions

- **Ambassador supply for v1.** Ambassadors need recruiting before the tag-match has anyone to match to. *Recommend: ship peer↔peer (live, §3–§4) for v1; gate ambassador discovery behind `social_ambassadors_enabled` and turn it on per-institution as each onboards verified students (mirrors `20` §14 "Peers fast-follow").*
- **Assistant grounding scope.** Public knowledge (`60`) only, or also the institution's *private* uploaded FAQ (`24`)? *Recommend: public + institution-opted-in private FAQ (usage-scope consent, `69`); never a prospect's own profile without `consent.matching`.*
- **Confidence threshold for handoff.** Too high → over-escalates (kills the funnel value); too low → risks a wrong answer. *Recommend: start conservative (favour handoff like the `61` crisis floor favours recall), tune per-institution via `37` AI-config + `62` eval on a grounded-QA golden set.*
- **Group vs 1:1 first.** Community spaces are higher-value but heavier to moderate. *Recommend: 1:1 ambassador chat first (clear moderation surface), spaces fast-follow once moderator tooling (§5/§7) is proven.*
- **Embedder for retrieval.** Shares `65`/`63` §8's choice (managed Qwen/Bedrock → self-host on volume). *Recommend: reuse whatever `65` lands; the assistant consumes the same index, not a parallel one.*

Sources: internal — `20` (Connect feed, follows, peers), `27` (posts/events), `28` (attribution/CRM signal), `29`/`17` (institution + peer messaging), `40` (recruitment prospect), `46` (consent/peer_connect), `57` (realtime broker, SSE/WS), `58` (security/UGC moderation), `60`/`69` (knowledge index), `61` (chatbot safety floor + constitution), `63` (§1/§3 Qwen-RAG/Claude-voice boundary, §8 embeddings), `64` §3 R3 (the `71` row), `65` (shared retrieval/embedder), `51`:148 (data-model record corrected here). Code — `models/follow.py:17`, `models/peer.py:36,74`, `models/engagement.py:202,250`, `models/institution.py:472,510`, `models/knowledge.py:36,55`, `services/follow_service.py:44,129`, `services/peer_service.py:69,118,212,366`, `api/connect.py:50,124`, `api/realtime.py:123,183`, `core/realtime.py:72`, `ai/safety.py:167,207`, `ai/advisor_matcher.py`, `ai/orchestrator.py`, `ai/agent_registry.py`, `ai/institution_reply.py`, `config.py:311,324`. Papers — `Master_Paper.docx`:59,61. Benchmark — `Competition_Analysis.docx`:972 (EAB handoff), :2306 (integrate-don't-rebuild), :2343 (tag auto-match), :2348,2352 (never-invents), :2421 (51% chat→apply).
