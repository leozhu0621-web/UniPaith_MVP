"""Spec 49 — Feature-List V1 coverage map, as queryable data.

Every feature from the founder's Feature List, mapped to the spec that covers it
(or flagged net-new), classified core / extend / defer for the MVP cut. Two axes
are tracked deliberately:

- ``klass`` — the MVP *plan* classification from spec 49 (core/extend/defer).
- ``delivered`` — whether it is *actually* in the live build today.

These differ where the build has moved ahead of the plan: spec 49 was written
before specs 38–41 shipped, so International / Fees / Recruitment / Graduate are
``defer`` in the plan yet ``delivered`` now. Surfacing both is the honest mirror —
nothing in the founder's list is silently dropped, and the build's actual reach
is shown plainly.
"""

from __future__ import annotations

from dataclasses import dataclass

# klass — the MVP plan classification
CORE = "core"
EXTEND = "extend"
DEFER = "defer"

# status — spec-49 coverage state
COVERED = "covered"  # a shipped spec already specifies it
WRITTEN = "written"  # spec written this pass (closed an MVP gap)
NET_NEW = "net_new"  # not in the spec set; needs a spec / section

KLASS_LABELS = {CORE: "Core", EXTEND: "Extend", DEFER: "Defer"}
STATUS_LABELS = {COVERED: "Covered", WRITTEN: "Written", NET_NEW: "Net-new"}


@dataclass(frozen=True)
class Feature:
    name: str
    side: str  # "student" | "institution"
    status: str  # COVERED | WRITTEN | NET_NEW
    spec: str  # spec doc id(s), e.g. "08" or "18 §3 + 45 §15"
    klass: str  # CORE | EXTEND | DEFER
    delivered: bool  # in the live build today
    note: str = ""


# ── Student-side features (spec 49 §2) ──────────────────────────────────────
STUDENT: tuple[Feature, ...] = (
    Feature("Universal Profile (19 sections)", "student", COVERED, "08", CORE, True),
    Feature("Program Match (banded results + reasoning)", "student", COVERED, "09", CORE, True),
    Feature("Discovery (NLP search, chips, tiles, compare)", "student", COVERED, "10", CORE, True),
    Feature("Program Detail Page (+ Insights)", "student", COVERED, "11", CORE, True),
    Feature("School Detail Page", "student", COVERED, "12", CORE, True),
    Feature("Saved List (reach/target/safer, compare)", "student", COVERED, "13", CORE, True),
    Feature("Workshops (resume/essay/test, feedback-only)", "student", COVERED, "14", CORE, True),
    Feature(
        "Applications (adaptive checklist, readiness gate)", "student", COVERED, "15", CORE, True
    ),
    Feature("Calendar", "student", COVERED, "16", CORE, True),
    Feature("Inbox (human/system, action labels)", "student", COVERED, "17", CORE, True),
    Feature("Decisions & Offers (compare, accept/decline)", "student", COVERED, "18", CORE, True),
    Feature("Discovery chat (3-track LLM)", "student", COVERED, "19", CORE, True),
    Feature(
        "Probability Bands (admit/scholarship/waitlist)", "student", WRITTEN, "09 §4A", EXTEND, True
    ),
    Feature(
        "Net Price Estimator (COA + scholarship gap)", "student", WRITTEN, "11 §3.3a", EXTEND, True
    ),
    Feature(
        "Offer Package Explainer (line-item cost/aid/terms)",
        "student",
        COVERED,
        "18 §3 + 45 §15",
        CORE,
        True,
        "OutcomeBrief agent turns an offer into a plain-language brief.",
    ),
    Feature(
        "Support Plan Preview (tutoring/disability/writing-center)",
        "student",
        NET_NEW,
        "11 (new section)",
        DEFER,
        False,
    ),
    Feature(
        "Readiness Tracker w/ peer context", "student", WRITTEN, "08 §15 + 42 §4.5", EXTEND, True
    ),
    Feature("Thank-You Note Tracker (recommenders)", "student", NET_NEW, "08 §11.4", DEFER, False),
    Feature("Letter Request Templates / brag sheets", "student", NET_NEW, "08 §11.4", DEFER, False),
    Feature("Campus Visit Tracker", "student", NET_NEW, "16 (event type)", DEFER, False),
    Feature("Student Connect (Updates/Events/Peers)", "student", WRITTEN, "20", CORE, True),
    Feature("Alumni Network Connection", "student", NET_NEW, "20 §14", DEFER, False),
    Feature("Offline Mode", "student", NET_NEW, "cross-cutting PWA", DEFER, False),
    Feature("Voice Input (dictation)", "student", NET_NEW, "19 accessibility", DEFER, False),
    Feature("Multi-Device Sync w/ conflict resolution", "student", NET_NEW, "infra", DEFER, False),
    Feature("Profile Export → Common App / Coalition", "student", WRITTEN, "08 §16", EXTEND, True),
    Feature("LinkedIn profile sync", "student", WRITTEN, "08 §16 + 44 §5.3", EXTEND, True),
    Feature(
        "Application Cost Tracker (fees/waivers/deadlines)",
        "student",
        WRITTEN,
        "15 §2A",
        EXTEND,
        True,
    ),
)


