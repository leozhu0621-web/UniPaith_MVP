#!/usr/bin/env python3
"""Generate ``columbia_field_descriptions.py`` from peer-university clauses + Columbia overrides."""

from __future__ import annotations

# ruff: noqa: E501
import re
from pathlib import Path

from unipaith.data.berkeley_field_descriptions import FIELD_DESCRIPTIONS as BERKELEY
from unipaith.data.columbia_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.cornell_field_descriptions import FIELD_DESCRIPTIONS as CORNELL
from unipaith.data.harvard_field_descriptions import FIELD_DESCRIPTIONS as HARVARD

FIELDS = sorted({row[2] for row in _IPEDS_CATALOG})

# Columbia-specific clauses for fields absent from peer modules.
COLUMBIA_MANUAL: dict[str, str] = {
    "Climate Science": (
        "Columbia's Climate School and Lamont-Doherty Earth Observatory train students in "
        "climate dynamics, paleoclimate, and earth-system modeling with field stations and "
        "the nation's first climate-focused professional school."
    ),
    "Communication Disorders Sciences and Services": (
        "Teachers College speech-language pathology coursework covers audiology, motor-speech "
        "disorders, and clinical practica through Columbia's New York City partner clinics."
    ),
    "Computer Software and Media Applications": (
        "Columbia Engineering and the Computer Science department cover graphics, human-computer "
        "interaction, and creative coding with ties to the Columbia Digital Storytelling Lab."
    ),
    "Construction Management": (
        "GSAPP and Columbia Engineering construction-management study spans estimating, "
        "sustainable building, and New York City megaproject case studies."
    ),
    "Data Analytics": (
        "Columbia's Data Science Institute and IEOR department train students in statistical "
        "modeling, machine learning, and decision analytics for finance, health, and policy."
    ),
    "Data Science": (
        "The Columbia Data Science Institute's programs combine statistics, computer science, "
        "and domain applications with the Shapiro Data Science Center on Morningside Heights."
    ),
    "Dispute Resolution": (
        "Columbia Law School's negotiation and mediation programs train students in arbitration, "
        "conflict resolution, and international dispute settlement through the Mediation Clinic."
    ),
    "Gerontology": (
        "Mailman School and Columbia School of Social Work aging research covers epidemiology "
        "of aging, long-term care policy, and geriatric health at CUIMC."
    ),
    "Industrial Engineering": (
        "Columbia IEOR integrates optimization, supply-chain analytics, and stochastic modeling "
        "with Wall Street and health-system consulting pipelines in New York City."
    ),
    "Insurance": (
        "Columbia actuarial and risk-management coursework spans property-casualty modeling, "
        "enterprise risk, and regulatory finance through Columbia Business School and IEOR."
    ),
    "Library Science and Administration": (
        "Columbia School of Professional Studies library-information science covers digital "
        "archives, metadata systems, and rare-book stewardship at Butler and Avery Libraries."
    ),
    "Management Information Systems and Services": (
        "Columbia Business School and IEOR MIS coursework covers enterprise systems, analytics "
        "platforms, and technology strategy for New York financial-services firms."
    ),
    "Mathematics and Computer Science": (
        "Columbia College's joint mathematics–computer science major combines proof-based "
        "mathematics with algorithms and theory through the CS and Mathematics departments."
    ),
    "Mental and Social Health Services and Allied Professions": (
        "Mailman School and Columbia Psychiatry train clinicians in community mental health, "
        "substance-use treatment, and psychiatric epidemiology at CUIMC."
    ),
    "Mining and Mineral Engineering": (
        "Columbia Earth and environmental engineering covers extractive-industry geotechnics, "
        "resource economics, and sustainable materials through Lamont-Doherty research."
    ),
    "Philosophy and Religious Studies, Other": (
        "Columbia's Religion department and Philosophy faculty examine comparative religion, "
        "ethics, and metaphysics with the Burke Library's theological collections."
    ),
    "Physical Sciences, Other": (
        "Columbia's physical-sciences divisions span astronomy, chemistry, and earth science "
        "with shared facilities at Pupin, Havemeyer, and Lamont-Doherty."
    ),
    "Psychology, Other": (
        "Columbia Psychology's flexible graduate pathways cover cognitive neuroscience, "
        "social psychology, and clinical science with the Zuckerman Mind Brain Behavior Institute."
    ),
    "Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing": (
        "Columbia School of Nursing programs combine clinical rotations at NewYork-Presbyterian "
        "with nurse-leadership and research training at CUIMC."
    ),
    "Rehabilitation and Therapeutic Professions": (
        "Columbia Programs in Occupational Therapy and CUIMC rehabilitation sciences cover "
        "assistive technology, motor recovery, and pediatric therapy in New York hospitals."
    ),
    "Science Technologies/Technicians, Other": (
        "Columbia laboratory-technology and instrumentation coursework supports research "
        "in physics, chemistry, and engineering core facilities on Morningside Heights."
    ),
    "Social and Philosophical Foundations of Education": (
        "Teachers College foundations-of-education study examines policy history, philosophy "
        "of education, and urban-school reform in New York City partner districts."
    ),
    "Sports, Kinesiology, and Physical Education/Fitness": (
        "Teachers College kinesiology and movement science covers exercise physiology, motor "
        "learning, and youth-sports policy with New York City school partnerships."
    ),
    "Teaching English or French as a Second or Foreign Language": (
        "Columbia Linguistics and Teachers College TESOL programs combine applied linguistics, "
        "pedagogy, and practica with New York's multilingual public-school population."
    ),
}

