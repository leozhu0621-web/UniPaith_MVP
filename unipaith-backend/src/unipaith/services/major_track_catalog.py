"""Spec 43 — Major-Specific Field Catalog (the build-ready structured contract).

The authoritative 15-track registry plus, per track, the field schema students
fill in. Each track is a JSONB signal subdocument on
``student_major_specific_signals`` (Spec 42 §8); a track activates when the
student's major (``field_of_study`` / ``target_major_field_primary``) maps to its
``track_key`` (Spec 43 §1), or when the student opts in explicitly.

This module is **pure data + pure helpers** — no DB, no I/O — so it can be read
by the validator, the deterministic ``major_track_coach`` (§4.18 outputs), the
API ``/catalog`` endpoint, and the frontend's generic form renderer alike (one
source of truth, Spec 43 §18 "store once… avoid duplication").

Sources (Spec 43 §3): ``Misc./Prompt Library.docx`` (deepest enumeration,
preserved at ``/tmp/master_paper.txt`` lines 3905–4617) + Master Paper Appendix A
(typed I/O) + Spec 43 §2–§16 (the organized per-track contract).

Field ``kind`` vocabulary (drives validation + the FE widget):
- ``rating_1_5`` — 1–5 self-rating (1 = none, 5 = expert), Spec 43 §1.
- ``enum``       — single choice from ``options``.
- ``tags``       — array of strings (free + ``options`` as suggestions).
- ``bool``       — flag.
- ``number``     — non-negative number (hours, months, counts, scores).
- ``link``       — URL / external reference (string).
- ``text``       — short free text.
"""

from __future__ import annotations

# ── Track registry (Spec 43 §1, the 15 track_keys) ───────────────────────────
TRACK_KEYS: tuple[str, ...] = (
    "cs_data_ai",
    "engineering",
    "business",
    "health",
    "arts_design",
    "performing_arts",
    "humanities_social_sciences",
    "law_policy",
    "education_counseling",
    "journalism_communications",
    "math_physics_chemistry_sciences",
    "comp_engineering_robotics",
    "environmental_sustainability",
    "language_linguistics",
    "entrepreneurship_product",
)


# ── Field builders (keep each track readable + ruff-format friendly) ──────────
def _r(key: str, label: str) -> dict:
    """1–5 self-rating."""
    return {"key": key, "label": label, "kind": "rating_1_5", "max": 5}


def _b(key: str, label: str) -> dict:
    return {"key": key, "label": label, "kind": "bool"}


def _tags(key: str, label: str, options: tuple[str, ...] = ()) -> dict:
    return {"key": key, "label": label, "kind": "tags", "options": list(options)}


def _enum(key: str, label: str, options: tuple[str, ...]) -> dict:
    return {"key": key, "label": label, "kind": "enum", "options": list(options)}


def _num(key: str, label: str, *, unit: str | None = None) -> dict:
    f: dict = {"key": key, "label": label, "kind": "number"}
    if unit:
        f["unit"] = unit
    return f


def _link(key: str, label: str) -> dict:
    return {"key": key, "label": label, "kind": "link"}


def _text(key: str, label: str) -> dict:
    return {"key": key, "label": label, "kind": "text"}


def _g(key: str, label: str, *fields: dict) -> dict:
    return {"key": key, "label": label, "fields": list(fields)}


# ── Per-track schemas ─────────────────────────────────────────────────────────
# Each entry: track_key → {label, blurb, groups[], recommendation?}. ``groups``
# is the ordered set of field groups the FE renders. ``recommendation`` (where
# present) names rating fields whose maxima drive a sub-track suggestion
# (§4.18 track_recommendation).