# ── Institution-side features (spec 49 §3) ──────────────────────────────────
INSTITUTION: tuple[Feature, ...] = (
    Feature("Institution Profile Page", "institution", COVERED, "22", CORE, True),
    Feature("Program Detail Editor", "institution", COVERED, "23", CORE, True),
    Feature("Data Upload", "institution", COVERED, "24", CORE, True),
    Feature("Campaigns (internal + external SES)", "institution", COVERED, "25", CORE, True),
    Feature("Audience Segmentation", "institution", COVERED, "26", CORE, True),
    Feature("Posts / Updates / Events", "institution", COVERED, "27", CORE, True),
    Feature("Attribution & Funnel Analytics", "institution", COVERED, "28", CORE, True),
    Feature("Admissions Intake (dashboard, batch)", "institution", COVERED, "31", CORE, True),
    Feature("Review Workspace (rubric, cohort compare)", "institution", COVERED, "32", CORE, True),
    Feature("Interviews Module", "institution", COVERED, "33", CORE, True),
    Feature("Decisions & Offers", "institution", COVERED, "34", CORE, True),
    Feature("Audit Log", "institution", COVERED, "36", CORE, True),
    Feature("AI Extensibility", "institution", COVERED, "37", CORE, True),
    Feature("Institution Messaging / Inbox", "institution", WRITTEN, "29", CORE, True),
    Feature(
        "Enrollment Management (+ waitlist, yield)", "institution", WRITTEN, "35", EXTEND, True
    ),
    Feature("Blind review mode", "institution", WRITTEN, "32 §7A.1", EXTEND, True),
    Feature(
        "Reader calibration (inter-rater reliability)",
        "institution",
        WRITTEN,
        "32 §7A.2",
        EXTEND,
        True,
    ),
    Feature(
        "Test-score management (superscore, test-optional)",
        "institution",
        WRITTEN,
        "23 §3 + 32 §7A.3",
        EXTEND,
        True,
    ),
    Feature(
        "Holistic-review flags (first-gen / context)",
        "institution",
        WRITTEN,
        "32 §7A.4 + 46",
        EXTEND,
        True,
    ),
    Feature(
        "Transcript Parsing (OCR)", "institution", WRITTEN, "44 §3.1/§5.3 + 45 §19", EXTEND, True
    ),
    # ── Plan said defer; the build shipped these ahead of plan (specs 38–41, 39) ──
    Feature(
        "International tooling (credential eval, I-20, English)",
        "institution",
        NET_NEW,
        "38",
        DEFER,
        True,
        "Plan deferred; shipped as spec 38 (institution-side processing).",
    ),
    Feature(
        "Fee management (app fees, waivers, deposits, refunds)",
        "institution",
        NET_NEW,
        "39",
        DEFER,
        True,
        "Plan deferred; shipped as spec 39 (Stripe-abstracted, mock default).",
    ),
    Feature(
        "Recruitment / pre-applicant CRM (travel, territories, fairs)",
        "institution",
        NET_NEW,
        "40",
        DEFER,
        True,
        "Plan deferred; shipped as spec 40 (top-of-funnel CRM).",
    ),
    Feature(
        "Graduate / PhD tooling (advisor match, funding, dept review)",
        "institution",
        NET_NEW,
        "41",
        DEFER,
        True,
        "Plan deferred; shipped as spec 41 (graduate admissions).",
    ),
    Feature(
        "Deposit payment gateway (real collection, refunds)",
        "institution",
        NET_NEW,
        "39",
        DEFER,
        True,
        "Provider seam shipped; production stays on the mock provider.",
    ),
    Feature(
        "Multi-stage review workflow + workload balancing",
        "institution",
        NET_NEW,
        "32 (extend)",
        DEFER,
        False,
    ),
    Feature("Committee-review scheduling", "institution", NET_NEW, "32 (extend)", DEFER, False),
    Feature(
        "Alumni Interviewer Network (portal, geo, training)",
        "institution",
        NET_NEW,
        "33 (extend)",
        DEFER,
        False,
    ),
    Feature(
        "Transfer-student tools (credit eval, articulation)",
        "institution",
        NET_NEW,
        "31 (extend)",
        DEFER,
        False,
    ),
    Feature(
        "Compliance (IPEDS, FERPA tools, SIS export)",
        "institution",
        NET_NEW,
        "46 (extend)",
        DEFER,
        False,
        "Partial in spec 46 (data-rights governance).",
    ),
    Feature(
        "Communication channels (SMS, WhatsApp, widget)",
        "institution",
        NET_NEW,
        "25 / 17 (extend)",
        DEFER,
        False,
    ),
    Feature(
        "Mobile App for Reviewers (offline, push)", "institution", NET_NEW, "infra", DEFER, False
    ),
)