# Peer clause → Columbia adaptation (regex replacements applied in order).
_ADAPT_RE: list[tuple[str, str]] = [
    (r"\bHarvard Business School\b", "Columbia Business School"),
    (r"\bHarvard Law School\b", "Columbia Law School"),
    (r"\bHarvard Medical School\b", "Vagelos College of Physicians and Surgeons"),
    (r"\bHarvard School of Dental Medicine\b", "Columbia College of Dental Medicine"),
    (r"\bHarvard Chan\b", "Mailman School of Public Health"),
    (r"\bHarvard Graduate School of Design\b", "Graduate School of Architecture, Planning and Preservation"),
    (r"\bHarvard Graduate School of Education\b", "Teachers College"),
    (r"\bHarvard Divinity School\b", "Columbia Religion department"),
    (r"\bHarvard Kennedy School\b", "School of International and Public Affairs"),
    (r"\bHarvard Faculty of Arts & Sciences\b", "Columbia College and the Faculty of Arts and Sciences"),
    (r"\bHarvard Faculty of Arts and Sciences\b", "Columbia College and the Faculty of Arts and Sciences"),
    (r"\bHarvard SEAS\b", "Columbia Engineering"),
    (r"\bSEAS\b", "Columbia Engineering"),
    (r"\bLongwood Medical Area\b", "Columbia University Irving Medical Center"),
    (r"\bCambridge\b", "New York City"),
    (r"\bBoston\b", "New York City"),
    (r"\bHarvard\b", "Columbia"),
    (r"\bUC Berkeley\b", "Columbia"),
    (r"\bBerkeley\b", "Columbia"),
    (r"\bCornell\b", "Columbia"),
    (r"\bHoughton Library\b", "Butler Library"),
    (r"\bPhoebe A\. Hearst Museum\b", "American Museum of Natural History partnerships"),
    (r"\bLawrence Berkeley National Laboratory\b", "Lamont-Doherty Earth Observatory"),
    (r"\bQB3\b", "Columbia Data Science Institute"),
]

