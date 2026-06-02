"""Spec 51 — the consolidated data model, with the table map derived LIVE.

The domain grouping, the per-table notes and the §7/§8 narrative are authored
from spec 51. The **table list, counts, columns, foreign keys and JSONB / vector
flags are introspected from the running SQLAlchemy metadata** (``Base.metadata``)
— so this surface can never claim a table the deployed schema doesn't have, and
it automatically corrects the doc where the build has moved on.

Two corrections fall straight out of reading the live schema (same shape as the
api-contract's 285→553 route drift):

- Spec 51 was drafted at **107 tables**; the live schema has more (specs 39–50
  and the ML / knowledge subsystems landed after the doc).
- Spec 51 §8 listed ``payments`` and the behavioral layer as *not built*; several
  now exist (spec 39 fees, spec 42 story-bank). The §8 list below computes each
  one's live presence, so the page shows exactly what the doc got overtaken on.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

# Spec 51 was drafted at 107 tables / 23 model files (2026-05-30). Surfaced so the
# page shows the doc-vs-live correction, the running schema being the truth.
DOC_CLAIMED_TABLES = 107
DOC_CLAIMED_MODEL_FILES = 23


# ── Domain grouping (spec 51 §2–§6) ─────────────────────────────────────────
# Each live model module is assigned to one of the five domains the doc uses.
# The grouping is authored; the membership and counts are computed from the live
# table → module map, so every deployed table lands in exactly one domain.
@dataclass(frozen=True)
class Domain:
    key: str
    title: str
    section: str  # the spec 51 section
    spec: str
    blurb: str
    modules: tuple[str, ...]


DOMAINS: tuple[Domain, ...] = (
    Domain(
        "profile",
        "Student identity & profile",
        "§2",
        "08 · 42 · 43",
        "The profile is fully relational — a hub row plus a real table per domain "
        "(academics, tests, activities, research, work, languages …), not a JSONB "
        "dump. Goals, needs, identity, strategy and the behavioral signal layer sit "
        "alongside it.",
        (
            "user",
            "student",
            "goals",
            "needs",
            "identity",
            "strategy",
            "major_specific",
            "prompt_library",
        ),
    ),
    Domain(
        "matching_ai",
        "Discovery, matching & AI artifacts",
        "§3",
        "09 · 19 · 45 · 06",
        "The Stage-1 discovery dialogue, the dual-score match results and their "
        "cached rationales, plus the ML / matching substrate — feature vectors, "
        "embeddings, the model registry and the AI audit ledger.",
        ("discovery", "matching", "ai_artifacts", "confidence_outcome"),
    ),
    Domain(
        "application",
        "Application lifecycle",
        "§4",
        "15 · 18 · 32 · 33 · 34 · 35",
        "From a started application through its adaptive checklist, the review "
        "packet and rubric scores, interviews, the offer letter and enrollment — "
        "one connected lifecycle.",
        ("application",),
    ),
    Domain(
        "institution",
        "Institution & engagement",
        "§5",
        "22 · 23 · 25–29 · 38–41",
        "The institution profile, its programs and intake rounds, the outreach "
        "stack (segments, campaigns, posts, events), messaging, recruitment CRM, "
        "international and graduate tooling, payments and saved lists.",
        (
            "institution",
            "engagement",
            "attribution",
            "recruitment",
            "intake",
            "international",
            "graduate",
            "peer",
            "follow",
            "settings",
            "billing",
            "payment",
        ),
    ),
    Domain(
        "platform",
        "Notifications, audit, ML-loop & knowledge",
        "§6",
        "21 · 36 · 46 · 06",
        "The cross-cutting spine: notifications, the append-only audit logs, the "
        "feedback-only workshop runs, the fairness harness, the full ML learning "
        "loop and the knowledge / crawler subsystem.",
        (
            "workflow",
            "audit",
            "admin_audit_event",
            "workshops",
            "ai_feedback",
            "fairness",
            "ml_loop",
            "pipeline",
            "knowledge",
        ),
    ),
)

_DOMAIN_BY_MODULE: dict[str, str] = {m: d.key for d in DOMAINS for m in d.modules}


# ── Per-table notes (spec 51 §2–§6, keyed on the LIVE table name) ───────────
# A table without a note still renders, grouped by domain with its computed
# stats; the note just adds the doc's colour for the tables it calls out.
TABLE_NOTES: dict[str, tuple[str, str]] = {
    # §2 — profile
    "users": ("05", "Unified identity — students and institution staff."),
    "student_profiles": ("08", "The hub; FK target for almost every student table."),
    "academic_records": ("42", "Per-school academic history — a real table, not JSONB."),
    "student_courses": ("42", "Per-course rows."),
    "test_scores": ("42", "Standardized tests."),
    "activities": ("42", "Activities / leadership."),
    "student_competitions": ("42", "Competitions."),
    "student_research": ("42", "Research experience."),
    "student_work_experiences": ("42", "Work experience."),
    "student_portfolio_items": ("42", "Portfolio."),
    "student_languages": ("42", "Languages."),
    "student_online_presence": ("42", "LinkedIn / GitHub / site links."),
    "student_visa_info": ("42 §3.3", "International applicants."),
    "student_accommodations": ("42 §3.2", "Accessibility / accommodations."),
    "student_scheduling": ("42", "Availability."),
    "student_data_consent": (
        "46 §2",
        "The 4-lever consent record — consent IS built, not implicit.",
    ),
    "student_goals": ("08", "SMART goals; source = discovery | manual, provenance-checked."),
    "student_needs": (
        "08",
        "Maslow-keyed; severity ∈ must_have | strong_preference | nice_to_have.",
    ),
    "student_identity": ("08 · 19", "core_values / worldview / self_awareness + identity_summary."),
    "student_strategies": ("09", "Versioned; one active strategy per student."),
    "onboarding_progress": ("05 §11", "First-run state."),
    "recommendation_requests": ("08", "Recommenders."),
    "student_major_specific_signals": (
        "43",
        "Per-discipline major readiness — supersedes the dropped student_major_readiness scaffold.",
    ),
    "behavioral_prompts": ("42", "Behavioral Prompt Library catalog."),
    "student_behavioral_responses": (
        "42 §3.19",
        "Behavioral responses — §8 once listed this absent; now live.",
    ),
    "student_stories": ("42 §3.20", "Story bank — §8 once listed this absent; now live."),
    # §3 — discovery / matching / AI
    "discovery_sessions": ("19", "Stage-1 chat per track (profile|goals|needs) × layer."),
    "discovery_messages": (
        "19 · 44",
        "Append-only; extracted_signals JSONB written by the extractor.",
    ),
    "match_results": ("09", "fitness + confidence split; legacy match_score kept one release."),
    "match_rationales": (
        "09 · 45",
        "Cached per (profile_version, program_version, prompt_version).",
    ),
    "student_feature_vectors": ("45 · 06", "embedding + sparse_features — the L2→L3 handoff."),
    "ai_turns": ("45 §8", "The AI audit / cost ledger — agent, model, tokens, cost, consent_mask."),
    "confidence_outcome_pairs": ("09", "Predicted confidence vs actual outcome — calibration."),
    "embeddings": ("06", "pgvector store for L3 match similarity."),
    "model_registry": ("06", "Registered matching models."),
    "prediction_logs": ("06", "Match-model prediction log."),
    # §4 — application lifecycle
    "applications": ("15 · 18", "status, completeness, decision + decision_by / at / notes."),
    "application_checklists": ("15", "items JSONB, completion %, auto-generated."),
    "application_submissions": ("15", "Submitted docs + package URL + confirmation number."),
    "review_assignments": ("32", "Reviewer ↔ application, due date, status."),
    "rubrics": ("32", "Per institution / program; criteria JSONB."),
    "application_scores": ("32", "The review row — criterion_scores, total, scored_by_type."),
    "ai_packet_summaries": (
        "32 · 37",
        "AI review summary — strengths / concerns / recommended_score.",
    ),
    "interviews": ("33", "Proposed / confirmed times, type, status."),
    "interview_scores": ("33", "criterion_scores + recommendation."),
    "offer_letters": ("34", "offer_type, financial_package_total, conditions, student_response."),
    "enrollment_records": ("35", "Enrollment IS built — the spec 35 spine."),
    "integrity_signals": ("32 §7", "Fraud / anomaly per application."),
    "historical_outcomes": ("06", "Per-program prior outcomes — matching training signal."),
    # §5 — institution & engagement
    "institutions": ("22", "Rich profile JSONB — campus, outcomes, policies, international_info."),
    "schools": ("12", "Sub-institution, e.g. School of Engineering."),
    "programs": (
        "11 · 23",
        "requirements / cost / outcomes / intake_rounds / tracks — JSONB, read by exact key.",
    ),
    "intake_rounds": ("23", "Per-round windows + capacity + enrolled_count."),
    "program_checklist_items": ("23", "Per-program requirement items."),
    "target_segments": ("26", "Rule-tree audience; criteria JSONB."),
    "campaigns": ("25", "+ campaign_recipients / links / actions — trackable."),
    "events": ("20 · 27", "Events; + event_rsvps."),
    "institution_posts": ("27", "Posts / updates; pinned, tagged_program_ids, is_template."),
    "promotions": ("27", "Spotlight / featured; impression & click counts."),
    "inquiries": ("31", "Inbound prospect / applicant inquiries; assigned_to."),
    "communication_templates": ("25 · 29", "Reusable subject / body + variables."),
    "institution_datasets": (
        "24",
        "Uploaded data; column_mapping, validation_errors, usage_scope.",
    ),
    "reviewers": ("32", "Institution staff reviewers; workload."),
    "employer_feedback": ("11", "Insights — employer reviews."),
    "student_program_reviews": ("11", "Insights — student reviews."),
    "crm_records": ("26", "Touchpoints."),
    "saved_lists": ("13", "Saved programs."),
    "saved_list_items": ("13", "Saved-program rows; priority + tags persist server-side."),
    "student_calendar": ("16", "Calendar entries — deadline / interview / work-block."),
    "student_engagement_signals": ("44 §8", "Engagement telemetry."),
    "student_essays": ("14", "Workshop drafts — feedback-only."),
    "student_resumes": ("14", "Workshop drafts — feedback-only."),
    "conversations": ("17 · 29", "Messaging uses conversations, not 'threads'."),
    "messages": ("17 · 29", "Append-only message rows."),
    "conversation_sessions": ("29", "Tracks the LLM intake dialogue."),
    "prospects": ("40", "Pre-applicant top-of-funnel CRM."),
    "recruitment_trips": ("40", "Travel planning."),
    "territories": ("40", "Territory dashboards."),
    "recruitment_fairs": ("40", "Fair lead capture."),
    "international_processing": ("38", "Credential eval, I-20 / DS-2019, English policy."),
    "country_requirement_packs": ("38", "Per-country requirement defaults."),
    "advisor_matches": ("41", "Faculty-advisor matching."),
    "faculty_profiles": ("41", "Faculty research profiles."),
    "funding_packages": ("41 §9", "Assistantship / funding packages."),
    "departments": ("41", "Two-stage department review."),
    "peer_profiles": ("20", "Connect Peers — opt-in, consent- & privacy-gated."),
    "peer_connections": ("20", "Peer connections."),
    "institution_follows": (
        "12",
        "Explicit institution follow — drives the Connect feed. The Connect 'follow' "
        "is institution-level.",
    ),
    "payments": (
        "39",
        "Application fees / deposits / refunds — §8 once listed this absent; now live.",
    ),
    "student_subscriptions": ("06 · 07", "Student billing."),
    "institution_team_invites": ("30", "Team invites."),
    "user_settings": ("05", "Per-user settings."),
    # §6 — platform
    "notifications": ("21", "Notification rows."),
    "notification_preferences": ("21", "Per-user notification preferences."),
    "touchpoints": ("21", "Notification touchpoints."),
    "admissions_audit_log": ("36", "Append-only admissions audit."),
    "admin_audit_events": ("36", "Append-only admin / governance audit."),
    "workshop_feedback_runs": (
        "14",
        "Feedback-only — mechanically excludes any generation field (CI-enforced).",
    ),
    "fairness_reports": ("46 §6", "Fairness IS built — the ml-loop disparate-impact report."),
    "fairness_signals": ("46 §6", "Disparate-impact signal per cohort × week."),
    "fairness_overrides": ("46 §6", "Audited fairness auto-halt overrides."),
    "training_runs": ("06 · 46", "The ML learning loop."),
    "evaluation_runs": ("06 · 46", "Model evaluation runs."),
    "drift_snapshots": ("46", "Drift monitoring."),
    "pipeline_configs": ("31", "Admissions pipeline config."),
    "knowledge_documents": (
        "—",
        "Knowledge / crawler subsystem — in code, beyond the MVP feature docs (§10).",
    ),
    "ai_turn_feedback": ("37", "Thumbs up / down per AI turn."),
}


# ── §7 — already built (other specs imply it's future) ──────────────────────
@dataclass(frozen=True)
class BuiltItem:
    capability: str
    table: str
    spec: str
    note: str


ALREADY_BUILT: tuple[BuiltItem, ...] = (
    BuiltItem(
        "Consent", "student_data_consent", "46 §2", "The 4-lever consent record — not implicit."
    ),
    BuiltItem("Enrollment / yield", "enrollment_records", "35", "The spec 35 data spine exists."),
    BuiltItem(
        "Fairness", "fairness_reports", "46 §6", "Plus the whole ml_loop learning subsystem."
    ),
    BuiltItem(
        "Profile sub-domains",
        "academic_records",
        "42",
        "academic_records, student_courses, test_scores, activities, research, work … "
        "— real tables.",
    ),
    BuiltItem(
        "Major-specific",
        "student_major_specific_signals",
        "43",
        "Per-discipline readiness (renamed from the dropped student_major_readiness).",
    ),
    BuiltItem(
        "Insights", "employer_feedback", "11", "employer_feedback + student_program_reviews."
    ),
)


# ── §8 — the doc's "genuinely NOT built" list, with live presence computed ──
@dataclass(frozen=True)
class PlannedItem:
    table: str
    spec: str
    note: str
    covered_by: str = ""  # a live table that fulfils the capability under another name


PLANNED: tuple[PlannedItem, ...] = (
    PlannedItem(
        "student_follows",
        "20 §2",
        "Connect feed — the doc lists this absent; the live Connect follow is institution-level.",
        covered_by="institution_follows",
    ),
    PlannedItem(
        "payments",
        "39",
        "Phase-2 fee / deposit gateway — the doc listed this absent; spec 39 shipped it.",
    ),
    PlannedItem(
        "student_behavioral_responses",
        "42 §3.19",
        "Behavioral layer — the doc listed this absent; spec 42 shipped it.",
    ),
    PlannedItem(
        "student_stories",
        "42 §3.20",
        "Story bank — the doc listed this absent; spec 42 shipped it.",
    ),
    PlannedItem(
        "student_decision_style", "42 §3.21", "Decision-psychology layer — still future scope."
    ),
    PlannedItem("student_working_style", "42 §3.22", "Working-style layer — still future scope."),
    PlannedItem("student_skills", "42 §3.23", "Skills layer — still future scope."),
    PlannedItem("student_friction_signals", "42 §3.26", "Friction signals — still future scope."),
)


# ── §9 — conventions, as built ──────────────────────────────────────────────
CONVENTIONS: tuple[dict, ...] = (
    {
        "title": "UUID keys + timestamps",
        "body": "Almost every table carries a UUID primary key (UUIDPrimaryKeyMixin) and "
        "created_at / updated_at (TimestampMixin). The counts below are read from the live "
        "schema, so the coverage is exact.",
    },
    {
        "title": "Relational profile, JSONB at the edges",
        "body": "The student profile is fully relational — a real table per domain, not a JSONB "
        "blob. Evolving program shapes (requirements / cost / outcomes) stay JSONB on programs "
        "and are read by exact key.",
    },
    {
        "title": "Versioning drives the cache",
        "body": "profile_version / program_version / strategy version bump on write and invalidate "
        "the match-rationale cache (spec 45 §12).",
    },
    {
        "title": "pgvector for similarity",
        "body": "embeddings and knowledge_documents carry a pgvector embedding column for L3 match "
        "similarity (spec 06 §4).",
    },
    {
        "title": "Append-only + soft-delete",
        "body": "Audit, ML-outcome and financial rows are append-only and never hard-deleted; "
        "student PII is soft-deleted with a grace window (spec 46).",
    },
)


def _column_stats(table) -> dict:
    """Per-table column / FK / JSONB / vector / mixin facts, read live."""
    cols = list(table.columns)
    jsonb = sum(1 for c in cols if c.type.__class__.__name__ in ("JSONB", "JSON"))
    is_vector = any("vector" in c.type.__class__.__name__.lower() for c in cols)
    fk_targets: list[str] = []
    for c in cols:
        for fk in c.foreign_keys:
            target = fk.target_fullname.split(".")[0]  # → referenced table name
            if target not in fk_targets:
                fk_targets.append(target)
    has_pk = any(c.primary_key and c.type.__class__.__name__ == "UUID" for c in cols)
    has_ts = "created_at" in table.columns and "updated_at" in table.columns
    return {
        "column_count": len(cols),
        "jsonb_count": jsonb,
        "fk_count": sum(len(c.foreign_keys) for c in cols),
        "fk_targets": sorted(fk_targets)[:6],
        "is_vector": is_vector,
        "has_uuid_pk": has_pk,
        "has_timestamps": has_ts,
    }


def _module_map(registry) -> dict[str, str]:
    """live table name → model module (last path segment)."""
    out: dict[str, str] = {}
    for mapper in registry.mappers:
        cls = mapper.class_
        tn = getattr(cls, "__tablename__", None)
        if tn:
            out[tn] = cls.__module__.rsplit(".", 1)[-1]
    return out


def build_data_model(metadata=None, registry=None) -> dict:
    """Assemble the ``GET /build/data-model`` payload from the live schema.

    ``metadata`` defaults to the running ``Base.metadata`` — the same object the
    app and Alembic build against — so the table count equals what's deployed.
    """
    if metadata is None or registry is None:
        import unipaith.models  # noqa: F401 — force-populate the metadata + registry
        from unipaith.models.base import Base

        metadata = metadata or Base.metadata
        registry = registry or Base.registry

    tables = metadata.tables
    mod_of = _module_map(registry)

    # Group live tables by domain (via module), attaching computed stats + notes.
    by_domain: dict[str, list[dict]] = defaultdict(list)
    module_counts: dict[str, int] = defaultdict(int)
    total_columns = total_jsonb = total_fk = vector_tables = uuid_pk = ts_tables = 0

    for name in sorted(tables):
        table = tables[name]
        module = mod_of.get(name, "(assoc)")
        module_counts[module] += 1
        domain = _DOMAIN_BY_MODULE.get(module, "platform")
        stats = _column_stats(table)
        total_columns += stats["column_count"]
        total_jsonb += stats["jsonb_count"]
        total_fk += stats["fk_count"]
        vector_tables += 1 if stats["is_vector"] else 0
        uuid_pk += 1 if stats["has_uuid_pk"] else 0
        ts_tables += 1 if stats["has_timestamps"] else 0
        note = TABLE_NOTES.get(name)
        by_domain[domain].append(
            {
                "table": name,
                "module": module,
                "spec": note[0] if note else "",
                "note": note[1] if note else "",
                **stats,
            }
        )

    domains = []
    for d in DOMAINS:
        rows = sorted(by_domain.get(d.key, []), key=lambda r: (not r["note"], r["table"]))
        domains.append(
            {
                "key": d.key,
                "title": d.title,
                "section": d.section,
                "spec": d.spec,
                "blurb": d.blurb,
                "table_count": len(rows),
                "modules": list(d.modules),
                "tables": rows,
            }
        )

    already_built = [
        {
            "capability": b.capability,
            "table": b.table,
            "spec": b.spec,
            "note": b.note,
            "live": b.table in tables,
        }
        for b in ALREADY_BUILT
    ]

    planned = [
        {
            "table": p.table,
            "spec": p.spec,
            "note": p.note,
            "covered_by": p.covered_by,
            "live": p.table in tables,
            "covered_by_live": bool(p.covered_by) and p.covered_by in tables,
        }
        for p in PLANNED
    ]
    planned_now_live = sum(1 for p in planned if p["live"])

    modules = sorted(
        (
            {"module": m, "table_count": c, "domain": _DOMAIN_BY_MODULE.get(m, "platform")}
            for m, c in module_counts.items()
        ),
        key=lambda x: (-x["table_count"], x["module"]),
    )

    table_count = len(tables)
    return {
        "summary": {
            "table_count": table_count,
            "column_count": total_columns,
            "jsonb_column_count": total_jsonb,
            "fk_count": total_fk,
            "vector_table_count": vector_tables,
            "module_count": len(module_counts),
            "uuid_pk_table_count": uuid_pk,
            "timestamp_table_count": ts_tables,
            "domain_count": len(DOMAINS),
            # Doc-vs-live drift (spec 51 says 107 tables / 23 files), surfaced for honesty.
            "doc_claimed_tables": DOC_CLAIMED_TABLES,
            "doc_claimed_model_files": DOC_CLAIMED_MODEL_FILES,
            "planned_total": len(planned),
            "planned_now_live": planned_now_live,
            "live_is_source_of_truth": True,
        },
        "conventions": list(CONVENTIONS),
        "domains": domains,
        "modules": modules,
        "already_built": already_built,
        "planned": planned,
        "note": "The table list and every count are introspected from the running "
        "SQLAlchemy metadata — the same schema the app and Alembic build against — so "
        "this map is the source of truth and can't drift from what's deployed.",
    }