ALL_FEATURES: tuple[Feature, ...] = STUDENT + INSTITUTION


def _feature_payload(f: Feature) -> dict:
    return {
        "name": f.name,
        "side": f.side,
        "status": f.status,
        "status_label": STATUS_LABELS.get(f.status, f.status),
        "spec": f.spec,
        "klass": f.klass,
        "klass_label": KLASS_LABELS.get(f.klass, f.klass),
        "delivered": f.delivered,
        "note": f.note,
    }


def build_features() -> dict:
    """Assemble the ``GET /build/features`` payload (spec 49)."""
    features = [_feature_payload(f) for f in ALL_FEATURES]
    klass_counts: dict[str, int] = {CORE: 0, EXTEND: 0, DEFER: 0}
    for f in ALL_FEATURES:
        klass_counts[f.klass] += 1
    delivered = sum(1 for f in ALL_FEATURES if f.delivered)
    # MVP scope = everything the plan calls core or extend.
    mvp_scope = [f for f in ALL_FEATURES if f.klass in (CORE, EXTEND)]
    mvp_delivered = sum(1 for f in mvp_scope if f.delivered)
    ahead_of_plan = sum(1 for f in ALL_FEATURES if f.klass == DEFER and f.delivered)
    return {
        "summary": {
            "feature_count": len(ALL_FEATURES),
            "student_count": len(STUDENT),
            "institution_count": len(INSTITUTION),
            "delivered": delivered,
            "klass_counts": klass_counts,
            "mvp_scope_count": len(mvp_scope),
            "mvp_delivered": mvp_delivered,
            "mvp_complete": mvp_delivered == len(mvp_scope),
            "ahead_of_plan": ahead_of_plan,
        },
        "features": features,
    }