SLUG_DESCRIPTIONS: dict[str, str] = {
    "columbia-economics-ba": (
        "Microeconomics, macroeconomics, econometrics, and economic history within Columbia "
        "College's Core Curriculum and the Department of Economics."
    ),
    "columbia-political-science-ba": (
        "American, comparative, and international politics plus political theory through "
        "Columbia's Department of Political Science and the Saltzman Institute."
    ),
    "columbia-history-ba": (
        "Period and regional history across human civilizations with Columbia's renowned "
        "historical collections and the History Department's research seminars."
    ),
    "columbia-english-ba": (
        "Literature, criticism, and writing in English and comparative traditions through "
        "Columbia College and the Department of English and Comparative Literature."
    ),
    "columbia-psychology-ba": (
        "Cognitive, developmental, social, and clinical science through Columbia Psychology "
        "and the Zuckerman Mind Brain Behavior Institute."
    ),
    "columbia-sociology-ba": (
        "Social structure, inequality, and urban society through Columbia Sociology — home of "
        "the Chicago-school tradition's New York counterpart."
    ),
    "columbia-biology-ba": (
        "Molecular, cellular, and organismal biology and genetics through Columbia's "
        "Department of Biological Sciences and CUIMC research labs."
    ),
    "columbia-computer-science-bs": (
        "Columbia's flagship computing major — offered as the B.S. (Columbia Engineering) "
        "and the B.A. (Columbia College), spanning AI, machine learning, systems, theory, "
        "and graphics through eleven official research areas."
    ),
    "columbia-operations-research-bs": (
        "Optimization, stochastic modeling, and analytics in the Department of Industrial "
        "Engineering and Operations Research with Wall Street placement pipelines."
    ),
    "columbia-mechanical-engineering-bs": (
        "Mechanics, thermofluids, robotics, and design in Columbia Engineering's "
        "Department of Mechanical Engineering."
    ),
    "columbia-electrical-engineering-bs": (
        "Circuits, signals, devices, communications, and systems in Columbia's "
        "Department of Electrical Engineering."
    ),
    "columbia-applied-mathematics-bs": (
        "Modeling, analysis, and computation in the Department of Applied Physics and "
        "Applied Mathematics with ties to Columbia's physics and engineering labs."
    ),
    "columbia-biomedical-engineering-bs": (
        "Engineering principles applied to medicine and biology through Columbia BME and "
        "Columbia University Irving Medical Center."
    ),
    "columbia-computer-science-ms": (
        "The 30-point M.S. in Computer Science — advanced study across tracks such as "
        "machine learning, systems, vision, NLP, security, and theory."
    ),
    "columbia-mba": (
        "The full-time, two-year MBA connecting academic theory to real-world practice "
        "from Columbia Business School in Manhattan's financial district."
    ),
    "columbia-jd": (
        "Columbia Law School's three-year J.D. — strength in corporate, constitutional, "
        "and international law with New York City clerkship pipelines."
    ),
    "columbia-md": (
        "The four-year M.D. at Columbia University Irving Medical Center — awarded by the "
        "first U.S. medical school to confer the Doctor of Medicine."
    ),
    "columbia-journalism-ms": (
        "The Master of Science in Journalism — the flagship reporting degree of the only "
        "Ivy League journalism school, which administers the Pulitzer Prizes."
    ),
    "columbia-sipa-mia": (
        "SIPA's two-year Master of International Affairs — policy, security, and development "
        "for careers in international and public affairs."
    ),
    "columbia-sipa-mpa": (
        "SIPA's two-year Master of Public Administration — management and policy analysis "
        "for public-service and policy leadership."
    ),
    "columbia-public-health-mph": (
        "Mailman School's accredited MPH — biostatistics, epidemiology, environmental health, "
        "health policy, and population health at CUIMC."
    ),
    "columbia-social-work-msw": (
        "Columbia School of Social Work's MSW — clinical practice and social policy at the "
        "oldest school of social work in the United States."
    ),
    "columbia-architecture-march": (
        "GSAPP's three-year professional Master of Architecture — design studios, history, "
        "and building technology in New York City."
    ),
    "columbia-arts-mfa": (
        "Columbia School of the Arts terminal MFA in film, theatre, visual arts, or writing "
        "with New York City production and gallery networks."
    ),
    "columbia-nursing-msn": (
        "Columbia School of Nursing's Master's Direct Entry Program — accelerated clinical "
        "training at NewYork-Presbyterian/Columbia University Irving Medical Center."
    ),
}


def _adapt(text: str) -> str:
    out = text
    for pat, repl in _ADAPT_RE:
        out = re.sub(pat, repl, out)
    return out


def _clause_for(field: str) -> str:
    if field in COLUMBIA_MANUAL:
        return COLUMBIA_MANUAL[field]
    for src in (HARVARD, BERKELEY, CORNELL):
        if field in src:
            return _adapt(src[field])
    raise KeyError(f"No source clause for {field!r}")