_TRACKS: dict[str, dict] = {
    # 2 — Computer Science / Data / AI
    "cs_data_ai": {
        "label": "Computer Science · Data · AI",
        "blurb": "Programming, CS fundamentals, ML/data readiness, tooling, and "
        "competitive/portfolio evidence.",
        "groups": [
            _g(
                "fundamentals",
                "CS fundamentals (self-rating)",
                _r("cs_fundamentals_self_rating_dsa", "Data structures & algorithms"),
                _r("cs_fundamentals_self_rating_algorithms", "Algorithms"),
                _r("cs_fundamentals_self_rating_os", "Operating systems"),
                _r("cs_fundamentals_self_rating_networks", "Networks"),
                _r("cs_fundamentals_self_rating_databases", "Databases"),
                _r("cs_fundamentals_self_rating_discrete_math", "Discrete math"),
                _r("cs_fundamentals_self_rating_oop", "Object-oriented programming"),
                _r("cs_fundamentals_self_rating_concurrency", "Concurrency / parallelism"),
                _r("cs_fundamentals_self_rating_security_basics", "Security basics"),
                _r("cs_fundamentals_self_rating_computer_architecture", "Computer architecture"),
                _r("cs_fundamentals_self_rating_compilers", "Compilers"),
                _r("cs_fundamentals_self_rating_software_engineering", "Software engineering"),
            ),
            _g(
                "data_ml",
                "Data & ML readiness (self-rating)",
                _r("data_skill_self_rating_sql", "SQL"),
                _r("data_skill_self_rating_eda", "Cleaning / EDA"),
                _r("data_skill_self_rating_viz", "Visualization / storytelling"),
                _r("data_skill_self_rating_ab_testing", "Experiment design / A-B testing"),
                _r("data_skill_self_rating_feature_engineering", "Feature engineering"),
                _r("ml_readiness_classification_regression", "Classification / regression"),
                _r("ml_readiness_deep_learning", "Deep learning"),
                _r("ml_readiness_nlp", "NLP / LLMs"),
                _r("ml_readiness_recsys", "Recommendation systems"),
                _r("ml_readiness_computer_vision", "Computer vision"),
                _r("ml_readiness_time_series", "Time series"),
                _r("ml_readiness_evaluation", "Model evaluation / metrics"),
            ),
            _g(
                "math",
                "Math readiness (self-rating)",
                _r("math_readiness_calculus", "Calculus sequence"),
                _r("math_readiness_linear_algebra", "Linear algebra"),
                _r("math_readiness_probability", "Probability"),
                _r("math_readiness_statistics", "Statistics"),
            ),
            _g(
                "languages",
                "Programming languages",
                _enum(
                    "primary_programming_language",
                    "Primary language",
                    ("python", "java", "cpp", "javascript", "go", "rust", "c", "other"),
                ),
                _tags(
                    "programming_languages_list",
                    "Languages used",
                    ("Python", "Java", "C++", "JavaScript", "Go", "Rust", "C", "SQL", "R"),
                ),
            ),
            _g(
                "tools",
                "Tool familiarity (self-rating)",
                _r("tool_familiarity_git", "Git / version control"),
                _r("tool_familiarity_linux", "Linux"),
                _r("tool_familiarity_docker", "Docker"),
                _r("tool_familiarity_kubernetes", "Kubernetes"),
                _r("tool_familiarity_cloud", "Cloud (AWS/GCP/Azure)"),
                _r("tool_familiarity_ci_cd", "CI/CD"),
                _r("tool_familiarity_data_warehouse", "Data warehouse / Spark / dbt / Airflow"),
                _b("mlops_exposure_flag", "MLOps exposure"),
            ),
            _g(
                "evidence",
                "Evidence & competitive",
                _link("github_link", "GitHub profile"),
                _link("kaggle_link", "Kaggle profile"),
                _b("open_source_contributions", "Open-source contributions"),
                _tags("hackathon_list", "Hackathons (name / result)"),
                _enum(
                    "competitive_programming_best_rank",
                    "Competitive programming — best level",
                    ("n/a", "regional", "national", "ICPC_finalist"),
                ),
                _enum(
                    "leetcode_frequency",
                    "LeetCode practice frequency",
                    ("none", "occasional", "weekly", "daily"),
                ),
                _num("coding_assessment_score", "Coding assessment score (if any)"),
                _b("research_experience_flag", "Research experience"),
                _link("research_output_link", "Research output / DOI"),
                _link("portfolio_link", "Project portfolio (repos / demos)"),
            ),
        ],
        # Sub-track suggestion (§4.18 track_recommendation): the strongest cluster.
        "recommendation": {
            "Data": (
                "data_skill_self_rating_sql",
                "data_skill_self_rating_eda",
                "data_skill_self_rating_viz",
                "data_skill_self_rating_ab_testing",
            ),
            "AI": (
                "ml_readiness_deep_learning",
                "ml_readiness_nlp",
                "ml_readiness_computer_vision",
                "ml_readiness_recsys",
            ),
            "Systems": (
                "cs_fundamentals_self_rating_os",
                "cs_fundamentals_self_rating_networks",
                "cs_fundamentals_self_rating_concurrency",
                "cs_fundamentals_self_rating_computer_architecture",
            ),
            "SWE": (
                "cs_fundamentals_self_rating_software_engineering",
                "cs_fundamentals_self_rating_oop",
                "tool_familiarity_ci_cd",
                "cs_fundamentals_self_rating_dsa",
            ),
            "Cyber": (
                "cs_fundamentals_self_rating_security_basics",
                "cs_fundamentals_self_rating_networks",
                "cs_fundamentals_self_rating_os",
            ),
        },
        "artifact_hints": {
            "github_link": "Add a public GitHub with at least one substantial project.",
            "portfolio_link": "Link a deployed demo or a repo with a clear README.",
            "research_output_link": "Link a paper, poster, or open-source PR if you have one.",
        },
    },
    # 3 — Engineering (ME / EE / Civil / Aerospace / ChemE)
    "engineering": {
        "label": "Engineering",
        "blurb": "Mechanical / Electrical / Civil / Aerospace / Chemical core "
        "topics, tools, and hands-on evidence.",
        "groups": [
            _g(
                "core",
                "Core-topic readiness (self-rating)",
                _r("core_statics_dynamics", "Statics / dynamics"),
                _r("core_thermodynamics", "Thermodynamics"),
                _r("core_fluid_mechanics", "Fluid mechanics"),
                _r("core_heat_transfer", "Heat transfer"),
                _r("core_materials", "Materials science"),
                _r("core_circuits", "Circuits / electronics"),
                _r("core_controls", "Controls"),
            ),
            _g(
                "ee",
                "Electrical-specific (self-rating)",
                _r("ee_signals_systems", "Signals & systems"),
                _r("ee_power_systems", "Power systems"),
                _r("ee_electromagnetics", "Electromagnetics"),
                _r("ee_embedded_systems", "Embedded systems"),
                _r("ee_vlsi", "VLSI"),
            ),
            _g(
                "civil",
                "Civil-specific (self-rating)",
                _r("civil_structural", "Structural"),
                _r("civil_geotechnical", "Geotechnical"),
                _r("civil_transportation", "Transportation"),
                _r("civil_environmental", "Environmental"),
                _r("civil_construction_mgmt", "Construction management"),
            ),
            _g(
                "cheme",
                "Chemical-specific (self-rating)",
                _r("cheme_reaction_engineering", "Reaction engineering"),
                _r("cheme_separations", "Separations"),
                _r("cheme_process_control", "Process control"),
                _r("cheme_transport_phenomena", "Transport phenomena"),
            ),
            _g(
                "tools",
                "Tools (self-rating)",
                _r("tool_cad", "CAD (SolidWorks / AutoCAD)"),
                _r("tool_fea", "FEA"),
                _r("tool_cfd", "CFD"),
                _r("tool_matlab_simulink", "MATLAB / Simulink"),
                _r("tool_simulation", "Simulation (ANSYS / COMSOL)"),
            ),
            _g(
                "handson",
                "Hands-on & credentials",
                _tags(
                    "manufacturing_exposure",
                    "Manufacturing exposure",
                    ("machining", "3D printing", "welding", "metrology"),
                ),
                _b("lab_safety_certified", "Lab-safety certification"),
                _b("pe_track_flag", "Professional Engineer (PE) track"),
                _b("capstone_flag", "Capstone / major project"),
                _link("capstone_link", "Capstone report / portfolio"),
                _enum(
                    "discipline_preference",
                    "Discipline preference",
                    ("ME", "EE", "Civil", "Aerospace", "ChemE", "other"),
                ),
            ),
        ],
        "artifact_hints": {
            "capstone_link": "Link a capstone report, CAD portfolio, or build photos.",
        },
    },
    # 4 — Business / Finance / Marketing / Analytics
    "business": {
        "label": "Business · Finance · Marketing · Analytics",
        "blurb": "Domain depth, analytics tooling, work-sample artifacts, and credentials.",
        "groups": [
            _g(
                "domain",
                "Domain self-ratings",
                _r("domain_finance", "Finance"),
                _r("domain_accounting", "Accounting"),
                _r("domain_marketing", "Marketing"),
                _r("domain_analytics", "Analytics"),
                _r("domain_strategy", "Strategy"),
                _r("domain_operations", "Operations"),
                _r("domain_quant_methods", "Quant methods"),
            ),
            _g(
                "tools",
                "Tool depth (self-rating)",
                _r("tool_excel", "Excel"),
                _r("tool_sql", "SQL"),
                _r("tool_python", "Python"),
                _r("tool_r", "R"),
                _r("tool_bi", "Tableau / Power BI"),
                _r("tool_ga4", "GA4 / web analytics"),
                _r("tool_crm", "CRM (Salesforce / HubSpot)"),
            ),
            _g(
                "artifacts",
                "Work-sample artifacts",
                _link("financial_model_link", "Financial model"),
                _link("dashboard_link", "Dashboard"),
                _text("campaign_metrics", "Campaign metrics (CTR / CVR / CAC / ROAS)"),
                _text("case_competition_placements", "Case-competition placements"),
                _tags(
                    "internship_domains",
                    "Internship domains",
                    ("consulting", "finance", "marketing", "operations", "product"),
                ),
                _num("internship_months", "Internship experience", unit="months"),
            ),
            _g(
                "credentials",
                "Credentials & targets",
                _text("credentials_progress", "CFA / CPA / Bloomberg progress"),
                _tags(
                    "career_target_roles",
                    "Target roles",
                    ("consulting", "investment banking", "PM", "marketing analyst", "data analyst"),
                ),
            ),
        ],
        "artifact_hints": {
            "financial_model_link": "Add a financial model or valuation work sample.",
            "dashboard_link": "Link an analytics dashboard you built.",
        },
    },
    # 5 — Health / Pre-med / Nursing / Public Health
    "health": {
        "label": "Health · Pre-med · Nursing · Public Health",
        "blurb": "Clinical exposure, certifications, science prerequisites, and licensure path.",
        "groups": [
            _g(
                "clinical",
                "Clinical exposure",
                _tags(
                    "clinical_setting",
                    "Setting",
                    ("hospital", "clinic", "community", "research"),
                ),
                _tags(
                    "clinical_exposure_type",
                    "Exposure type",
                    ("shadowing", "volunteer", "EMT", "scribing"),
                ),
                _b("patient_facing_flag", "Patient-facing experience"),
                _num("clinical_hours_total", "Clinical hours (total)", unit="hours"),
                _num("volunteer_hours_health", "Health-related volunteer hours", unit="hours"),
            ),
            _g(
                "certifications",
                "Certifications",
                _tags(
                    "certifications",
                    "Certifications",
                    ("CNA", "EMT", "BLS", "ACLS", "phlebotomy", "CPR", "HIPAA"),
                ),
                _b("hipaa_training_flag", "HIPAA training complete"),
                _b("immunization_clearance_flag", "Immunization / health clearance ready"),
            ),
            _g(
                "prereqs",
                "Prerequisite readiness (self-rating)",
                _r("prereq_bio", "Biology"),
                _r("prereq_chem", "General chemistry"),
                _r("prereq_orgo", "Organic chemistry"),
                _r("prereq_physics", "Physics"),
                _r("prereq_biochem", "Biochemistry"),
                _r("prereq_anatomy", "Anatomy"),
                _r("prereq_physiology", "Physiology"),
                _r("prereq_stats", "Statistics"),
            ),
            _g(
                "licensure",
                "Licensure & public health",
                _b("mcat_flag", "MCAT planned / taken"),
                _b("nclex_flag", "NCLEX path"),
                _enum(
                    "licensure_track",
                    "Intended licensure track",
                    ("pre_med", "nursing", "public_health", "allied_health", "undecided"),
                ),
                _tags(
                    "public_health_interest",
                    "Public-health interest",
                    ("epidemiology", "global health", "community", "environmental health"),
                ),
                _num("community_health_hours", "Community-health project hours", unit="hours"),
            ),
        ],
        "artifact_hints": {},
    },
    # 6 — Arts / Design / Architecture / Media
    "arts_design": {
        "label": "Art · Design · Architecture · Media",
        "blurb": "Portfolio depth, software proficiency, and discipline-specific exposure.",
        "groups": [
            _g(
                "portfolio",
                "Portfolio",
                _enum(
                    "discipline",
                    "Discipline",
                    (
                        "art",
                        "graphic_design",
                        "product_design",
                        "architecture",
                        "film_media",
                        "photography",
                        "interaction_design",
                    ),
                ),
                _link("portfolio_link", "Portfolio link / upload"),
                _num("portfolio_pieces_count", "Number of pieces"),
                _tags("medium_breadth", "Media / techniques"),
                _b("exhibition_publication_flag", "Exhibitions / publications"),
                _b("commission_client_work_flag", "Commission / client work"),
            ),
            _g(
                "software",
                "Software proficiency (self-rating)",
                _r("software_adobe", "Adobe Creative Suite"),
                _r("software_figma", "Figma"),
                _r("software_cad", "CAD"),
                _r("software_rhino", "Rhino / 3D"),
                _r("software_motion", "Motion / video editing"),
            ),
            _g(
                "architecture",
                "Architecture-specific",
                _b("arch_model_making_flag", "Model-making exposure"),
                _b("arch_bim_flag", "BIM exposure"),
                _b("arch_site_analysis_flag", "Site analysis exposure"),
                _num("arch_studio_hours", "Studio hours", unit="hours"),
            ),
            _g(
                "design_process",
                "Design process",
                _b("design_research_flag", "Design research / user testing"),
                _link("artist_statement_link", "Artist / design statement"),
            ),
        ],
        "artifact_hints": {
            "portfolio_link": "A reviewable portfolio is the single most important artifact here.",
        },
    },
    # 7 — Performing Arts (Music / Theater / Dance)
    "performing_arts": {
        "label": "Performing Arts",
        "blurb": "Audition readiness — instrument/voice, repertoire, training, and recordings.",
        "groups": [
            _g(
                "profile",
                "Performer profile",
                _enum("discipline", "Discipline", ("music", "theater", "dance")),
                _text("instrument_voice_type", "Instrument / voice type"),
                _num("years_training", "Years of training", unit="years"),
                _r("theory_proficiency", "Theory proficiency (self-rating)"),
            ),
            _g(
                "experience",
                "Experience & repertoire",
                _enum(
                    "performance_history_type",
                    "Performance history",
                    ("solo", "ensemble", "lead", "company"),
                ),
                _text("repertoire_list", "Repertoire list"),
                _text("competition_placements", "Competition placements"),
                _tags("dance_styles", "Dance styles / technique"),
            ),
            _g(
                "audition",
                "Audition materials",
                _b("audition_required_flag", "Audition required"),
                _link("recording_link", "Recording link / upload"),
                _b("headshot_resume_ready_flag", "Headshot / resume ready"),
            ),
        ],
        "artifact_hints": {
            "recording_link": "Upload a recent recording — it anchors the audition packet.",
        },
    },
    # 8 — Humanities / Social Sciences
    "humanities_social_sciences": {
        "label": "Humanities · Social Sciences",
        "blurb": "Writing-sample depth, research methods, and scholarly outputs.",
        "groups": [
            _g(
                "methods",
                "Research methods (self-rating)",
                _r("methods_qualitative", "Qualitative methods"),
                _r("methods_quantitative", "Quantitative methods"),
                _r("methods_statistics", "Statistics (for quant tracks)"),
                _r("reading_volume_tolerance", "Reading-volume tolerance"),
            ),
            _g(
                "exposure",
                "Methods exposure",
                _b("method_surveys_flag", "Surveys"),
                _b("method_interviews_flag", "Interviews / focus groups"),
                _b("method_archival_flag", "Archival research"),
                _b("method_experimental_flag", "Experimental design"),
                _b("fieldwork_flag", "Fieldwork"),
                _b("irb_training_flag", "IRB / ethics training"),
            ),
            _g(
                "outputs",
                "Writing & outputs",
                _link("writing_sample_link", "Writing sample"),
                _b("thesis_independent_study_flag", "Thesis / independent study"),
                _text("publications_presentations", "Publications / conference presentations"),
                _tags("research_interest_tags", "Research interest topics"),
            ),
        ],
        "artifact_hints": {
            "writing_sample_link": "Link a strong analytical writing sample.",
        },
    },
    # 9 — Law / Policy / International Relations
    "law_policy": {
        "label": "Law · Policy · International Relations",
        "blurb": "LSAT readiness, writing, advocacy experience, and policy work.",
        "groups": [
            _g(
                "readiness",
                "Readiness",
                _b("lsat_flag", "LSAT planned / taken"),
                _r("policy_memo_familiarity", "Policy-memo structure familiarity"),
                _r("citation_familiarity", "Bluebook / Chicago citation familiarity"),
            ),
            _g(
                "experience",
                "Advocacy & experience",
                _b("debate_flag", "Debate experience"),
                _b("mock_trial_flag", "Mock-trial experience"),
                _b("model_un_flag", "Model UN experience"),
                _b("policy_research_flag", "Policy-research experience"),
                _tags(
                    "internships",
                    "Internships",
                    ("legislative", "NGO", "law firm", "government"),
                ),
            ),
            _g(
                "specialization",
                "Specialization & samples",
                _tags(
                    "issue_areas",
                    "Issue areas",
                    ("immigration", "security", "climate", "health", "human rights"),
                ),
                _tags("languages", "Languages"),
                _link("writing_sample_link", "Writing sample (memo / op-ed / paper)"),
            ),
        ],
        "artifact_hints": {
            "writing_sample_link": "A policy memo or analytical writing sample is key here.",
        },
    },
    # 10 — Education / Teaching / Counseling / Social Work
    "education_counseling": {
        "label": "Education · Counseling · Social Work",
        "blurb": "Teaching / tutoring experience, certifications, and fieldwork.",
        "groups": [
            _g(
                "experience",
                "Teaching / learner experience",
                _tags(
                    "learner_age_groups",
                    "Age groups taught",
                    ("early_childhood", "elementary", "middle", "high_school", "adult"),
                ),
                _tags(
                    "learner_settings",
                    "Settings",
                    ("tutoring", "classroom", "after_school", "online"),
                ),
                _num("teaching_hours_total", "Teaching / tutoring hours", unit="hours"),
                _b("lesson_plan_flag", "Lesson-plan experience"),
                _b("classroom_management_flag", "Classroom-management exposure"),
            ),
            _g(
                "credentials",
                "Credentials & fieldwork",
                _enum(
                    "teaching_license_progress",
                    "Teaching license progress",
                    ("none", "in_progress", "candidate", "licensed"),
                ),
                _b("practicum_flag", "Fieldwork / practicum"),
                _num("practicum_hours", "Practicum hours", unit="hours"),
                _b("licensure_pathway_interest_flag", "Licensure pathway interest"),
            ),
            _g(
                "counseling",
                "Counseling / social work",
                _b("counseling_exposure_flag", "Counseling exposure"),
                _b("crisis_intervention_flag", "Crisis-intervention training"),
                _r("counseling_theory_exposure", "Counseling-theory exposure (self-rating)"),
                _tags("populations_served", "Populations served"),
                _text("subject_area_depth", "Subject-area depth"),
            ),
        ],
        "artifact_hints": {},
    },
    # 11 — Journalism / Communications / Media
    "journalism_communications": {
        "label": "Journalism · Communications · Media",
        "blurb": "Published clips, beats, media tooling, and audience metrics.",
        "groups": [
            _g(
                "portfolio",
                "Clips & portfolio",
                _link("clips_portfolio_link", "Clips / published work"),
                _tags(
                    "clip_categories",
                    "Clip categories",
                    ("news", "feature", "investigative", "opinion", "video", "audio"),
                ),
                _b("publication_history_flag", "Publication history"),
                _tags("beats", "Beat / specialization"),
            ),
            _g(
                "tools",
                "Media tools (self-rating)",
                _r("tool_cms", "CMS"),
                _r("tool_video_editing", "Video editing"),
                _r("tool_audio_editing", "Audio editing"),
                _r("on_camera_comfort", "On-camera / on-mic comfort"),
            ),
            _g(
                "experience",
                "Experience & ethics",
                _tags("internships", "Internships", ("newsroom", "agency", "PR", "broadcast")),
                _b("editorial_workflow_flag", "Editorial-workflow exposure"),
                _b("social_analytics_flag", "Social / audience-analytics exposure"),
                _b("press_law_ethics_flag", "Ethics / law-of-press coursework"),
            ),
        ],
        "artifact_hints": {
            "clips_portfolio_link": "Link your strongest published clips.",
        },
    },
    # 12 — Pure Sciences (Math / Physics / Chemistry)
    "math_physics_chemistry_sciences": {
        "label": "Math · Physics · Chemistry · Natural Sciences",
        "blurb": "Subject readiness, research experience, and computational tools.",
        "groups": [
            _g(
                "math",
                "Mathematics readiness (self-rating)",
                _r("math_analysis", "Analysis / calculus depth"),
                _r("math_algebra", "Algebra / linear algebra"),
                _r("math_differential_equations", "Differential equations"),
                _r("math_probability_statistics", "Probability / statistics"),
            ),
            _g(
                "physics",
                "Physics readiness (self-rating)",
                _r("physics_classical_mechanics", "Classical mechanics"),
                _r("physics_em", "Electromagnetism"),
                _r("physics_quantum", "Quantum mechanics"),
                _r("physics_thermo", "Thermodynamics / statistical"),
            ),
            _g(
                "chemistry",
                "Chemistry readiness (self-rating)",
                _r("chem_general", "General chemistry"),
                _r("chem_organic", "Organic chemistry"),
                _r("chem_physical", "Physical chemistry"),
                _r("chem_analytical", "Analytical chemistry"),
                _r("lab_techniques", "Lab techniques"),
            ),
            _g(
                "research",
                "Research & competitions",
                _b("research_experience_flag", "Research experience (lab / PI)"),
                _num("lab_hours_total", "Lab hours (total)", unit="hours"),
                _link("research_output_link", "Research output / DOI"),
                _text("competition_placements", "Competition placements (Putnam / olympiads)"),
                _r("computational_tools", "Computational tools (self-rating)"),
                _b("gre_subject_readiness_flag", "GRE subject-test readiness"),
            ),
        ],
        "artifact_hints": {
            "research_output_link": "Link a paper, poster, or research summary.",
        },
    },
    # 13 — Computer Engineering / Embedded / Robotics
    "comp_engineering_robotics": {
        "label": "Computer Engineering · Embedded · Robotics",
        "blurb": "Embedded programming, hardware, and robotics-stack readiness.",
        "groups": [
            _g(
                "embedded",
                "Embedded (self-rating)",
                _r("embedded_c_cpp", "C / C++"),
                _r("embedded_microcontrollers", "Microcontrollers"),
                _r("embedded_rtos", "RTOS"),
                _tags(
                    "microcontroller_platforms",
                    "Platforms used",
                    ("Arduino", "STM32", "Raspberry Pi", "ESP32", "FPGA"),
                ),
            ),
            _g(
                "hardware",
                "Hardware",
                _b("pcb_design_flag", "PCB design experience"),
                _b("fpga_flag", "FPGA experience"),
                _b("hardware_debugging_flag", "Hardware debugging (scope / logic analyzer)"),
                _b("sensor_integration_flag", "Sensor / actuator integration"),
            ),
            _g(
                "robotics",
                "Robotics (self-rating)",
                _r("robotics_ros", "ROS"),
                _r("robotics_control", "Control"),
                _r("robotics_perception", "Perception"),
                _r("robotics_slam", "SLAM"),
            ),
            _g(
                "evidence",
                "Teams & portfolio",
                _tags(
                    "competition_teams",
                    "Competition teams",
                    ("FRC", "FTC", "VEX", "RoboCup", "DARPA"),
                ),
                _link("project_portfolio_link", "Project portfolio"),
            ),
        ],
        "artifact_hints": {
            "project_portfolio_link": "Link a robotics / embedded project with build details.",
        },
    },
    # 14 — Environmental / Sustainability / Energy
    "environmental_sustainability": {
        "label": "Environmental · Sustainability · Energy",
        "blurb": "Field/lab methods, GIS, sustainability frameworks, and policy exposure.",
        "groups": [
            _g(
                "methods",
                "Methods (self-rating)",
                _r("gis_proficiency", "GIS proficiency (ArcGIS / QGIS)"),
                _r("environmental_modeling", "Environmental / data modeling"),
                _r("tool_matlab_python_r", "MATLAB / Python / R"),
            ),
            _g(
                "field",
                "Field & lab",
                _b("field_experience_flag", "Field experience (sampling / fieldwork)"),
                _num("fieldwork_hours", "Fieldwork hours", unit="hours"),
                _num("lab_hours_total", "Lab hours (total)", unit="hours"),
            ),
            _g(
                "frameworks",
                "Frameworks & policy",
                _tags(
                    "sustainability_frameworks",
                    "Frameworks",
                    ("LCA", "ESG", "carbon accounting", "circular economy"),
                ),
                _b("energy_systems_coursework_flag", "Energy-systems coursework"),
                _b("policy_exposure_flag", "Policy exposure"),
                _tags("certifications", "Certifications", ("LEED", "GIS", "OSHA")),
                _link("sustainability_portfolio_link", "Sustainability project portfolio"),
            ),
        ],
        "artifact_hints": {
            "sustainability_portfolio_link": "Link a field study or sustainability project.",
        },
    },
    # 15 — Languages / Linguistics / Translation
    "language_linguistics": {
        "label": "Languages · Linguistics · Translation",
        "blurb": "Language proficiencies, translation experience, and linguistics subfields.",
        "groups": [
            _g(
                "proficiency",
                "Language proficiency",
                _tags("languages", "Languages (with CEFR/ACTFL level)"),
                _enum(
                    "proof_type",
                    "Proof type",
                    ("self_report", "test_certificate"),
                ),
            ),
            _g(
                "linguistics",
                "Linguistics subfields (self-rating)",
                _r("ling_phonology", "Phonology / phonetics"),
                _r("ling_syntax", "Syntax"),
                _r("ling_semantics", "Semantics"),
                _r("ling_sociolinguistics", "Sociolinguistics"),
            ),
            _g(
                "experience",
                "Translation & field",
                _b("translation_experience_flag", "Translation / interpreting experience"),
                _b("fieldwork_flag", "Field-work"),
                _b("cat_tools_flag", "CAT tools"),
                _link("target_language_sample_link", "Writing sample (target language)"),
                _text("publications", "Publications"),
            ),
        ],
        "artifact_hints": {
            "target_language_sample_link": "Link a translation or target-language writing sample.",
        },
    },
    # 16 — Entrepreneurship / Product / Innovation
    "entrepreneurship_product": {
        "label": "Entrepreneurship · Product · Innovation",
        "blurb": "Ventures, product work, fundraising, and hybrid technical+business skills.",
        "groups": [
            _g(
                "ventures",
                "Ventures",
                _b("startup_experience_flag", "Startup experience (founder / early)"),
                _enum(
                    "venture_stage",
                    "Furthest venture stage",
                    ("idea", "prototype", "launched", "revenue", "funded", "none"),
                ),
                _text("traction_metrics", "Traction metrics (users / revenue / growth)"),
                _b("revenue_traction_flag", "Revenue / traction available"),
            ),
            _g(
                "product",
                "Product work",
                _b("shipped_product_flag", "Shipped a product"),
                _link("product_artifacts_link", "PRD / spec / product artifacts"),
                _b("user_research_flag", "User-research experience"),
                _b("go_to_market_flag", "Go-to-market experience"),
            ),
            _g(
                "growth",
                "Fundraising & skills",
                _b("fundraising_flag", "Fundraising experience"),
                _b("accelerator_flag", "Accelerator participation"),
                _b("ip_patent_flag", "IP / patent exposure"),
                _text("pitch_competition_placements", "Pitch / competition placements"),
                _r("technical_skill", "Technical skill (self-rating)"),
                _r("business_skill", "Business skill (self-rating)"),
            ),
        ],
        "artifact_hints": {
            "product_artifacts_link": "Link a PRD, demo, or shipped product.",
        },
    },
}


