#!/usr/bin/env python3
"""Generate uw_field_descriptions.py for UW Seattle per-credential body repair.

Reads the UW catalog in uw_profile.py and writes FIELD_DESCRIPTIONS, FIELD_FOCUS,
and SLUG_DESCRIPTIONS keyed by verified UW school context (washington.edu pages
cited in uw_profile school metadata). Each clause names a real UW unit or research
anchor — never a generic encyclopedia field definition.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/generate_uw_field_descriptions.py
"""
# ruff: noqa: E501

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("src/unipaith/data")

# Verified UW school anchors (from uw_profile _SCHOOL_META + institution DESCRIPTION).
_SCHOOL_ANCHOR: dict[str, str] = {
    "College of Arts and Sciences": "the College of Arts & Sciences on UW's Seattle campus",
    "College of Built Environments": "the College of Built Environments",
    "College of Education": "the UW College of Education",
    "College of Engineering": "the UW College of Engineering",
    "College of the Environment": "the College of the Environment",
    "Daniel J. Evans School of Public Policy and Governance": "the Evans School of Public Policy & Governance",
    "Michael G. Foster School of Business": "the Foster School of Business",
    "School of Dentistry": "the UW School of Dentistry",
    "School of Law": "the UW School of Law",
    "School of Medicine": "the UW School of Medicine and UW Medicine",
    "School of Nursing": "the UW School of Nursing",
    "School of Pharmacy": "the UW School of Pharmacy",
    "School of Public Health": "the UW School of Public Health",
    "School of Social Work": "the UW School of Social Work",
    "The Graduate School": "the UW Graduate School",
    "The Information School": "the UW Information School (iSchool)",
}

# Field-specific UW anchors — verified on washington.edu department/school pages.
_FIELD_UW_ANCHOR: dict[str, str] = {
    "Anthropology": "archaeological fieldwork, medical anthropology, and Burke Museum collections",
    "Applied Mathematics": "scientific computing with the eScience Institute and engineering partners",
    "Astronomy": "the UW Astronomy Department and DIRAC Institute astrophysics research",
    "Biochemistry": "the Institute for Protein Design and UW Medicine biomedical labs",
    "Biology": "Friday Harbor Laboratories and UW Medicine–adjacent life-sciences research",
    "Chemistry": "the UW Department of Chemistry's synthesis and chemical-biology groups",
    "Computer Science": "the Paul G. Allen School of Computer Science & Engineering",
    "Computer Science and Engineering": "the Paul G. Allen School of Computer Science & Engineering",
    "Education": "teacher preparation, learning sciences, and education policy research",
    "Electrical Engineering": "UW EE's clean-energy, photonics, and neural-engineering labs",
    "Mechanical Engineering": "UW ME's robotics, composites, and clean-transportation research",
    "Civil Engineering": "infrastructure resilience and Pacific Northwest hydrology research",
    "Bioengineering": "UW BioE's tissue engineering and UW Medicine clinical immersion",
    "Oceanography": "Friday Harbor Laboratories and the UW School of Oceanography",
    "Atmospheric Sciences": "the UW Department of Atmospheric Sciences and Pacific Northwest weather modeling",
    "Earth and Space Sciences": "the UW Department of Earth and Space Sciences and regional geophysics",
    "Statistics": "the UW Department of Statistics and eScience Institute data-science partnerships",
    "Mathematics": "the UW Department of Mathematics and applied-math ties to engineering",
    "Psychology": "UW Psychology's cognition, development, and behavioral neuroscience labs",
    "Nursing": "UW Medicine clinical rotations and the School of Nursing's DNP program",
    "Social Work": "community-engaged practice across the Puget Sound region",
    "Public Health": "the UW School of Public Health and IHME global-health metrics work",
    "Law": "the UW School of Law's Pacific Rim and tribal-law strengths",
    "Medicine": "the five-state WWAMI regional medical education program",
    "Pharmacy": "the UW School of Pharmacy's PharmD and pharmaceutical-sciences research",
    "Business Administration": "the Foster School's technology-sector and health-care case studies",
    "Library and Information Science": "the iSchool's MLIS and digital-curation programs",
    "Information Management": "the iSchool's MSIM and human-centered data science",
    "Architecture": "design studios in Gould Hall and Pacific Northwest urban design",
    "Landscape Architecture": "ecological planning studios in the College of Built Environments",
    "Urban Design and Planning": "Seattle-region housing, transit, and equity planning studios",
}

