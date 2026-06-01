"""Spec 38 — International Admissions (institution processing) service.

Owns the per-application ``international_processing`` record and the operations
around it: credential normalization, English-proficiency / waiver evaluation,
country-requirement packs, immigration-document (I-20 / DS-2019) generation, and
visa-interview tracking.

Two invariants run through this module:
- **Fairness (§3 / §9 / 46 §6):** visa / immigration status is operational only.
  Nothing here feeds matching or ranking; the fairness contract test asserts the
  match feature builder never reads these fields.
- **AI never decides (§5):** the two agents (CredentialNormalizer,
  CountryRequirementAdvisor) only structure data for a human and always fall back
  to deterministic logic — the service never raises on AI failure.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.country_requirement_advisor import advise_country_pack, default_pack_for
from unipaith.ai.credential_normalizer import deterministic_normalize, normalize_credential
from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException, UnprocessableEntityException
from unipaith.models.application import Application, EnrollmentRecord
from unipaith.models.institution import Institution, Program
from unipaith.models.international import CountryRequirementPack, InternationalProcessing
from unipaith.models.student import StudentProfile
from unipaith.services.audit_service import AuditService

# The Spec-35 "enrollment intent confirmed" set — the I-20 gate (admit + intent).
_CONFIRMED_ENROLLMENT_STATES = {
    "intent_confirmed",
    "deposit_recorded",
    "enrollment_confirmed",
    "enrolled",
}
# Decisions that count as an admit for immigration-document issuance (§2.4).
_ADMITTED_DECISIONS = {"admitted", "accepted", "conditional_admission"}

# English-proficiency waiver — native-English-speaking countries (Spec 38 §2.2).
# Matched case-insensitively against nationality / country name or ISO-2 code.
_NATIVE_ENGLISH = {
    "US",
    "UNITED STATES",
    "USA",
    "GB",
    "UK",
    "UNITED KINGDOM",
    "ENGLAND",
    "SCOTLAND",
    "WALES",
    "IE",
    "IRELAND",
    "AU",
    "AUSTRALIA",
    "NZ",
    "NEW ZEALAND",
    "CA",
    "CANADA",
}

# Fields a PATCH may set directly on the processing row. Immigration-document and
# SEVIS fields are intentionally excluded — they move only via generate().
_EDITABLE_FIELDS = {
    "credential_provider",
    "credential_status",
    "credential_report_ref",
    "credential_normalized_gpa",
    "credential_source_scale",
    "credential_notes",
    "english_test",
    "english_score",
    "english_meets_minimum",
    "english_waiver_eligible",
    "english_waiver_basis",
    "country_requirements",
    "visa_appointment_at",
    "visa_consulate",
    "visa_outcome",
}

_VALID_COUNTRY_REQ_STATUS = {"pending", "received", "verified", "waived"}


def _norm_country(value: str | None) -> str:
    return (value or "").strip().upper()


def _fmt_gpa(value: Decimal | float | str | None) -> str | None:
    """Format a 4.0-scale GPA for display — strips a single trailing zero so a
    persisted Numeric(4,2) ``3.60`` reads back as ``3.6`` (Spec 38 §10 copy:
    "Normalized GPA: 3.6 (from 85/100)") while keeping ``3.33`` intact."""
    if value is None:
        return None
    s = format(Decimal(str(value)).quantize(Decimal("0.01")), "f")  # e.g. "3.60"
    if "." in s and s.endswith("0"):
        s = s[:-1]  # "3.6" (keeps "4.0", "3.3"; leaves "3.33")
    return s


def _display_name(profile: StudentProfile | None, student_id: uuid.UUID) -> str:
    if profile:
        full = f"{(profile.first_name or '').strip()} {(profile.last_name or '').strip()}".strip()
        if full:
            return full
    return f"Applicant {str(student_id)[:8]}"


def _is_native_english_country(*values: str | None) -> bool:
    return any(_norm_country(v) in _NATIVE_ENGLISH for v in values if v)


class InternationalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── loading + ownership ─────────────────────────────────────────────────
    async def _load_app(
        self, application_id: uuid.UUID, institution_id: uuid.UUID
    ) -> tuple[Application, Program]:
        app = (
            await self.db.execute(select(Application).where(Application.id == application_id))
        ).scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")
        program = (
            await self.db.execute(select(Program).where(Program.id == app.program_id))
        ).scalar_one_or_none()
        if not program or program.institution_id != institution_id:
            raise NotFoundException("Application not found for this institution")
        return app, program

    async def _load_profile(self, student_id: uuid.UUID) -> StudentProfile | None:
        return (
            await self.db.execute(
                select(StudentProfile)
                .where(StudentProfile.id == student_id)
                .options(
                    selectinload(StudentProfile.academic_records),
                    selectinload(StudentProfile.test_scores),
                    selectinload(StudentProfile.languages),
                    selectinload(StudentProfile.visa_info),
                )
            )
        ).scalar_one_or_none()

    async def _get_record(self, application_id: uuid.UUID) -> InternationalProcessing | None:
        return (
            await self.db.execute(
                select(InternationalProcessing).where(
                    InternationalProcessing.application_id == application_id
                )
            )
        ).scalar_one_or_none()

    # ── domestic / international classification (§6) ─────────────────────────
    @staticmethod
    def is_international(profile: StudentProfile | None, institution: Institution | None) -> bool:
        """Whether the applicant needs international processing. Conservative —
        an explicit ``visa_required`` always counts; otherwise nationality (or
        residence) differing from the institution's country counts."""
        if profile is None:
            return False
        visa = getattr(profile, "visa_info", None)
        if visa is not None and bool(getattr(visa, "visa_required", False)):
            return True
        if visa is not None and getattr(visa, "work_authorization_needed", False):
            return True
        inst_country = _norm_country(getattr(institution, "country", None)) if institution else ""
        if not inst_country:
            # Without an institution country we can't compare; fall back to the
            # presence of a non-domestic nationality signal.
            return bool(getattr(profile, "passport_issuing_country", None))
        nationality = _norm_country(profile.nationality)
        residence = _norm_country(getattr(profile, "country_of_residence", None))
        # Treat common US aliases as equivalent.
        us_aliases = {"US", "USA", "UNITED STATES", "UNITED STATES OF AMERICA"}
        same = inst_country in us_aliases

        def _domestic(value: str) -> bool:
            return value == inst_country or (same and value in us_aliases)

        if nationality and not _domestic(nationality):
            return True
        if residence and not _domestic(residence):
            return True
        return False

    # ── read-only student inputs the reviewer sees beside the editable record ─
    @staticmethod
    def _best_academic(profile: StudentProfile | None) -> Any | None:
        if not profile or not profile.academic_records:
            return None
        # Prefer a completed record with a GPA, latest end_date first.
        scored = [r for r in profile.academic_records if r.gpa is not None]
        if not scored:
            scored = list(profile.academic_records)
        return sorted(
            scored,
            key=lambda r: (r.end_date is not None, r.end_date or _epoch_date()),
            reverse=True,
        )[0]

    @staticmethod
    def _student_inputs(profile: StudentProfile | None) -> dict:
        visa = getattr(profile, "visa_info", None) if profile else None
        acad = InternationalService._best_academic(profile)
        english_tests = []
        for s in (profile.test_scores or []) if profile else []:
            t = (getattr(s, "test_type", "") or "").upper()
            if t in {"TOEFL", "IELTS", "DET", "DUOLINGO", "PTE"}:
                english_tests.append(
                    {
                        "test": "DET" if t == "DUOLINGO" else t,
                        "score": str(s.total_score) if getattr(s, "total_score", None) else None,
                    }
                )
        return {
            "nationality": getattr(profile, "nationality", None) if profile else None,
            "country_of_birth": getattr(profile, "place_of_birth", None) if profile else None,
            "country_of_residence": getattr(profile, "country_of_residence", None)
            if profile
            else None,
            "passport_issuing_country": getattr(profile, "passport_issuing_country", None)
            if profile
            else None,
            "raw_gpa": str(acad.gpa) if acad and acad.gpa is not None else None,
            "gpa_scale": getattr(acad, "gpa_scale", None) if acad else None,
            "grading_scale_type": getattr(acad, "grading_scale_type", None) if acad else None,
            "academic_country": getattr(acad, "country", None) if acad else None,
            "degree_type": getattr(acad, "degree_type", None) if acad else None,
            "self_reported_normalized_gpa": str(acad.normalized_gpa)
            if acad and getattr(acad, "normalized_gpa", None) is not None
            else None,
            "student_credential_eval_status": getattr(acad, "credential_evaluation_status", None)
            if acad
            else None,
            "credential_report_url": getattr(acad, "credential_evaluation_report_url", None)
            if acad
            else None,
            "english_test_scores": english_tests,
            # High-sensitivity (§7 / 46) — financial proof for the I-20 gate.
            "financial_proof_available": bool(getattr(visa, "financial_proof_available", False))
            if visa
            else False,
            "financial_proof_amount_band": getattr(visa, "financial_proof_amount_band", None)
            if visa
            else None,
            "sponsorship_source": getattr(visa, "sponsorship_source", None) if visa else None,
        }

    # ── get_or_init + serialize ─────────────────────────────────────────────
    async def get_or_init(
        self, institution_id: uuid.UUID, application_id: uuid.UUID, *, create: bool = True
    ) -> dict:
        app, program = await self._load_app(application_id, institution_id)
        profile = await self._load_profile(app.student_id)
        institution = (
            await self.db.execute(select(Institution).where(Institution.id == institution_id))
        ).scalar_one_or_none()
        is_intl = self.is_international(profile, institution)

        record = await self._get_record(application_id)
        if record is None and create and is_intl:
            inputs = self._student_inputs(profile)
            # Auto-attach the default country-requirement pack (§2.3).
            pack = default_pack_for(
                _country_code_from(inputs.get("nationality") or inputs.get("country_of_birth")),
                inputs.get("nationality"),
            )
            record = InternationalProcessing(
                application_id=application_id,
                institution_id=institution_id,
                credential_status="none",
                immigration_doc_status="not_started",
                country_requirements=[
                    {"item": r["item"], "status": "pending"} for r in pack["requirements"]
                ],
            )
            self.db.add(record)
            await self.db.flush()
            await self.db.refresh(record)

        return self._serialize(app, program, profile, institution, record, is_intl)

    def _serialize(
        self,
        app: Application,
        program: Program,
        profile: StudentProfile | None,
        institution: Institution | None,
        record: InternationalProcessing | None,
        is_international: bool,
    ) -> dict:
        inputs = self._student_inputs(profile)
        english_policy = program.english_policy if isinstance(program.english_policy, dict) else {}
        gate = self._immigration_gate(app, inputs)
        record_dict = _record_to_dict(record) if record else None
        feasibility = self._feasibility_band(record, inputs)
        return {
            "application_id": str(app.id),
            "institution_id": str(institution.id) if institution else None,
            "is_international": is_international,
            "student": {
                "display_name": _display_name(profile, app.student_id),
                "name_in_native_script": getattr(profile, "name_in_native_script", None)
                if profile
                else None,
                "date_of_birth": profile.date_of_birth.isoformat()
                if profile and profile.date_of_birth
                else None,
            },
            "program": {
                "id": str(program.id),
                "program_name": program.program_name,
                "degree_type": program.degree_type,
                "english_policy": english_policy or None,
            },
            "decision": app.decision,
            "student_inputs": inputs,
            "processing": record_dict,
            "immigration_gate": gate,
            "feasibility": feasibility,
            # §2.2 — auto-suggested English waiver; the reviewer confirms it.
            "english_waiver_suggestion": self.english_waiver_eligibility(profile, program),
        }

    async def packet_summary(
        self,
        app: Application,
        program: Program,
        profile: StudentProfile | None,
        institution: Institution | None,
    ) -> dict:
        """Compact read-only signal block for the Spec-32 review packet (§3).

        Surfaces credential-eval status, normalized GPA, English result,
        country-requirement completeness, immigration-doc status, and the
        feasibility band — plus ``is_international`` so the UI hides the tab for
        domestic applicants. Operational only: fairness_note states the contract
        that none of this is a selection criterion (§3 / §9 / 46 §6)."""
        record = await self._get_record(app.id)
        inputs = self._student_inputs(profile)
        is_intl = self.is_international(profile, institution)
        reqs = (record.country_requirements if record else None) or []
        done = sum(
            1
            for r in reqs
            if isinstance(r, dict) and r.get("status") in {"received", "verified", "waived"}
        )
        gate = self._immigration_gate(app, inputs)
        english = None
        if record:
            english = {
                "test": record.english_test,
                "score": str(record.english_score) if record.english_score is not None else None,
                "meets_minimum": record.english_meets_minimum,
                "waiver_eligible": record.english_waiver_eligible,
            }
        return {
            "is_international": is_intl,
            "credential_status": record.credential_status if record else None,
            "normalized_gpa": _fmt_gpa(record.credential_normalized_gpa) if record else None,
            "raw_gpa": inputs.get("raw_gpa"),
            "english": english,
            "country_requirements": {"complete": done, "total": len(reqs)},
            "immigration_doc_status": record.immigration_doc_status if record else "not_started",
            "immigration_can_generate": gate["can_generate"],
            "feasibility": self._feasibility_band(record, inputs),
            "fairness_note": (
                "Visa and immigration status inform feasibility and yield "
                "planning only — never a selection criterion."
            ),
        }

    # ── credential normalization (§2.1) ─────────────────────────────────────
    async def normalize_gpa(
        self,
        institution_id: uuid.UUID,
        application_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        *,
        raw_gpa: Decimal | float | None = None,
        scale_hint: str | None = None,
        country: str | None = None,
    ) -> dict:
        app, program = await self._load_app(application_id, institution_id)
        profile = await self._load_profile(app.student_id)
        inputs = self._student_inputs(profile)
        # Use explicit args, else the student's reported academic record.
        if raw_gpa is None and inputs.get("raw_gpa"):
            raw_gpa = Decimal(inputs["raw_gpa"])
        scale_hint = scale_hint or inputs.get("grading_scale_type") or inputs.get("gpa_scale")
        country = country or inputs.get("academic_country") or inputs.get("nationality")
        if raw_gpa is None:
            raise UnprocessableEntityException(
                {"message": "No GPA on file to normalize.", "missing_fields": ["raw_gpa"]}
            )

        normalized, source = deterministic_normalize(
            raw_gpa, scale_hint=scale_hint, country=country
        )
        ai_used = False
        note = None
        if settings.ai_international_v2_enabled:
            ai = await normalize_credential(
                raw_gpa=raw_gpa,
                scale_hint=scale_hint,
                country=country,
                degree_type=inputs.get("degree_type"),
            )
            if ai and ai.get("normalized_gpa") is not None:
                normalized = ai["normalized_gpa"]
                source = ai.get("source_scale") or source
                note = ai.get("course_map_note")
                ai_used = True

        record = await self._ensure_record(app, institution_id)
        record.credential_normalized_gpa = normalized
        record.credential_source_scale = source
        if note:
            record.credential_notes = note
        await self.db.flush()
        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            action="credential_normalize",
            entity_type="international_processing",
            entity_id=str(record.id),
            application_id=application_id,
            description=f"Normalized GPA {normalized} from {source}",
            new_value={"normalized_gpa": str(normalized), "source_scale": source},
            actor_role="ai_agent" if ai_used else None,
        )
        return {
            "normalized_gpa": _fmt_gpa(normalized),
            "source_scale": source,
            "raw_gpa": str(raw_gpa),
            "course_map_note": note,
            "ai_used": ai_used,
        }

    # ── English-proficiency waiver (§2.2) ────────────────────────────────────
    def english_waiver_eligibility(
        self, profile: StudentProfile | None, program: Program | None
    ) -> dict:
        policy = (
            program.english_policy if program and isinstance(program.english_policy, dict) else {}
        )
        # 1) Native-English-country rule (always applies).
        nationality = getattr(profile, "nationality", None) if profile else None
        birth = getattr(profile, "place_of_birth", None) if profile else None
        if _is_native_english_country(nationality, birth):
            return {
                "eligible": True,
                "basis": "Citizen of an English-speaking country",
            }
        # 2) Prior-degree-in-English rule (only if the program enables it).
        if policy.get("waiver_prior_degree_in_english", True):
            for r in (profile.academic_records or []) if profile else []:
                lang = (getattr(r, "transcript_language", None) or "").strip().lower()
                if lang in {"english", "en"}:
                    return {
                        "eligible": True,
                        "basis": "Prior degree completed in English",
                    }
        # 3) Program-configured extra waiver countries.
        for code in policy.get("waiver_native_english_countries", []) or []:
            if _norm_country(nationality) == _norm_country(code):
                return {"eligible": True, "basis": "Country on the program waiver list"}
        return {"eligible": False, "basis": None}

    # ── institution-wide international queue (§0 — /i/admissions?tab=international) ─
    async def list_applicants(self, institution_id: uuid.UUID) -> list[dict]:
        """All international applicants across the institution's programs with a
        compact processing summary, for the admissions overview tab. Read-only —
        creates no records. Domestic applicants are excluded (§6)."""
        institution = (
            await self.db.execute(select(Institution).where(Institution.id == institution_id))
        ).scalar_one_or_none()
        prog_rows = (
            await self.db.execute(
                select(Program.id, Program.program_name).where(
                    Program.institution_id == institution_id
                )
            )
        ).all()
        if not prog_rows:
            return []
        prog_name = {p.id: p.program_name for p in prog_rows}
        prog_ids = list(prog_name.keys())
        apps = list(
            (
                await self.db.execute(
                    select(Application).where(Application.program_id.in_(prog_ids))
                )
            ).scalars()
        )
        if not apps:
            return []
        student_ids = list({a.student_id for a in apps})
        profiles = {
            p.id: p
            for p in (
                await self.db.execute(
                    select(StudentProfile)
                    .where(StudentProfile.id.in_(student_ids))
                    .options(
                        selectinload(StudentProfile.visa_info),
                        selectinload(StudentProfile.academic_records),
                        selectinload(StudentProfile.test_scores),
                    )
                )
            ).scalars()
        }
        records = {
            r.application_id: r
            for r in (
                await self.db.execute(
                    select(InternationalProcessing).where(
                        InternationalProcessing.application_id.in_([a.id for a in apps])
                    )
                )
            ).scalars()
        }
        out: list[dict] = []
        for a in apps:
            profile = profiles.get(a.student_id)
            if not self.is_international(profile, institution):
                continue
            record = records.get(a.id)
            inputs = self._student_inputs(profile)
            reqs = (record.country_requirements if record else None) or []
            done = sum(
                1
                for r in reqs
                if isinstance(r, dict) and r.get("status") in {"received", "verified", "waived"}
            )
            out.append(
                {
                    "application_id": str(a.id),
                    "student_name": _display_name(profile, a.student_id),
                    "program_name": prog_name.get(a.program_id),
                    "nationality": inputs.get("nationality"),
                    "status": a.status,
                    "decision": a.decision,
                    "credential_status": record.credential_status if record else "none",
                    "normalized_gpa": (
                        _fmt_gpa(record.credential_normalized_gpa) if record else None
                    ),
                    "english_meets_minimum": record.english_meets_minimum if record else None,
                    "country_requirements": {"complete": done, "total": len(reqs)},
                    "immigration_doc_status": record.immigration_doc_status
                    if record
                    else "not_started",
                    "feasibility": self._feasibility_band(record, inputs)["band"],
                }
            )
        return sorted(out, key=lambda r: r["student_name"])

    # ── country-requirement packs (§2.3) ────────────────────────────────────
    async def list_country_requirements(self, institution_id: uuid.UUID) -> list[dict]:
        """Platform defaults merged with this institution's overrides."""
        overrides = {
            (row.country_code or "").upper(): row
            for row in (
                await self.db.execute(
                    select(CountryRequirementPack).where(
                        CountryRequirementPack.institution_id == institution_id,
                        CountryRequirementPack.is_active.is_(True),
                    )
                )
            ).scalars()
        }
        packs: list[dict] = []
        from unipaith.ai.country_requirement_advisor import DEFAULT_COUNTRY_PACKS

        seen = set()
        for code, base in DEFAULT_COUNTRY_PACKS.items():
            ov = overrides.get(code)
            if ov is not None:
                packs.append(
                    {
                        "country_code": code,
                        "country_name": ov.country_name,
                        "requirements": ov.requirements or [],
                        "source": "institution",
                    }
                )
            else:
                packs.append(
                    {
                        "country_code": code,
                        "country_name": base["country_name"],
                        "requirements": base["requirements"],
                        "source": "platform_default",
                    }
                )
            seen.add(code)
        # Institution overrides for countries without a platform default.
        for code, ov in overrides.items():
            if code not in seen:
                packs.append(
                    {
                        "country_code": code,
                        "country_name": ov.country_name,
                        "requirements": ov.requirements or [],
                        "source": "institution",
                    }
                )
        return sorted(packs, key=lambda p: p["country_name"])

    async def suggest_country_pack(
        self,
        institution_id: uuid.UUID,
        application_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
    ) -> dict:
        app, program = await self._load_app(application_id, institution_id)
        profile = await self._load_profile(app.student_id)
        inputs = self._student_inputs(profile)
        country_name = inputs.get("nationality") or inputs.get("country_of_birth")
        code = _country_code_from(country_name)
        pack = default_pack_for(code, country_name)
        ai_used = False
        if settings.ai_international_v2_enabled:
            ai = await advise_country_pack(
                country_code=code, country_name=country_name, degree_type=inputs.get("degree_type")
            )
            if ai and ai.get("requirements"):
                pack = {
                    "country_code": code,
                    "country_name": ai.get("country_name") or country_name or code,
                    "requirements": ai["requirements"],
                }
                ai_used = True
        items = [{"item": r["item"], "status": "pending"} for r in pack["requirements"]]
        record = await self._ensure_record(app, institution_id)
        record.country_requirements = items
        await self.db.flush()
        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            action="country_pack_attach",
            entity_type="international_processing",
            entity_id=str(record.id),
            application_id=application_id,
            description=f"Attached {len(items)} country requirement(s) for {pack['country_name']}",
            actor_role="ai_agent" if ai_used else None,
        )
        return {
            "country_name": pack["country_name"],
            "requirements": items,
            "ai_used": ai_used,
        }

    # ── update (§4 PATCH) ────────────────────────────────────────────────────
    async def update(
        self,
        institution_id: uuid.UUID,
        application_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        patch: dict,
    ) -> dict:
        app, program = await self._load_app(application_id, institution_id)
        record = await self._ensure_record(app, institution_id)
        changed: dict[str, Any] = {}
        for key, value in patch.items():
            if key not in _EDITABLE_FIELDS or value is None:
                continue
            if key == "country_requirements" and isinstance(value, list):
                value = [
                    {
                        "item": str(it.get("item", "")).strip(),
                        "status": it.get("status")
                        if it.get("status") in _VALID_COUNTRY_REQ_STATUS
                        else "pending",
                    }
                    for it in value
                    if isinstance(it, dict) and it.get("item")
                ]
            if key == "credential_normalized_gpa":
                value = Decimal(str(value))
            if key == "english_score":
                value = Decimal(str(value))
            if key in {"visa_appointment_at"} and isinstance(value, str):
                value = _parse_dt(value)
            setattr(record, key, value)
            changed[key] = str(value)
        await self.db.flush()
        if changed:
            await AuditService(self.db).log(
                institution_id=institution_id,
                actor_user_id=actor_user_id,
                action="international_update",
                entity_type="international_processing",
                entity_id=str(record.id),
                application_id=application_id,
                description=f"Updated international processing ({', '.join(sorted(changed))})",
                new_value=changed,
            )
        profile = await self._load_profile(app.student_id)
        institution = (
            await self.db.execute(select(Institution).where(Institution.id == institution_id))
        ).scalar_one_or_none()
        return self._serialize(
            app, program, profile, institution, record, self.is_international(profile, institution)
        )

    # ── immigration document generation (§2.4) ───────────────────────────────
    def _immigration_gate(self, app: Application, inputs: dict) -> dict:
        """Whether an I-20/DS-2019 can be issued: admit + enrollment intent +
        financial proof. Returns can_generate + the list of blockers (§6)."""
        blockers: list[dict] = []
        if (app.decision or "").lower() not in _ADMITTED_DECISIONS:
            blockers.append(
                {
                    "field": "decision",
                    "message": "Applicant must be admitted before issuing an immigration document.",
                }
            )
        if not inputs.get("financial_proof_available"):
            blockers.append(
                {
                    "field": "financial_proof_available",
                    "message": "Financial proof required before issuing.",
                }
            )
        return {"can_generate": len(blockers) == 0, "blockers": blockers}

    async def generate_immigration_doc(
        self,
        institution_id: uuid.UUID,
        application_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        *,
        doc_type: str = "I-20",
    ) -> dict:
        app, program = await self._load_app(application_id, institution_id)
        profile = await self._load_profile(app.student_id)
        institution = (
            await self.db.execute(select(Institution).where(Institution.id == institution_id))
        ).scalar_one_or_none()
        inputs = self._student_inputs(profile)

        if doc_type not in {"I-20", "DS-2019"}:
            raise UnprocessableEntityException(
                {"message": "Unsupported document type.", "missing_fields": ["doc_type"]}
            )

        # Gate: admit + enrollment intent + financial proof (§6).
        gate = self._immigration_gate(app, inputs)
        missing = [b["field"] for b in gate["blockers"]]
        enrollment = (
            await self.db.execute(
                select(EnrollmentRecord).where(EnrollmentRecord.application_id == application_id)
            )
        ).scalar_one_or_none()
        intent_confirmed = (
            enrollment is not None and enrollment.state in _CONFIRMED_ENROLLMENT_STATES
        )
        if not intent_confirmed:
            missing.append("enrollment_intent")
            gate["blockers"].append(
                {
                    "field": "enrollment_intent",
                    "message": "Applicant must confirm enrollment intent before issuing.",
                }
            )
        if missing:
            raise UnprocessableEntityException(
                {
                    "message": "Financial proof required before issuing."
                    if "financial_proof_available" in missing
                    else "This applicant is not ready for an immigration document.",
                    "missing_fields": gate["blockers"],
                }
            )

        sevis_export = self._build_sevis_export(
            app, program, institution, profile, inputs, doc_type
        )
        record = await self._ensure_record(app, institution_id)
        record.immigration_doc_type = doc_type
        record.immigration_doc_status = "drafted"
        record.sevis_id = record.sevis_id or _mint_sevis_id()
        record.immigration_issued_at = datetime.now(UTC)
        record.sevis_export = sevis_export
        await self.db.flush()
        # High-sensitivity action — always audit-logged (§2.4 / 36 / 46).
        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            action="immigration_doc_generate",
            entity_type="international_processing",
            entity_id=str(record.id),
            application_id=application_id,
            description=f"Generated {doc_type} (SEVIS {record.sevis_id})",
            new_value={"doc_type": doc_type, "sevis_id": record.sevis_id, "status": "drafted"},
        )
        return {
            "doc_type": doc_type,
            "status": record.immigration_doc_status,
            "sevis_id": record.sevis_id,
            "issued_at": record.immigration_issued_at.isoformat(),
            "sevis_export": sevis_export,
        }

    def _build_sevis_export(
        self,
        app: Application,
        program: Program,
        institution: Institution | None,
        profile: StudentProfile | None,
        inputs: dict,
        doc_type: str,
    ) -> dict:
        """A SEVIS-batch-compatible field map the institution uploads itself
        (no direct SEVIS API in this phase, §2.4 / §8)."""
        est_cost = None
        if isinstance(program.cost_data, dict):
            est_cost = program.cost_data.get("total_estimated_cost") or program.cost_data.get(
                "annual_cost"
            )
        return {
            "form_type": doc_type,
            "visa_class": "F-1" if doc_type == "I-20" else "J-1",
            "school": {
                "name": institution.name if institution else None,
                "country": institution.country if institution else None,
                # School/program SEVIS codes are configured by the DSO; left blank
                # for the institution to fill before upload.
                "sevis_school_code": None,
                "program_code": None,
            },
            "student": {
                "family_name": profile.last_name if profile else None,
                "given_name": profile.first_name if profile else None,
                "name_in_native_script": getattr(profile, "name_in_native_script", None)
                if profile
                else None,
                "date_of_birth": profile.date_of_birth.isoformat()
                if profile and profile.date_of_birth
                else None,
                "country_of_birth": inputs.get("country_of_birth"),
                "country_of_citizenship": inputs.get("nationality"),
            },
            "program": {
                "program_name": program.program_name,
                "degree_level": program.degree_type,
                "start_date": program.program_start_date.isoformat()
                if program.program_start_date
                else None,
                "education_level": program.degree_type,
            },
            "financials": {
                "estimated_cost": est_cost,
                "funding_source": inputs.get("sponsorship_source"),
                "financial_proof_amount_band": inputs.get("financial_proof_amount_band"),
                "financial_proof_on_file": inputs.get("financial_proof_available"),
            },
            "generated_for_application_id": str(app.id),
        }

    # ── feasibility band (operational only — never a ranking input, §3) ──────
    @staticmethod
    def _feasibility_band(record: InternationalProcessing | None, inputs: dict) -> dict:
        """Mirror of the student's ``visa_feasibility_band`` (42 §4.3), derived
        for the institution's operational planning. NEVER fed into matching."""
        reasons: list[str] = []
        score = 2  # 0 blocked · 1 at_risk · 2 moderate · 3 strong
        if record and record.visa_outcome == "approved":
            return {"band": "strong", "reasons": ["Visa approved"]}
        if record and record.visa_outcome == "denied":
            return {"band": "blocked", "reasons": ["Visa denied — consider offer deferral"]}
        if not inputs.get("financial_proof_available"):
            score -= 1
            reasons.append("Financial proof not yet on file")
        if record and record.credential_status in {"verified", "received"}:
            score += 1
            reasons.append("Credential evaluation in hand")
        elif record and record.credential_status in {"none", "requested"}:
            reasons.append("Credential evaluation pending")
        if record and record.english_meets_minimum is True:
            score += 1
            reasons.append("English proficiency met")
        elif (
            record
            and record.english_meets_minimum is False
            and not (record.english_waiver_eligible)
        ):
            score -= 1
            reasons.append("English minimum not met")
        bands = {0: "blocked", 1: "at_risk", 2: "moderate", 3: "strong"}
        return {
            "band": bands.get(max(0, min(3, score)), "moderate"),
            "reasons": reasons or ["Standard processing"],
        }

    # ── helpers ──────────────────────────────────────────────────────────────
    async def _ensure_record(
        self, app: Application, institution_id: uuid.UUID
    ) -> InternationalProcessing:
        record = await self._get_record(app.id)
        if record is None:
            record = InternationalProcessing(
                application_id=app.id,
                institution_id=institution_id,
                credential_status="none",
                immigration_doc_status="not_started",
            )
            self.db.add(record)
            await self.db.flush()
            await self.db.refresh(record)
        return record