# ── CIP / major → track mapping (Spec 43 §18 / Spec 42 §9 open question) ──────
# The authoritative map from a student's stated major to track_key(s). Keyed by
# lower-case substrings matched against ``field_of_study`` / a CIP title; some
# majors map to multiple tracks (dual-target). Order is irrelevant — all matches
# activate. CIP-2020 two-digit families are included as a coarse fallback.
_MAJOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "cs_data_ai": (
        "computer science",
        "data science",
        "data analytics",
        "machine learning",
        "artificial intelligence",
        " ai ",
        "informatics",
        "software",
        "cybersecurity",
        "information systems",
        "computational",
    ),
    "comp_engineering_robotics": (
        "computer engineering",
        "embedded",
        "robotics",
        "mechatronics",
    ),
    "engineering": (
        "mechanical engineering",
        "electrical engineering",
        "civil engineering",
        "aerospace",
        "chemical engineering",
        "industrial engineering",
        "materials engineering",
        "biomedical engineering",
        "structural engineering",
    ),
    "business": (
        "business",
        "finance",
        "marketing",
        "accounting",
        "economics",
        "management",
        "supply chain",
        "operations",
        "analytics",
    ),
    "entrepreneurship_product": (
        "entrepreneurship",
        "product management",
        "innovation",
        "venture",
    ),
    "health": (
        "pre-med",
        "premed",
        "nursing",
        "public health",
        "medicine",
        "biomedical sciences",
        "kinesiology",
        "nutrition",
        "pharmacy",
        "health sciences",
        "epidemiology",
    ),
    "arts_design": (
        "art",
        "design",
        "architecture",
        "graphic",
        "fashion",
        "media arts",
        "industrial design",
        "fine arts",
        "illustration",
        "animation",
        "photography",
    ),
    "performing_arts": (
        "music",
        "theater",
        "theatre",
        "dance",
        "performing arts",
        "drama",
        "acting",
    ),
    "humanities_social_sciences": (
        "history",
        "philosophy",
        "sociology",
        "anthropology",
        "psychology",
        "political science",
        "social science",
        "humanities",
        "religious studies",
        "gender studies",
        "geography",
    ),
    "law_policy": (
        "law",
        "pre-law",
        "prelaw",
        "policy",
        "public policy",
        "international relations",
        "criminal justice",
        "legal",
    ),
    "education_counseling": (
        "education",
        "teaching",
        "counseling",
        "social work",
        "early childhood",
    ),
    "journalism_communications": (
        "journalism",
        "communication",
        "media studies",
        "public relations",
        "broadcasting",
        "advertising",
    ),
    "math_physics_chemistry_sciences": (
        "mathematics",
        "physics",
        "chemistry",
        "biochemistry",
        "astronomy",
        "statistics",
        "biology",
        "neuroscience",
        "geology",
        "natural science",
    ),
    "environmental_sustainability": (
        "environmental",
        "sustainability",
        "energy",
        "climate",
        "ecology",
        "conservation",
        "earth science",
    ),
    "language_linguistics": (
        "linguistics",
        "translation",
        "interpreting",
        "language",
        "literature",
        "comparative literature",
        "classics",
    ),
}

