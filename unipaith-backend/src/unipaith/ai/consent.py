"""Spec 03 §11 — consent enforcement at the LLM call site.

Every AIClient.message()/stream_message()/embed() call resolves the
student's consent mask BEFORE the request. The mask is recorded on the
audit ledger row (§8) so a compliance audit can verify every call
respected the active consent state at request time.

Mask shape
----------
The mask is a JSONB dict with four boolean keys (spec 03 §11):
- matching: program/school matching + the rationale agent
- outreach: any outbound LLM-drafted communication (inbox suggester)
- analytics: aggregate analytics + cohort metrics
- training: include in any retrieval-augmented fine-tuning corpus

The DB columns are `consent_matching`, `consent_outreach`,
`consent_research` (legacy name; mapped to `analytics`). `training` is
inferred from the absence of `consent_research=False` plus is implicit
in Anthropic's no-training default (spec 03 §11 caveat).

Agent → required-consent map
----------------------------
Each agent declares which mask key it needs. If the student denied that
key, the call short-circuits to the agent's rule-based fallback with
`failure_reason='consent_denied'` and a `consent_mask` recorded on the
ledger row.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentDataConsent

logger = logging.getLogger(__name__)


# Default mask used when:
# - student_id is None (eval harness / system jobs)
# - no StudentDataConsent row exists (older accounts pre-Appendix-A)
# Per spec 03 §11, the default is permissive — the consent UI is the
# enforceable surface, not a missing row. Updating this default is a
# governance decision, not a code edit; track in `43-data-rights-privacy.md`.
DEFAULT_MASK: dict[str, bool] = {
    "matching": True,
    "outreach": True,
    "analytics": True,
    "training": True,
}


# Spec 03 §11 — agents declare which consent gate they sit behind. The
# AIClient consults this map to decide whether a denied mask short-
# circuits the call. Workshop coaches are user-initiated artifact work
# and don't fall under any of the four mask categories — they always
# run (the student opening the workshop IS the consent signal).
AGENT_REQUIRES: dict[str, str | None] = {
    "orchestrator": None,  # discovery is consent-prerequisite at sign-up
    "extractor": "analytics",
    "validator": "analytics",
    "feature_emitter": "matching",
    "rationale": "matching",
    "workshop_coach": None,
    "workshop_judge": None,
    # Spec 17 §7 — the Inbox reply drafter produces outbound communication,
    # so it sits behind the `outreach` lever (this module's documented home
    # for "the inbox suggester"). Spec 17 §7's literal "matching" is
    # reconciled to `outreach` here. MANDATORY: `is_call_permitted` silently
    # allows agents missing from this map, so omitting this line would let
    # the drafter run even when the student denied outreach consent.
    "inbox_reply_drafter": "outreach",
    "embedding": "matching",  # used by the match pipeline
    # Spec 06 §2 / §5.2.
    "review_summarizer": "matching",  # institution review summary (45 §14)
    # Essay authenticity is an institution integrity workflow on a *submitted*
    # application — the act of applying is the consent signal, like the
    # workshop coaches. Gated by institution role, not the matching mask.
    "authenticity_risk": None,
    "matcher": "matching",  # L3 ML scoring (consent-gated in MatchService)
    # Spec 10 §3 / 45 §12 — type-first search interpreter (consent ["matching"]).
    # On deny, the SearchService catches ConsentDeniedError → rule-based parser.
    "query_interpreter": "matching",
    # Spec 20 §8 — Connect feed ranking + event recs. Gated on matching consent;
    # on deny the agent returns None and the feed falls back to its heuristic.
    "connect_ranker": "matching",
    "event_recommender": "matching",
    # Spec 25 §10 / 45 §16 — institution-side campaign copy suggester. Operates
    # on an aggregate audience summary, not any individual student's protected
    # data, so it sits behind no student-consent lever (institution role gates
    # it). Declared here so the spec-03 agent registry stays consistent.
    "campaign_copy": None,
    # Spec 24 §9 / 45 §19 — DocumentParseTriage runs on an institution-uploaded
    # dataset (no student in scope), so it carries no student-consent gate —
    # like review_summarizer / authenticity_risk. Access is gated by the
    # institution_admin role at the API layer.
    "document_parse_triage": None,
    # Spec 26 §6 / 45 §17 — SegmentBuilderNLBridge converts the institution's own
    # natural-language description into rules; no individual student is in scope,
    # so no student-consent gate (institution_admin role-gated at the API layer).
    # The resulting audience preview still honors each student's outreach
    # suppression in SegmentService.
    "segment_builder_nl": None,
    # Spec 29 §8 — institution messaging agents are institution-initiated and
    # role-gated at the API layer (like campaign_copy / review_summarizer), so
    # they carry no student-consent lever here. The InstitutionReplyDrafter
    # additionally checks the *applicant's* matching consent in-service before
    # enriching the draft with profile context — denial degrades to thread-text
    # only rather than blocking the call.
    "institution_reply_drafter": None,
    "inbound_intent_classifier": None,
    # Spec 32 §4/§6 — review-workspace assist agents are institution-initiated
    # and role-gated at the API layer (like review_summarizer). They operate on
    # an application within the reviewer's own tenant, so no student-consent
    # lever here.
    "review_synthesis": None,
    "review_assistant": None,
    # Spec 35 §6 — enrollment/yield intelligence agents are institution-initiated
    # and role-gated at the API layer (like review_summarizer / campaign_copy).
    # They operate on the institution's own admit pool aggregate, so no
    # student-consent lever here. Fairness disparities surface but never drive
    # selection (§4 / 46 §6); on any failure the services fall back to counts.
    "yield_risk_scorer": None,
    "next_best_action_yield": None,
}


async def get_consent_mask(
    db: AsyncSession | None, student_id: uuid.UUID | None
) -> dict[str, bool]:
    """Return the active consent mask for a student.

    Falls back to `DEFAULT_MASK` when:
    - `db` or `student_id` is None (eval harness, batch system jobs)
    - the student has no StudentDataConsent row yet

    This is a hot-path call (runs before every LLM request). It uses a
    single indexed read and returns a plain dict — no SQLAlchemy
    relationship loading.
    """
    if db is None or student_id is None:
        return dict(DEFAULT_MASK)
    row = await db.scalar(
        select(StudentDataConsent).where(StudentDataConsent.student_id == student_id)
    )
    if row is None:
        return dict(DEFAULT_MASK)
    return {
        "matching": bool(row.consent_matching),
        "outreach": bool(row.consent_outreach),
        # DB legacy: `consent_research` is the analytics consent.
        "analytics": bool(row.consent_research),
        # Spec 46 §2 4th lever. Anthropic doesn't train on customer data by
        # default; this gate governs UniPaith's own future fine-tuning
        # corpus extractor. Opt-in (column default false). No inference-time
        # agent declares `training` in AGENT_REQUIRES, so toggling it never
        # blocks a live call — it only flips the recorded consent mask.
        "training": bool(row.consent_training),
    }


def is_call_permitted(agent: str, mask: dict[str, bool]) -> bool:
    """Check whether a given agent may run under the given mask.

    Returns True for agents with no consent requirement
    (`AGENT_REQUIRES[agent] is None`) — those gates live elsewhere
    (sign-up flow, workshop entry).
    """
    needed = AGENT_REQUIRES.get(agent)
    if needed is None:
        return True
    return bool(mask.get(needed, True))
