from __future__ import annotations

import uuid

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile

# Account-level rows that reference the student but are NOT "memory" — kept on
# reset so the demo account stays usable. (Billing FKs users.id, not the
# profile, so it is never matched by the student_id sweep below.)
_KEEP_TABLES = {"student_data_consent"}


async def reset_student_demo_data(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Wipe a student's generated "memory" while KEEPING the account + profile
    row (demo mode). Every student-owned table references ``student_profiles.id``
    via a ``student_id`` column; we resolve the profile id, reset the profile's
    journey fields in place, then delete the student's rows from every such table.

    Robustness: each delete runs inside a SAVEPOINT so a missing column or an
    FK-ordering miss can never abort the surrounding login transaction — worst
    case is an incomplete (never a failed) reset. Two passes let child→parent
    FK-ordered deletes all land.
    """
    pid = (
        await session.execute(select(StudentProfile.id).where(StudentProfile.user_id == user_id))
    ).scalar_one_or_none()
    if pid is None:
        return

    # Reset the kept profile row's journey fields (also clears the
    # strategy_active_id FK before strategies are deleted).
    try:
        async with session.begin_nested():
            await session.execute(
                update(StudentProfile)
                .where(StudentProfile.id == pid)
                .values(discovery_completion={}, strategy_active_id=None)
            )
    except Exception:
        pass

    # Discover every table that references the profile via a `student_id` column.
    rows = await session.execute(
        text(
            "SELECT table_name FROM information_schema.columns "
            "WHERE column_name = 'student_id' AND table_schema = 'public'"
        )
    )
    tables = sorted({r[0] for r in rows} - _KEEP_TABLES)

    for _pass in range(2):
        for table in tables:
            try:
                async with session.begin_nested():
                    await session.execute(
                        text(f'DELETE FROM "{table}" WHERE student_id = :pid').bindparams(pid=pid)
                    )
            except Exception:
                pass

    await session.flush()