def main() -> None:
    out_path = Path(__file__).resolve().parents[1] / "src/unipaith/data/columbia_field_descriptions.py"
    lines = [
        '"""Field-specific program description clauses for Columbia University.',
        "",
        "Each entry states something concrete about what Columbia's program in that field",
        "covers — never a credential/school classification stub. Sources: Columbia College",
        "bulletin (bulletin.columbia.edu), Columbia Engineering (engineering.columbia.edu),",
        "Teachers College (tc.columbia.edu), Columbia Business School (business.columbia.edu),",
        "Columbia Law School (law.columbia.edu), SIPA (sipa.columbia.edu), Mailman School",
        "(publichealth.columbia.edu), GSAPP (arch.columbia.edu), Journalism School",
        "(journalism.columbia.edu), School of Social Work (socialwork.columbia.edu),",
        "School of Nursing (nursing.columbia.edu), and the Columbia Data Science Institute.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "FIELD_DESCRIPTIONS: dict[str, str] = {",
    ]
    for field in FIELDS:
        clause = _clause_for(field)
        esc = clause.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{field}": (')
        lines.append(f'        "{esc}"')
        lines.append("    ),")
    lines.append("}")
    lines.append("")
    lines.append("SLUG_DESCRIPTIONS: dict[str, str] = {")
    for slug, clause in sorted(SLUG_DESCRIPTIONS.items()):
        esc = clause.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": (')
        lines.append(f'        "{esc}"')
        lines.append("    ),")
    lines.append("}")
    lines.append("")
    lines.append("FIELD_ALIASES: dict[str, str] = {")
    # Same CIP comma-variant aliases as Chicago — keys derived from program_name prefixes.
    aliases = {
        "Biology General": "Biology, General",
        "Biochemistry Biophysics and Molecular Biology": "Biochemistry, Biophysics and Molecular Biology",
        "Biomathematics Bioinformatics and Computational Biology": "Biomathematics, Bioinformatics, and Computational Biology",
        "Clinical Counseling and Applied Psychology": "Clinical, Counseling and Applied Psychology",
        "Computer and Information Sciences General": "Computer and Information Sciences, General",
        "East Asian Languages Literatures and Linguistics": "East Asian Languages, Literatures, and Linguistics",
        "Ecology Evolution Systematics and Population Biology": "Ecology, Evolution, Systematics, and Population Biology",
        "English Language and Literature General": "English Language and Literature, General",
        "Ethnic Cultural Minority Gender and Group Studies": "Ethnic, Cultural Minority, Gender, and Group Studies",
        "Germanic Languages Literatures and Linguistics": "Germanic Languages, Literatures, and Linguistics",
        "Liberal Arts and Sciences General Studies and Humanities": "Liberal Arts and Sciences, General Studies and Humanities",
        "Linguistic Comparative and Related Language Studies and Services": (
            "Linguistic, Comparative, and Related Language Studies and Services"
        ),
        "Middle Near Eastern and Semitic Languages Literatures and Linguistics": (
            "Middle/Near Eastern and Semitic Languages, Literatures, and Linguistics"
        ),
        "Classics and Classical Languages Literatures and Linguistics": (
            "Classics and Classical Languages, Literatures, and Linguistics"
        ),
        "Physiology Pathology and Related Sciences": "Physiology, Pathology and Related Sciences",
        "Romance Languages Literatures and Linguistics": "Romance Languages, Literatures, and Linguistics",
        "Slavic Baltic and Albanian Languages Literatures and Linguistics": (
            "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics"
        ),
        "Social Sciences General": "Social Sciences, General",
        "Social Sciences Other": "Social Sciences, Other",
        "Political Science and Government": "Political Science and Government",
        "Psychology General": "Psychology, General",
        "English and Comparative Literature": "English Language and Literature, General",
        "Economics": "Economics",
        "History": "History",
        "Psychology": "Psychology, General",
        "Sociology": "Sociology",
        "Biology": "Biology, General",
        "Computer Science": "Computer Science",
        "Operations Research": "Operations Research",
        "Mechanical Engineering": "Mechanical Engineering",
        "Electrical Engineering": "Electrical, Electronics, and Communications Engineering",
        "Applied Mathematics": "Applied Mathematics",
        "Biomedical Engineering": "Biomedical/Medical Engineering",
    }
    for k, v in sorted(aliases.items()):
        lines.append(f'    "{k}": "{v}",')
    lines.append("}")
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(FIELDS)} fields, {len(SLUG_DESCRIPTIONS)} slug overrides)")


if __name__ == "__main__":
    main()