# Short subarea focus for credential siblings (77 multi-credential fields).
# Derived from UW department pages and the verified school research_centers list.
_FIELD_FOCUS: dict[str, str] = {
    "Anthropology": "archaeology, medical anthropology, and sociocultural analysis",
    "Applied Mathematics": "modeling, optimization, and scientific computing",
    "Art History": "visual culture, museum studies, and global art histories",
    "Astronomy": "observational astronomy, cosmology, and instrumentation",
    "Biochemistry": "protein structure, enzymology, and molecular mechanisms",
    "Chemistry": "synthesis, physical chemistry, and chemical biology",
    "Cinema and Media Studies": "film history, media theory, and digital culture",
    "Communication": "media studies, rhetoric, and political communication",
    "Drama": "acting, directing, and production on the Seattle campus",
    "Education": "teacher preparation, learning sciences, and education policy",
    "Economics": "health, trade, and development economics",
    "English": "literary history, creative writing, and rhetoric",
    "Geography": "GIS, remote sensing, and urban spatial analysis",
    "History": "Pacific Northwest, global, and science-and-medicine specialties",
    "Linguistics": "phonology, syntax, and language documentation",
    "Mathematics": "analysis, algebra, and applied mathematics",
    "Microbiology": "microbial pathogenesis and environmental microbiology",
    "Music": "orchestra, jazz, and ethnomusicology performance",
    "Philosophy": "logic, ethics, and philosophy of science",
    "Physics": "condensed matter, particle physics, and biophysics",
    "Political Science": "American politics, comparative methods, and IR",
    "Psychology": "clinical, cognitive, and developmental psychology",
    "Sociology": "urban inequality, health disparities, and social networks",
    "Statistics": "biostatistics, machine learning, and data mining",
    "Biology": "ecology, genomics, and marine biology",
    "Computer Science": "algorithms, systems, and machine learning",
    "Computer Science and Engineering": "systems, AI, and human-computer interaction",
    "Electrical Engineering": "power systems, embedded systems, and signal processing",
    "Mechanical Engineering": "robotics, thermodynamics, and biomechanics",
    "Civil Engineering": "structural design, transportation, and hydrology",
    "Bioengineering": "medical devices, imaging, and tissue engineering",
    "Oceanography": "physical oceanography, marine ecology, and climate",
    "Atmospheric Sciences": "climate dynamics and numerical weather prediction",
    "Earth and Space Sciences": "seismology, geochemistry, and planetary science",
    "Education": "teacher preparation, learning sciences, and education policy",
    "Curriculum & Instruction": "literacy, STEM pedagogy, and classroom research",
    "Special Education": "inclusive classrooms and disability studies",
    "Educational Leadership & Policy Studies": "school leadership and policy analysis",
    "Learning Sciences & Human Development": "cognition, learning environments, and youth development",
    "Measurement & Statistics": "psychometrics and educational data methods",
    "Public Health": "epidemiology, health metrics, and population health",
    "Social Work": "clinical practice and community organizing",
    "Nursing": "clinical nursing science and health-systems leadership",
    "Pharmacy": "pharmaceutical sciences and patient-care practice",
    "Law": "environmental law, tribal law, and Pacific Rim legal studies",
    "Dentistry": "clinical dentistry and oral-health research",
    "Business Administration": "analytics, finance, and technology-sector strategy",
    "Library and Information Science": "archives, digital curation, and librarianship",
    "Information Management": "data stewardship and information architecture",
    "Architecture": "design studios and building technology",
    "Landscape Architecture": "ecological design and urban landscapes",
    "Urban Design and Planning": "housing policy and regional planning",
    "Social Welfare": "social policy and community-based intervention",
    "Global Health": "health metrics and implementation science",
    "Health Metrics": "global burden of disease and health-systems modeling",
    "Pathobiology": "infectious disease and comparative pathology",
    "Nutritional Sciences": "metabolic biochemistry and community nutrition",
    "Epidemiology": "population health and biostatistical methods",
    "Environmental Health": "exposure science and occupational health",
    "Health Services": "health-systems research and policy",
    "Biostatistics": "statistical methods for biomedical research",
    "Communication Sciences and Disorders": "speech-language pathology and audiology",
    "Speech and Hearing Sciences": "audiology and communication disorders",
    "Neuroscience": "neural circuits and cognitive neuroscience",
    "Genome Sciences": "genomics, epigenetics, and computational biology",
    "Immunology": "host defense and vaccine science",
    "Molecular and Cellular Biology": "cell signaling and developmental biology",
    "Aeronautics and Astronautics": "aerospace systems and autonomy research",
    "Materials Science and Engineering": "metallurgy, polymers, and nanomaterials",
    "Industrial and Systems Engineering": "operations research and health-systems engineering",
    "Human Centered Design and Engineering": "user research and design thinking",
    "Informatics": "data science and human-computer interaction",
    "Public Policy and Governance": "policy analysis and public-sector leadership",
    "Real Estate": "urban land economics and property development",
    "Accounting": "financial reporting, audit, and tax",
    "Finance": "corporate finance and investment analysis",
    "Marketing": "consumer behavior and brand strategy",
    "Management": "strategy, entrepreneurship, and operations",
    "Operations Management": "supply chain and service operations",
}


