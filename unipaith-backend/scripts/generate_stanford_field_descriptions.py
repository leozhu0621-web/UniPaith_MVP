#!/usr/bin/env python3
"""Generate ``stanford_field_descriptions.py`` from peer-university clauses + Stanford overrides."""

from __future__ import annotations

# ruff: noqa: E501
import re
from pathlib import Path

from unipaith.data.berkeley_field_descriptions import FIELD_DESCRIPTIONS as BERKELEY
from unipaith.data.columbia_field_descriptions import FIELD_DESCRIPTIONS as COLUMBIA
from unipaith.data.cornell_field_descriptions import FIELD_DESCRIPTIONS as CORNELL
from unipaith.data.harvard_field_descriptions import FIELD_DESCRIPTIONS as HARVARD
from unipaith.data.jhu_field_descriptions import FIELD_DESCRIPTIONS as JHU
from unipaith.data.northwestern_field_descriptions import FIELD_DESCRIPTIONS as NORTHWESTERN
from unipaith.data.penn_field_descriptions import FIELD_DESCRIPTIONS as PENN
from unipaith.data.stanford_ipeds_catalog import _IPEDS_CATALOG

FIELDS = sorted({row[2] for row in _IPEDS_CATALOG})

# Stanford-specific clauses for fields absent from peer modules.
STANFORD_MANUAL: dict[str, str] = {
    "Allied Health and Medical Assisting Services": (
        "Stanford Medicine allied-health pathways cover clinical assisting, patient-care "
        "coordination, and health-system operations within Stanford Health Care partner sites."
    ),
    "Business, Management, Marketing, and Related Support Services, Other": (
        "Stanford Graduate School of Business and the School of Humanities and Sciences offer "
        "interdisciplinary management studies spanning entrepreneurship, product marketing, and "
        "technology commercialization in Silicon Valley ventures."
    ),
    "English Language and Literature/Letters, Other": (
        "Stanford's Department of English and Creative Writing programs span literary history, "
        "critical theory, and workshop-based writing with the Stanford Humanities Center."
    ),
    "Chemical Engineering": (
        "Reaction engineering, transport phenomena, and materials processing in Stanford "
        "School of Engineering's Department of Chemical Engineering."
    ),
    "Teacher Education and Professional Development, Specific Levels and Methods": (
        "Stanford GSE teacher-preparation programs lead to California credential pathways "
        "with Peninsula partner-school clinical practice."
    ),
    "Teacher Education and Professional Development, Specific Subject Areas": (
        "Stanford GSE subject-specific teacher education pairs content expertise with "
        "pedagogy and classroom placements in Bay Area school districts."
    ),
    "Petroleum Engineering": (
        "Stanford's Energy Resources Engineering group trains students in subsurface energy "
        "systems, reservoir engineering, and the geoscience of oil and gas within the School "
        "of Engineering's sustainability-focused energy curriculum."
    ),
}

# Peer clause → Stanford adaptation (regex replacements applied in order).
_ADAPT_RE: list[tuple[str, str]] = [
    (r"\bHarvard Business School\b", "Stanford Graduate School of Business"),
    (r"\bHarvard Law School\b", "Stanford Law School"),
    (r"\bHarvard Medical School\b", "Stanford School of Medicine"),
    (r"\bHarvard School of Dental Medicine\b", "Stanford School of Medicine"),
    (r"\bHarvard Chan\b", "Stanford School of Medicine"),
    (r"\bHarvard Graduate School of Design\b", "School of Humanities and Sciences"),
    (r"\bHarvard Graduate School of Education\b", "Graduate School of Education"),
    (r"\bHarvard Divinity School\b", "Department of Religious Studies"),
    (r"\bHarvard Kennedy School\b", "Freeman Spogli Institute for International Studies"),
    (r"\bHarvard Faculty of Arts & Sciences\b", "School of Humanities and Sciences"),
    (r"\bHarvard Faculty of Arts and Sciences\b", "School of Humanities and Sciences"),
    (r"\bHarvard SEAS\b", "Stanford School of Engineering"),
    (r"\bSEAS\b", "Stanford School of Engineering"),
    (r"\bColumbia Business School\b", "Stanford Graduate School of Business"),
    (r"\bColumbia Law School\b", "Stanford Law School"),
    (r"\bVagelos College of Physicians and Surgeons\b", "Stanford School of Medicine"),
    (r"\bColumbia University Irving Medical Center\b", "Stanford Medicine"),
    (r"\bColumbia College and the Faculty of Arts and Sciences\b", "School of Humanities and Sciences"),
    (r"\bColumbia Engineering\b", "Stanford School of Engineering"),
    (r"\bTeachers College\b", "Graduate School of Education"),
    (r"\bMailman School of Public Health\b", "Stanford School of Medicine"),
    (r"\bGraduate School of Architecture, Planning and Preservation\b", "School of Humanities and Sciences"),
    (r"\bLongwood Medical Area\b", "Stanford Medicine campus"),
    (r"\bCambridge\b", "Palo Alto"),
    (r"\bBoston\b", "Palo Alto"),
    (r"\bNew York City\b", "Silicon Valley"),
    (r"\bManhattan\b", "Silicon Valley"),
    (r"\bMorningside Heights\b", "the Stanford campus"),
    (r"\bHarvard\b", "Stanford"),
    (r"\bColumbia\b", "Stanford"),
    (r"\bUC Berkeley\b", "Stanford"),
    (r"\bBerkeley\b", "Stanford"),
    (r"\bCornell\b", "Stanford"),
    (r"\bHoughton Library\b", "Stanford University Libraries"),
    (r"\bLawrence Berkeley National Laboratory\b", "SLAC National Accelerator Laboratory"),
    (r"\bLamont-Doherty Earth Observatory\b", "Stanford Doerr School of Sustainability"),
    (r"\bQB3\b", "Stanford Institute for Human-Centered AI"),
]

