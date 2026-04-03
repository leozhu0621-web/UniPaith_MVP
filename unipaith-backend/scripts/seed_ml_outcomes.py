"""
Seed realistic ML training data — PredictionLogs + OutcomeRecords.

Bootstraps the self-improving loop so the ML pipeline can train a first
model without waiting for real users to go through the full application
flow.

Usage:
    cd unipaith-backend
    PYTHONPATH=src python -m scripts.seed_ml_outcomes        # seed
    PYTHONPATH=src python -m scripts.seed_ml_outcomes --dry   # count only
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import random
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import async_session
from unipaith.models.institution import Program
from unipaith.models.matching import ModelRegistry, PredictionLog
from unipaith.models.ml_loop import OutcomeRecord
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TARGET_OUTCOMES = 120
MIN_EXTRA_STUDENTS = 10


def _random_features(gpa: float, tier: int) -> dict:
    """Generate a plausible features_snapshot for a prediction."""
    return {
        "normalized_gpa": round(gpa / 4.0, 4),
        "work_experience_years": round(random.uniform(0, 5), 1),
        "research_count": random.randint(0, 4),
        "leadership_count": random.randint(0, 3),
        "publication_count": random.randint(0, 3),
        "total_activities": random.randint(2, 12),
        "test_score_avg": round(random.uniform(0.5, 1.0), 4),
        "embedding_similarity": round(random.uniform(0.3, 0.95), 4),
        "historical_fit": round(random.uniform(0.2, 0.9), 4),
        "institution_pref_fit": round(random.uniform(0.3, 0.95), 4),
        "student_pref_fit": round(random.uniform(0.3, 0.95), 4),
        "budget_fit": round(random.uniform(0.1, 1.0), 4),
    }


def _outcome_for(score: float) -> str:
    """Probabilistically assign an outcome correlated with prediction score."""
    r = random.random()
    if score > 0.7:
        return "admitted" if r < 0.70 else ("enrolled" if r < 0.85 else "rejected")
    if score > 0.45:
        return "admitted" if r < 0.35 else ("rejected" if r < 0.70 else "enrolled")
    return "rejected" if r < 0.65 else ("admitted" if r < 0.85 else "declined")


async def _ensure_extra_students(db: AsyncSession, needed: int) -> list[uuid.UUID]:
    """Create lightweight synthetic student profiles for ML seeding."""
    first_names = [
        "Alex", "Jordan", "Taylor", "Morgan", "Casey",
        "Riley", "Quinn", "Avery", "Harper", "Sage",
        "Drew", "Cameron", "Rowan", "Hayden", "Blake",
        "Emery", "Dakota", "Skyler", "Finley", "Reese",
    ]
    ids: list[uuid.UUID] = []
    for i in range(needed):
        name = first_names[i % len(first_names)]
        suffix = i // len(first_names) + 1
        email = f"synth.{name.lower()}{suffix}@seed.local"

        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            profile = await db.scalar(
                select(StudentProfile).where(StudentProfile.user_id == existing.id)
            )
            if profile:
                ids.append(profile.id)
                continue

        user = User(
            email=email,
            cognito_sub=str(uuid.uuid4()),
            role=UserRole.student,
        )
        db.add(user)
        await db.flush()

        profile = StudentProfile(
            user_id=user.id,
            first_name=name,
            last_name=f"Seed{suffix}",
            nationality="Synthetic",
            country_of_residence="United States",
        )
        db.add(profile)
        await db.flush()
        ids.append(profile.id)

    return ids


async def seed_ml(db: AsyncSession, *, dry: bool = False) -> None:
    existing_outcomes = await db.scalar(
        select(func.count()).select_from(OutcomeRecord)
    ) or 0
    if existing_outcomes >= TARGET_OUTCOMES:
        logger.info(
            "Already have %d outcome records (target %d) — skipping.",
            existing_outcomes,
            TARGET_OUTCOMES,
        )
        return

    active_version = (
        await db.scalar(
            select(ModelRegistry.model_version)
            .where(ModelRegistry.is_active.is_(True))
        )
    ) or "heuristic-default"
    logger.info("Active model version: %s", active_version)

    students = list(
        (await db.execute(select(StudentProfile.id))).scalars().all()
    )
    programs = list(
        (await db.execute(select(Program.id))).scalars().all()
    )

    if not programs:
        logger.error("No programs found. Run seed_dev_data.py first.")
        return

    needed_pairs = TARGET_OUTCOMES - existing_outcomes
    pairs_available = len(students) * len(programs)

    if pairs_available < needed_pairs:
        extra = (needed_pairs - pairs_available) // len(programs) + 1
        extra = max(extra, MIN_EXTRA_STUDENTS)
        logger.info("Creating %d synthetic students for ML seeding", extra)
        if not dry:
            new_ids = await _ensure_extra_students(db, extra)
            students.extend(new_ids)

    random.shuffle(students)
    random.shuffle(programs)

    created = 0
    now = datetime.now(UTC)

    for student_id in students:
        if created >= needed_pairs:
            break
        for program_id in programs:
            if created >= needed_pairs:
                break

            existing = await db.scalar(
                select(func.count())
                .select_from(PredictionLog)
                .where(
                    PredictionLog.student_id == student_id,
                    PredictionLog.program_id == program_id,
                )
            )
            if existing and existing > 0:
                continue

            gpa = round(random.uniform(2.5, 4.0), 2)
            tier = random.randint(1, 5)
            score = round(random.uniform(0.15, 0.95), 4)
            features = _random_features(gpa, tier)
            predicted_at = now - timedelta(
                days=random.randint(7, 180),
                hours=random.randint(0, 23),
            )
            outcome = _outcome_for(score)

            if dry:
                created += 1
                continue

            pred = PredictionLog(
                student_id=student_id,
                program_id=program_id,
                predicted_score=Decimal(str(score)),
                predicted_tier=tier,
                model_version=active_version,
                features_used=features,
                predicted_at=predicted_at,
                actual_outcome=outcome,
                outcome_recorded_at=predicted_at + timedelta(days=random.randint(14, 90)),
            )
            db.add(pred)
            await db.flush()

            rec = OutcomeRecord(
                prediction_log_id=pred.id,
                student_id=student_id,
                program_id=program_id,
                predicted_score=Decimal(str(score)),
                predicted_tier=tier,
                actual_outcome=outcome,
                outcome_source="application_decision",
                outcome_confidence=Decimal("0.70"),
                features_snapshot=features,
                outcome_recorded_at=pred.outcome_recorded_at,
            )
            db.add(rec)
            await db.flush()
            created += 1

    if not dry:
        await db.commit()

    logger.info(
        "%s %d outcome records (total now: %d)",
        "Would create" if dry else "Created",
        created,
        existing_outcomes + created,
    )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="Count only, don't write")
    args = parser.parse_args()

    async with async_session() as db:
        await seed_ml(db, dry=args.dry)


if __name__ == "__main__":
    asyncio.run(main())