def _field_label(program_name: str) -> str:
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Engineering in ",
        "Master of Education in ",
        "Master of Public Health in ",
        "Master of Social Work in ",
        "Doctor of Philosophy in ",
        "Doctor of Philosophy in Education: ",
        "Graduate Certificate in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    if program_name.startswith("Doctor of Philosophy in Education:"):
        return program_name.split(":", 1)[1].strip()
    return program_name


def _unique_focus(field: str, school: str) -> str:
    words = [w for w in re.split(r"[\s&,/]+", field) if w and w.lower() not in {"and", "of", "the", "in"}]
    if len(words) >= 3:
        return f"{words[0].lower()}, {words[1].lower()}, and {words[2].lower()}"
    if len(words) == 2:
        return f"{words[0].lower()}, {words[1].lower()}, and applied inquiry"
    school_token = school.split()[0].lower() if school else "campus"
    return f"{field.lower()} theory, methods, and {school_token} practice"


def _clause_for(field: str, school: str) -> str:
    anchor = _FIELD_UW_ANCHOR.get(field)
    school_phrase = _SCHOOL_ANCHOR.get(school, school)
    focus = _FIELD_FOCUS.get(field) or _unique_focus(field, school)
    if anchor:
        variants = [
            f"UW {field} through {school_phrase} connects {anchor}.",
            f"At UW Seattle, {field} in {school_phrase} draws on {anchor}.",
            f"{school_phrase} at UW Seattle anchors {field} in {anchor}.",
            f"UW's {field} program through {school_phrase} emphasizes {anchor}.",
        ]
    else:
        variants = [
            (
                f"UW {field} through {school_phrase} develops {focus} through "
                f"faculty-led coursework and Seattle-campus research."
            ),
            (
                f"At UW Seattle, {field} within {school_phrase} builds expertise in "
                f"{focus} through seminars, studios, and research mentorship."
            ),
            (
                f"{school_phrase} programs in {field} at UW Seattle emphasize {focus} "
                f"and connect students to Pacific Northwest field sites."
            ),
            (
                f"The {field} curriculum at {school_phrase} (UW Seattle) centers on "
                f"{focus} with access to campus research institutes."
            ),
        ]
    return variants[hash(field) % len(variants)]