SLUG_DESCRIPTIONS: dict[str, str] = {
    "stanford-cs-ms": (
        "Stanford's flexible 45-unit M.S. in Computer Science spans ten official specializations "
        "— including AI, systems, theory, and HCI — with research ties to the Stanford AI Lab."
    ),
    "stanford-cs-bs": (
        "Stanford's most popular undergraduate major covers algorithms, systems, AI, and theory "
        "through the School of Engineering's Computer Science department."
    ),
    "stanford-cs-phd": (
        "A fully funded doctoral program producing researchers in theory, systems, AI, and "
        "human-computer interaction across Stanford CS and affiliated labs."
    ),
    "stanford-ee-ms": (
        "The M.S. in Electrical Engineering spans integrated circuits, photonics, signal "
        "processing, and information systems in the Stanford School of Engineering."
    ),
    "stanford-me-ms": (
        "Graduate mechanical engineering at Stanford covers design, robotics, biomechanics, "
        "and energy systems with the Center for Design Research and autonomous-vehicle labs."
    ),
    "stanford-me-bs": (
        "Undergraduate mechanical engineering combines mechanics, thermofluids, and product "
        "design with hands-on prototyping in the School of Engineering."
    ),
    "stanford-cee-ms": (
        "Civil and environmental engineering graduate study spans structures, geotechnics, "
        "and sustainable water systems at the Stanford Doerr School of Sustainability."
    ),
    "stanford-aa-ms": (
        "Aeronautics and astronautics graduate training covers spacecraft design, controls, "
        "and propulsion with ties to NASA Ames and Stanford's autonomous-systems research."
    ),
    "stanford-bioe-bs": (
        "Undergraduate bioengineering integrates device design, biomaterials, and physiology "
        "at the interface of engineering and Stanford Medicine."
    ),
    "stanford-mse-ms": (
        "Management Science and Engineering combines optimization, analytics, and technology "
        "strategy — a signature Stanford program linking engineering and the GSB ecosystem."
    ),
    "stanford-economics-bs": (
        "Undergraduate economics at Stanford covers micro, macro, econometrics, and policy "
        "with the Stanford Institute for Economic Policy Research."
    ),
    "stanford-economics-phd": (
        "Doctoral economics at Stanford trains scholars in theory, empirical micro, and "
        "macroeconomics with the Stanford Institute for Economic Policy Research."
    ),
    "stanford-human-biology-bs": (
        "Human Biology integrates life sciences, health policy, and social context — a "
        "Stanford interdisciplinary major bridging biology and society."
    ),
    "stanford-symbolic-systems-bs": (
        "Symbolic Systems examines cognition, computation, language, and philosophy — "
        "Stanford's signature interdisciplinary major feeding AI and cognitive-science research."
    ),
    "stanford-mathematics-bs": (
        "Undergraduate mathematics spans pure and applied study with undergraduate research "
        "in the Department of Mathematics and ICME."
    ),
    "stanford-political-science-bs": (
        "Political science undergraduates study American politics, comparative government, "
        "and political theory through the Freeman Spogli Institute network."
    ),
    "stanford-international-relations-bs": (
        "International relations combines security studies, political economy, and area "
        "expertise through Stanford's Center for International Security and Cooperation."
    ),
    "stanford-psychology-bs": (
        "Undergraduate psychology covers cognitive, social, developmental, and neuroscience "
        "foundations in one of the nation's top-ranked psychology departments."
    ),
    "stanford-english-bs": (
        "English and creative writing at Stanford spans literary history, criticism, and "
        "workshop-based fiction and poetry through the Creative Writing Program."
    ),
    "stanford-earth-systems-bs": (
        "Earth Systems integrates geology, ecology, and environmental policy in the Stanford "
        "Doerr School of Sustainability's interdisciplinary undergraduate major."
    ),
    "stanford-energy-science-engineering-ms": (
        "Energy Science and Engineering graduate study covers the energy transition, carbon "
        "capture, and grid systems within the Doerr School of Sustainability."
    ),
    "stanford-mba": (
        "The Stanford MBA is a two-year, full-time general-management program emphasizing "
        "entrepreneurship, innovation, and Silicon Valley venture networks."
    ),
    "stanford-msx": (
        "The MSx is a one-year, full-time master's for accomplished mid-career leaders "
        "seeking general-management training at the GSB."
    ),
    "stanford-gsb-phd": (
        "The GSB doctoral program trains future business-school faculty in finance, "
        "organizational behavior, marketing, and operations research."
    ),
    "stanford-education-ms": (
        "Stanford GSE master's programs span learning design, education policy, and teacher "
        "preparation with Silicon Valley school and ed-tech partnerships."
    ),
    "stanford-education-phd": (
        "Doctoral study at the Graduate School of Education covers learning sciences, policy "
        "analysis, and economics of education with the Stanford Accelerator for Learning."
    ),
    "stanford-jd": (
        "Stanford Law School's three-year J.D. emphasizes law, technology, and policy with "
        "clinics in intellectual property, criminal defense, and international law."
    ),
    "stanford-md": (
        "Stanford Medicine's M.D. program pairs clinical training with discovery science "
        "on a flexible-length schedule at Stanford Hospital and Lucile Packard Children's."
    ),
}