# CIP-2020 two-digit family → track_key (coarse fallback when the title is a code).
_CIP_FAMILY: dict[str, str] = {
    "11": "cs_data_ai",
    "14": "engineering",
    "15": "engineering",
    "52": "business",
    "45": "humanities_social_sciences",
    "42": "humanities_social_sciences",
    "54": "humanities_social_sciences",
    "22": "law_policy",
    "44": "law_policy",
    "13": "education_counseling",
    "09": "journalism_communications",
    "10": "journalism_communications",
    "50": "arts_design",
    "04": "arts_design",
    "26": "math_physics_chemistry_sciences",
    "27": "math_physics_chemistry_sciences",
    "40": "math_physics_chemistry_sciences",
    "51": "health",
    "60": "health",
    "03": "environmental_sustainability",
    "16": "language_linguistics",
    "23": "language_linguistics",
}


# ── Public helpers ────────────────────────────────────────────────────────────
def is_valid_track(track_key: str) -> bool:
    return track_key in _TRACKS


def track_schema(track_key: str) -> dict | None:
    """The full schema for one track (label, blurb, groups), or None."""
    t = _TRACKS.get(track_key)
    if t is None:
        return None
    return {"track_key": track_key, **{k: v for k, v in t.items() if k != "recommendation"}}


