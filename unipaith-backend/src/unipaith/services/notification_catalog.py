"""Spec 57 §3 — the typed notification catalog.

One registry mapping an ``event_type`` (the concrete string every ``notify()`` call
passes today) to:

- ``pref_key`` — the per-type preference category (one of the canonical
  ``notification_service.NOTIFICATION_TYPES`` keys) the per-channel matrix is keyed
  on, so a user's per-type × per-channel preference actually governs the send;
- ``urgency`` — ``urgent`` (fire immediately) vs ``digest`` (batch into the periodic
  digest email, §6);
- ``silenceable`` — ``False`` for transactional / active-application events
  (decision, interview, applied-program deadline, missing-item) which §4 says may be
  *down-ranked but never fully silenced*: in-app delivery stays on for safety;
- optional ``title`` / ``body`` / ``deep_link`` templates — used by the catalog-driven
  ``emit()`` path and the digest renderer. Existing callers that pass their own copy
  keep working unchanged.

Pure data + helpers. Imports nothing from the service layer, so
``notification_service`` can import it without a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass

# Urgency classes (§6). Urgent → immediate; digest → batched daily/weekly.
URGENT = "urgent"
DIGEST = "digest"


@dataclass(frozen=True)
class CatalogEntry:
    event_type: str
    pref_key: str
    urgency: str  # URGENT | DIGEST
    silenceable: bool
    title: str = ""
    body: str = ""
    deep_link: str = ""

    @property
    def essential(self) -> bool:
        """Mirror of ``NOTIFICATION_TYPES.essential`` — transactional safety types."""
        return not self.silenceable


# ── The catalog ──────────────────────────────────────────────────────────────
# Keyed by the concrete ``event_type`` string. ``pref_key`` reuses the canonical
# preference categories so the per-channel matrix governs delivery.
_ENTRIES: tuple[CatalogEntry, ...] = (
    # ── Student-facing, transactional (not silenceable — in-app stays on) ──
    CatalogEntry(
        "decision_made",
        "decisions",
        URGENT,
        silenceable=False,
        title="Application decision update",
        body="A decision has been made on your application.",
        deep_link="/applications/{application_id}",
    ),
    CatalogEntry(
        "offer_sent",
        "decisions",
        URGENT,
        silenceable=False,
        title="Offer letter available",
        body="Your offer letter is ready — review and respond.",
        deep_link="/applications/{application_id}/offers/{offer_id}",
    ),
    CatalogEntry(
        "enrollment_update",
        "decisions",
        URGENT,
        silenceable=False,
        title="Enrollment update",
        body="There's an update on your enrollment.",
        deep_link="/applications/{application_id}",
    ),
    CatalogEntry(
        "interview_scheduled",
        "interview_invites",
        URGENT,
        silenceable=False,
        title="Interview scheduled",
        body="An interview has been scheduled for your application.",
        deep_link="/applications/{application_id}/interviews/{interview_id}",
    ),
    CatalogEntry(
        "interview_confirmed",
        "interview_invites",
        URGENT,
        silenceable=False,
        title="Interview time confirmed",
        body="Your interview time has been confirmed.",
        deep_link="/interviews/{interview_id}",
    ),
    CatalogEntry(
        "deadline_reminders",
        "deadline_reminders",
        URGENT,
        silenceable=False,
        title="Deadline approaching",
        body="A deadline on one of your applications is approaching.",
        deep_link="/s/manage?tab=calendar",
    ),
    CatalogEntry(
        "application_missing_item",
        "application_missing_item",
        URGENT,
        silenceable=False,
        title="Action needed on your application",
        body="Your application is missing a required item.",
        deep_link="/applications/{application_id}",
    ),
    # ── Student-facing, non-transactional (silenceable) ──
    CatalogEntry(
        "message_received",
        "messages",
        URGENT,
        silenceable=True,
        title="New message",
        body="You have a new message.",
        deep_link="/messages/{conversation_id}",
    ),
    CatalogEntry(
        "saved_search_alert",
        "match_updates",
        DIGEST,
        silenceable=True,
        title="New matches for your saved search",
        body="New programs match a search you saved.",
        deep_link="/s/saved?tab=searches",
    ),
    CatalogEntry(
        "match_update",
        "match_updates",
        DIGEST,
        silenceable=True,
        title="Your matches were refreshed",
        body="Your program recommendations were updated.",
        deep_link="/s/explore",
    ),
    CatalogEntry(
        "institution_post",
        "institution_posts",
        DIGEST,
        silenceable=True,
        title="New post from a saved program",
        body="An institution you follow shared an update.",
        deep_link="/s/posts",
    ),
    CatalogEntry(
        "campaign",
        "institution_posts",
        DIGEST,
        silenceable=True,
        title="Message from an institution",
        body="An institution sent you an update.",
        deep_link="/s/posts",
    ),
    # ── Institution-facing ──
    CatalogEntry(
        "application_submitted",
        "messages",
        URGENT,
        silenceable=True,
        title="New application received",
        body="A new application has been submitted.",
        deep_link="/applications/{application_id}",
    ),
    CatalogEntry(
        "reviewer_assigned",
        "messages",
        URGENT,
        silenceable=True,
        title="New review assignment",
        body="You've been assigned to review an application.",
        deep_link="/reviews/applications/{application_id}",
    ),
    CatalogEntry(
        "inquiry",
        "messages",
        URGENT,
        silenceable=True,
        title="New inquiry",
        body="A prospective applicant sent an inquiry.",
        deep_link="/i/communications?tab=inbox",
    ),
    CatalogEntry(
        "fairness_auto_halt",
        "decisions",
        URGENT,
        silenceable=False,
        title="Matching paused — fairness threshold",
        body="Automated matching was paused after a disparate-impact signal.",
        deep_link="/i/fairness",
    ),
)

CATALOG: dict[str, CatalogEntry] = {e.event_type: e for e in _ENTRIES}

# Fallback for any event_type not explicitly registered. Treated as an urgent,
# silenceable in-app/email message keyed on the generic "messages" category — the
# safe default the legacy ``notify()`` already used.
DEFAULT_ENTRY = CatalogEntry(
    "default", "messages", URGENT, silenceable=True, title="", body="", deep_link=""
)


def get_entry(event_type: str) -> CatalogEntry:
    """Return the catalog entry for ``event_type``, or the safe default.

    A ``template_*`` institution-message type (e.g. ``template_acceptance``) and any
    other unregistered string resolve to ``DEFAULT_ENTRY`` so an unknown event still
    delivers in-app + email rather than being dropped.
    """
    return CATALOG.get(event_type, DEFAULT_ENTRY)


def urgency_of(event_type: str) -> str:
    return get_entry(event_type).urgency


def is_silenceable(event_type: str) -> bool:
    return get_entry(event_type).silenceable


def render(event_type: str, context: dict | None = None) -> tuple[str, str, str | None]:
    """Render ``(title, body, deep_link)`` for an event from its templates + context.

    Missing context keys leave the ``{placeholder}`` in place rather than raising, so
    a partially-specified emit still produces a usable notification.
    """
    entry = get_entry(event_type)
    ctx = {str(k): str(v) for k, v in (context or {}).items()}

    def _fill(tmpl: str) -> str:
        out = tmpl
        for key, val in ctx.items():
            out = out.replace("{" + key + "}", val)
        return out

    title = _fill(entry.title) if entry.title else ""
    body = _fill(entry.body) if entry.body else ""
    deep_link = _fill(entry.deep_link) if entry.deep_link else None
    return title, body, deep_link


def event_type_count() -> int:
    """Number of registered event types — surfaced on the /goal/realtime page."""
    return len(CATALOG)


def catalog_summary() -> list[dict]:
    """A serializable view of the catalog for the transparency surface (no PII)."""
    return [
        {
            "event_type": e.event_type,
            "pref_key": e.pref_key,
            "urgency": e.urgency,
            "silenceable": e.silenceable,
        }
        for e in _ENTRIES
    ]