def _adapt(text: str) -> str:
    out = text
    for pat, repl in _ADAPT_RE:
        out = re.sub(pat, repl, out)
    return out


def _clause_for(field: str) -> str:
    if field in STANFORD_MANUAL:
        return STANFORD_MANUAL[field]
    for src in (HARVARD, COLUMBIA, BERKELEY, CORNELL, JHU, NORTHWESTERN, PENN):
        if field in src:
            return _adapt(src[field])
    raise KeyError(f"No source clause for {field!r}")


def main() -> None:
    out_path = (
        Path(__file__).resolve().parents[1]
        / "src/unipaith/data/stanford_field_descriptions.py"
    )
    lines = [
        '"""Field-specific program description clauses for Stanford University.',
        "",
        "Each entry states something concrete about what Stanford's program in that field",
        "covers — never a credential/school classification stub. Sources: Stanford Bulletin",
        "(bulletin.stanford.edu), School of Engineering (engineering.stanford.edu), Graduate",
        "School of Business (gsb.stanford.edu), Graduate School of Education (ed.stanford.edu),",
        "Stanford Law School (law.stanford.edu), Stanford Medicine (med.stanford.edu),",
        "Stanford Doerr School of Sustainability (sustainability.stanford.edu), and the",
        "School of Humanities and Sciences (humsci.stanford.edu).",
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
    aliases = {
        "Biology General": "Biology, General",
        "Biochemistry Biophysics and Molecular Biology": "Biochemistry, Biophysics and Molecular Biology",
        "Biomathematics Bioinformatics and Computational Biology": (
            "Biomathematics, Bioinformatics, and Computational Biology"
        ),
        "Clinical Counseling and Applied Psychology": "Clinical, Counseling and Applied Psychology",
        "Computer and Information Sciences General": "Computer and Information Sciences, General",
        "East Asian Languages Literatures and Linguistics": "East Asian Languages, Literatures, and Linguistics",
        "Ecology Evolution Systematics and Population Biology": (
            "Ecology, Evolution, Systematics, and Population Biology"
        ),
        "English Language and Literature General": "English Language and Literature, General",
        "Ethnic Cultural Minority Gender and Group Studies": (
            "Ethnic, Cultural Minority, Gender, and Group Studies"
        ),
        "Germanic Languages Literatures and Linguistics": "Germanic Languages, Literatures, and Linguistics",
        "Liberal Arts and Sciences General Studies and Humanities": (
            "Liberal Arts and Sciences, General Studies and Humanities"
        ),
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
        "Computer Science": "Computer Science",
        "Mechanical Engineering": "Mechanical Engineering",
        "Electrical Engineering": "Electrical, Electronics, and Communications Engineering",
        "Civil and Environmental Engineering": "Civil Engineering",
        "Bioengineering": "Biomedical/Medical Engineering",
        "Management Science and Engineering": "Engineering, Other",
        "Economics": "Economics",
        "Human Biology": "Biology, General",
        "Symbolic Systems": "Cognitive Science",
        "Mathematics": "Mathematics",
        "Political Science": "Political Science and Government",
        "International Relations": "International Relations and National Security Studies",
        "Psychology": "Psychology, General",
        "English": "English Language and Literature, General",
        "Earth Systems": "Natural Resources Conservation and Research",
        "Energy Science and Engineering": "Environmental/Environmental Health Engineering",
        "Education": "Education, General",
        "Aeronautics and Astronautics": "Aerospace, Aeronautical, and Astronautical/Space Engineering",
    }
    for k, v in sorted(aliases.items()):
        lines.append(f'    "{k}": "{v}",')
    lines.append("}")
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(FIELDS)} fields, {len(SLUG_DESCRIPTIONS)} slug overrides)")


if __name__ == "__main__":
    main()
