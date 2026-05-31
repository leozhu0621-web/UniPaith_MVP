"""Seed the unipaith_preview DB with varied Spec 15 application states.

Run with DATABASE_URL pointed at unipaith_preview. Drops + recreates schema
via create_all (the from-base alembic chain is pre-existing-broken), then seeds
a demo student and a portfolio that exercises every dashboard bucket + the
guardrails / offer / external paths.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from unipaith.config import settings
from unipaith.models.application import Application, OfferLetter
from unipaith.models.base import Base
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import AcademicRecord, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.checklist_service import ChecklistService

DEMO_EMAIL = "demo@unipaith.co"


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sm() as db:
        # Student
        user = User(
            id=uuid.uuid4(),
            email=DEMO_EMAIL,
            cognito_sub="dev-demo",
            role=UserRole("student"),
            is_active=True,
        )
        db.add(user)
        await db.flush()
        profile = StudentProfile(
            user_id=user.id,
            first_name="Maya",
            last_name="Chen",
            nationality="Singapore",
            country_of_residence="Singapore",
            bio_text="Aspiring ML engineer focused on health applications.",
        )
        db.add(profile)
        await db.flush()
        db.add(
            AcademicRecord(
                student_id=profile.id,
                institution_name="National University of Singapore",
                degree_type="bachelors",
                field_of_study="Computer Science",
                gpa=Decimal("3.80"),
                gpa_scale="4.0",
                is_current=False,
            )
        )

        # Institutions + programs (each needs its own admin user — unique FK).
        def inst(name: str) -> Institution:
            admin = User(
                id=uuid.uuid4(),
                email=f"admin-{uuid.uuid4().hex[:6]}@{name.split()[0].lower()}.edu",
                cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
                role=UserRole("institution_admin"),
                is_active=True,
            )
            db.add(admin)
            i = Institution(admin_user_id=admin.id, name=name, type="university", country="US")
            db.add(i)
            return i

        northbridge = inst("Northbridge University")
        lakeside = inst("Lakeside Institute of Technology")
        carthage = inst("Carthage University")
        await db.flush()

        def prog(
            institution: Institution, name: str, deadline_days: int | None, tuition: int
        ) -> Program:
            p = Program(
                institution_id=institution.id,
                program_name=name,
                degree_type="masters",
                description_text=f"{name} — a rigorous graduate program.",
                tuition=tuition,
                is_published=True,
                application_deadline=(date.today() + timedelta(days=deadline_days))
                if deadline_days is not None
                else None,
            )
            db.add(p)
            return p

        cs = prog(northbridge, "Computer Science MS", 6, 58000)
        ds = prog(lakeside, "Data Science MS", 25, 49000)
        hci = prog(carthage, "Human-Computer Interaction MS", 40, 52000)
        info = prog(northbridge, "Information Systems MS", 12, 45000)
        await db.flush()

        def match(p: Program, fitness: float, conf: float) -> None:
            db.add(
                MatchResult(
                    student_id=profile.id,
                    program_id=p.id,
                    fitness_score=Decimal(str(fitness)),
                    confidence_score=Decimal(str(conf)),
                    rationale_text="Strong alignment with your goals and academic background.",
                )
            )

        match(cs, 0.82, 0.78)
        match(ds, 0.18, 0.62)  # low fit → guardrails
        match(hci, 0.74, 0.70)
        match(info, 0.66, 0.71)

        def application(p: Program, status: str, **kw) -> Application:
            a = Application(
                student_id=profile.id,
                program_id=p.id,
                status=status,
                submission_mode=kw.get("submission_mode", "internal"),
                completeness_status=kw.get("completeness_status", "incomplete"),
                match_score=kw.get("match_score"),
                decision=kw.get("decision"),
                decision_at=kw.get("decision_at"),
                submitted_at=kw.get("submitted_at"),
                intent_picker=kw.get("intent_picker"),
                intent_rationale=kw.get("intent_rationale"),
            )
            db.add(a)
            return a

        app_cs = application(cs, "draft", match_score=Decimal("0.82"), intent_picker="dream")
        app_ds = application(ds, "draft", match_score=Decimal("0.18"), submission_mode="external")
        app_info = application(
            info,
            "submitted",
            match_score=Decimal("0.66"),
            submitted_at=datetime.now(UTC) - timedelta(days=3),
        )
        app_hci = application(
            hci,
            "decision_made",
            match_score=Decimal("0.74"),
            decision="admitted",
            decision_at=datetime.now(UTC) - timedelta(days=1),
            submitted_at=datetime.now(UTC) - timedelta(days=20),
        )
        await db.flush()

        # Offer for the admitted app
        db.add(
            OfferLetter(
                application_id=app_hci.id,
                offer_type="full_admission",
                tuition_amount=52000,
                scholarship_amount=20000,
                financial_package_total=20000,
                response_deadline=date.today() + timedelta(days=21),
                status="sent",
            )
        )
        await db.commit()

        # Generate checklists so readiness_pct is populated for the draft apps.
        cl = ChecklistService(db)
        for a in (app_cs, app_ds, app_info, app_hci):
            await cl.generate_checklist(profile.id, a.id)
        await db.commit()

        print(f"Seeded demo student: {DEMO_EMAIL}")
        print(f"  token: dev:{profile.id}:student  (login with any password)")
        print("  apps: CS(draft) · DS(external/low-fit) · Info(submitted) · HCI(admitted+offer)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