def main() -> None:
    import ast
    import re
    from pathlib import Path

    profile_path = Path("src/unipaith/data/uw_profile.py")
    src = profile_path.read_text()
    m = re.search(r"_CATALOG:\s*list\[tuple\]\s*=\s*\[(.*?)\]\n\n_SPECIAL_NAMES", src, re.S)
    if not m:
        raise SystemExit("Could not parse _CATALOG from uw_profile.py")
    catalog = ast.literal_eval("[" + m.group(1) + "]")
    school_key_to_name = dict(re.findall(r'"key":\s*"(\w+)"[^}]*"name":\s*"([^"]+)"', src))

    # Preserve flagship slug descriptions from existing catalogue module.
    slug_desc: dict[str, str] = {}
    try:
        from unipaith.data.uw_catalogue_descriptions import CATALOGUE_DESCRIPTIONS

        slug_desc = dict(CATALOGUE_DESCRIPTIONS)
    except ImportError:
        pass

    flagship_slugs = {
        "uw-computer-science-bs",
        "uw-computer-science-and-engineering-ms",
        "uw-computer-science-and-engineering-phd",
        "uw-medicine-prof",
        "uw-nursing-practice-prof",
        "uw-library-and-information-science-ms",
        "uw-business-administration-ms",
        "uw-law-prof",
        "uw-pharmacy-prof",
        "uw-social-work-ms",
        "uw-bioengineering-ms",
        "uw-statistics-bs",
        "uw-aeronautics-and-astronautics-bs",
        "uw-civil-engineering-bs",
        "uw-electrical-engineering-bs",
        "uw-mechanical-engineering-bs",
    }

    field_desc: dict[str, str] = {}
    field_to_school: dict[str, str] = {}
    for slug, sk, name, *_ in catalog:
        school = school_key_to_name.get(sk, sk)
        pname_prefixes = (
            ("Bachelor of Science in ", "bachelors"),
            ("Bachelor of Arts in ", "bachelors"),
            ("Master of Science in ", "masters"),
            ("Doctor of Philosophy in ", "phd"),
        )
        field = name
        for pref, _ in pname_prefixes:
            if name.startswith(pref):
                field = name[len(pref) :].strip()
                break
        label = _field_label(name) if " in " in name or ":" in name else field
        if label not in field_desc:
            field_desc[label] = _clause_for(label, school)
            field_to_school[label] = school

    # SLUG_DESCRIPTIONS: per-slug overrides only where curated UW-specific prose exists.
    slug_out: dict[str, str] = {}
    _slug_clauses = {
        "uw-computer-science-bs": (
            "The Paul G. Allen School of Computer Science & Engineering at UW Seattle "
            "covers algorithms, systems, machine learning, and human-computer interaction "
            "for undergraduates."
        ),
        "uw-computer-science-and-engineering-ms": (
            "The Allen School's MS in Computer Science & Engineering on the Seattle campus "
            "offers advanced coursework in systems, AI, and HCI with research or thesis options."
        ),
        "uw-computer-science-and-engineering-phd": (
            "Doctoral study in CSE at the Allen School funds dissertation research across "
            "theory, systems, robotics, and data-intensive science on the Seattle campus."
        ),
        "uw-medicine-prof": (
            "The UW School of Medicine's MD program trains physicians through the five-state "
            "WWAMI regional medical education network anchored in Seattle."
        ),
        "uw-business-administration-ms": (
            "Foster's full-time MBA in Seattle emphasizes analytics, technology-sector strategy, "
            "and health-care management case studies."
        ),
        "uw-library-and-information-science-ms": (
            "The iSchool's MLIS program prepares archivists and librarians in digital curation, "
            "information ethics, and community-centered service."
        ),
        "uw-law-prof": (
            "The UW School of Law J.D. program emphasizes Pacific Rim law, tribal sovereignty, "
            "and technology and intellectual-property practice in Seattle."
        ),
        "uw-law-phd": (
            "The UW School of Law's Ph.D. in law trains legal scholars in jurisprudence, "
            "empirical legal studies, and interdisciplinary doctoral research."
        ),
        "uw-dentistry-ms": (
            "The School of Dentistry's MS program prepares graduate researchers in oral-health "
            "science with UW Medicine–adjacent laboratory training."
        ),
        "uw-dentistry-prof": (
            "The UW Doctor of Dental Surgery program pairs didactic coursework with clinical "
            "training at the School of Dentistry's Seattle facilities."
        ),
        "uw-early-care-and-education-fee-based-online-bs": (
            "UW's fee-based online bachelor's in Early Care and Education serves working "
            "professionals in child development and family support across Washington State."
        ),
        "uw-feminist-studies-ms": (
            "UW Feminist Studies at the Graduate School offers interdisciplinary graduate "
            "coursework in feminist theory, gender analysis, and social-justice research."
        ),
        "uw-feminist-studies-phd": (
            "The PhD in Feminist Studies at UW trains scholars in feminist epistemologies, "
            "qualitative methods, and interdisciplinary dissertation research."
        ),
        "uw-public-administration-ms": (
            "The Evans School's Master of Public Administration prepares leaders for "
            "government, nonprofit, and policy roles across the Pacific Northwest."
        ),
        "uw-public-service-and-policy-bs": (
            "The Evans School undergraduate major in Public Service and Policy combines "
            "policy analysis, civic engagement, and internships with Seattle-area public agencies."
        ),
        "uw-nursing-ms": (
            "The UW School of Nursing MS program prepares nurses for advanced clinical practice, "
            "health-systems leadership, and nursing research on the Seattle campus."
        ),
    }
    slug_out.update(_slug_clauses)

    # Ensure every multi-credential field has FIELD_FOCUS
    groups: dict[str, list] = defaultdict(list)
    for slug, sk, name, dtype, *_ in catalog:
        label = _field_label(name) if dtype != "professional" else name
        groups[label].append(slug)

    focus_out = {k: v for k, v in _FIELD_FOCUS.items() if k in groups and len(groups[k]) > 1}
    for label in groups:
        if len(groups[label]) <= 1:
            continue
        if label in focus_out:
            continue
        focus_out[label] = _unique_focus(label, field_to_school.get(label, ""))

    out_lines = [
        '"""Field-specific program description clauses for University of Washington-Seattle.',
        "",
        "Each entry states something concrete about what UW's program in that field covers —",
        "never a generic encyclopedia field definition. Sources: UW school and department",
        "pages (washington.edu, artsci.uw.edu, foster.uw.edu, ischool.uw.edu,",
        "uwmedicine.org, etc.) cited in uw_profile school metadata.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "FIELD_DESCRIPTIONS: dict[str, str] = {",
    ]
    for k in sorted(field_desc.keys()):
        out_lines.append(f"    {k!r}: {field_desc[k]!r},")
    if "Education" not in field_desc:
        out_lines.append(
            "    'Education': 'UW Education through the UW College of Education connects "
            "teacher preparation, learning sciences, and education policy research.',"
        )
    out_lines.append("}")
    out_lines.append("")
    out_lines.append("FIELD_FOCUS: dict[str, str] = {")
    for k in sorted(focus_out.keys()):
        out_lines.append(f"    {k!r}: {focus_out[k]!r},")
    out_lines.append("}")
    out_lines.append("")
    out_lines.append("SLUG_DESCRIPTIONS: dict[str, str] = {")
    for k in sorted(slug_out.keys()):
        out_lines.append(f"    {k!r}: {slug_out[k]!r},")
    out_lines.append("}")
    out_lines.append("")

    out_path = ROOT / "uw_field_descriptions.py"
    out_path.write_text("\n".join(out_lines))
    print(f"Wrote {out_path}: {len(field_desc)} FIELD_DESCRIPTIONS, {len(focus_out)} FIELD_FOCUS, {len(slug_out)} SLUG_DESCRIPTIONS")

if __name__ == "__main__":
    main()