def catalog() -> list[dict]:
    """All 15 track schemas in registry order (for the /catalog endpoint + FE)."""
    return [track_schema(k) for k in TRACK_KEYS if k in _TRACKS]


def track_fields(track_key: str) -> dict[str, dict]:
    """Flat {field_key: field_def} for a track (validation + scoring)."""
    t = _TRACKS.get(track_key)
    if not t:
        return {}
    out: dict[str, dict] = {}
    for grp in t["groups"]:
        for f in grp["fields"]:
            out[f["key"]] = f
    return out


def rating_field_keys(track_key: str) -> list[str]:
    """Keys of the 1–5 self-rating fields — the basis of the fit score."""
    return [k for k, f in track_fields(track_key).items() if f["kind"] == "rating_1_5"]


def recommendation_clusters(track_key: str) -> dict[str, tuple[str, ...]]:
    """Sub-track → rating-field keys, for §4.18 track_recommendation. {} if none."""
    return dict(_TRACKS.get(track_key, {}).get("recommendation", {}))


def artifact_hints(track_key: str) -> dict[str, str]:
    """{evidence_field_key: human hint} for §4.18 suggested_artifacts_to_add."""
    return dict(_TRACKS.get(track_key, {}).get("artifact_hints", {}))


def infer_tracks_from_major(field_of_study: str | None) -> list[str]:
    """Map a free-text major / CIP title to track_key(s) (Spec 43 §1).

    Returns every track whose keyword set matches; multi-track majors (e.g.
    "Computer Engineering") legitimately activate more than one. Empty when the
    major is unknown/blank — the student can still activate tracks manually.
    """
    if not field_of_study:
        return []
    text = f" {field_of_study.strip().lower()} "
    hits: list[str] = []
    for track_key, kws in _MAJOR_KEYWORDS.items():
        if any(kw in text for kw in kws):
            hits.append(track_key)
    # CIP-code fallback: a leading two-digit family.
    if not hits:
        digits = field_of_study.strip()[:2]
        fam = _CIP_FAMILY.get(digits)
        if fam:
            hits.append(fam)
    # Keep registry order, dedupe.
    return [k for k in TRACK_KEYS if k in set(hits)]
