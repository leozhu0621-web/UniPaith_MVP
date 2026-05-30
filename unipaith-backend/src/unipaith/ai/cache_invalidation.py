"""Spec 03 §12 — cache invalidation rules.

Response caches (the `(profile_v, program_v, prompt_v)` cache on
MatchRationale and the analogous caches on other agents) must
invalidate when:

1. The student's profile version increments
   (any profile-section edit) — handled by composite key including
   profile_version. Automatic.
2. The program version increments
   (institution edit on a published program) — same mechanism.
3. The student's `consent_mask` changes
   — handled by `invalidate_for_consent_change` below.
4. The active model ID changes
   — bumped via PROMPT_VERSION constant when rolled.
5. The active prompt version changes
   — same PROMPT_VERSION constant.

PROMPT_VERSION is the single integer agents reference when reading or
writing rows. Bumping it forces every cached rationale to be re-derived
on next read. The old rows stay for the audit ledger; readers ignore
them because they no longer match the PK.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Spec 03 §12 — bumping this integer invalidates every cached rationale
# on next read. The old rows remain in match_rationales but the readers
# read (student_id, program_id, profile_v, program_v, PROMPT_VERSION)
# and miss; the agent regenerates and writes the new row.
#
# Bump when:
# - the rationale system prompt changes substantively (style, schema,
#   guardrails), OR
# - the active workhorse model rolls to a new family (sonnet 4.6 → 4.7).
RATIONALE_PROMPT_VERSION: int = 1


async def invalidate_for_consent_change(db: AsyncSession, student_id: uuid.UUID) -> int:
    """Delete every cached rationale for a student after their consent
    mask changed.

    Returns the number of rows removed. Logged so a compliance audit
    can verify the invalidation hop happened.

    The deletion is intentional, not soft — once a student opts out of
    matching, the cached rationales are stale derivative data they
    didn't consent to keep. The rule-based path takes over until the
    student opts back in.
    """
    # Local import — avoids the discovery-side circular load when this
    # module is imported by the consent endpoint.
    from unipaith.models.ai_artifacts import MatchRationale

    result = await db.execute(delete(MatchRationale).where(MatchRationale.student_id == student_id))
    count = result.rowcount or 0
    if count > 0:
        logger.info(
            "Cache invalidation: removed %d match_rationale rows for student=%s "
            "after consent change",
            count,
            student_id,
        )
    return count


async def invalidate_for_prompt_change(db: AsyncSession) -> int:
    """Delete every cached rationale whose `prompt_version` is below
    the current `RATIONALE_PROMPT_VERSION`. Use after bumping the
    constant in a release.

    Returns the row count removed. Safe to run multiple times.
    """
    from unipaith.models.ai_artifacts import MatchRationale

    result = await db.execute(
        delete(MatchRationale).where(MatchRationale.prompt_version < RATIONALE_PROMPT_VERSION)
    )
    count = result.rowcount or 0
    if count > 0:
        logger.info(
            "Cache invalidation: removed %d stale-prompt match_rationale rows " "(below v%d)",
            count,
            RATIONALE_PROMPT_VERSION,
        )
    return count