# ── module helpers ───────────────────────────────────────────────────────────
def _epoch_date():
    from datetime import date

    return date(1900, 1, 1)


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _mint_sevis_id() -> str:
    # Placeholder SEVIS identifier (real IDs come from SEVIS on upload). N + 10 digits.
    return "N" + str(uuid.uuid4().int)[:10]


# Minimal country-name → ISO-2 map for the common international source countries
# (matches the default packs). Falls back to the first two letters uppercased.
_COUNTRY_NAME_TO_CODE = {
    "CHINA": "CN",
    "PEOPLE'S REPUBLIC OF CHINA": "CN",
    "INDIA": "IN",
    "NIGERIA": "NG",
    "BRAZIL": "BR",
    "UNITED KINGDOM": "GB",
    "UK": "GB",
    "ENGLAND": "GB",
    "UNITED STATES": "US",
    "USA": "US",
    "SOUTH KOREA": "KR",
    "KOREA": "KR",
    "VIETNAM": "VN",
    "PAKISTAN": "PK",
    "CANADA": "CA",
    "MEXICO": "MX",
    "GERMANY": "DE",
    "FRANCE": "FR",
}


def _country_code_from(country: str | None) -> str | None:
    if not country:
        return None
    key = country.strip().upper()
    if key in _COUNTRY_NAME_TO_CODE:
        return _COUNTRY_NAME_TO_CODE[key]
    if len(key) == 2:
        return key
    return key[:2]


def _record_to_dict(r: InternationalProcessing) -> dict:
    return {
        "id": str(r.id),
        "credential_eval": {
            "provider": r.credential_provider,
            "status": r.credential_status,
            "report_ref": r.credential_report_ref,
            "normalized_gpa": _fmt_gpa(r.credential_normalized_gpa),
            "source_scale": r.credential_source_scale,
            "notes": r.credential_notes,
        },
        "english_proficiency": {
            "test": r.english_test,
            "score": str(r.english_score) if r.english_score is not None else None,
            "meets_minimum": r.english_meets_minimum,
            "waiver": {"eligible": r.english_waiver_eligible, "basis": r.english_waiver_basis},
        },
        "country_requirements": r.country_requirements or [],
        "immigration_doc": {
            "type": r.immigration_doc_type,
            "status": r.immigration_doc_status,
            "sevis_id": r.sevis_id,
            "issued_at": r.immigration_issued_at.isoformat() if r.immigration_issued_at else None,
            "sevis_export": r.sevis_export,
        },
        "visa": {
            "appointment_at": r.visa_appointment_at.isoformat() if r.visa_appointment_at else None,
            "consulate": r.visa_consulate,
            "outcome": r.visa_outcome,
        },
    }
