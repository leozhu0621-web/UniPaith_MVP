#!/usr/bin/env python3
"""Generate ``purdue_field_descriptions.py`` from peer-university clauses + Purdue overrides."""

from __future__ import annotations

# ruff: noqa: E501
import re
from pathlib import Path

from unipaith.data import purdue_profile as p
from unipaith.data.berkeley_field_descriptions import FIELD_DESCRIPTIONS as BERKELEY
from unipaith.data.columbia_field_descriptions import FIELD_DESCRIPTIONS as COLUMBIA
from unipaith.data.cornell_field_descriptions import FIELD_DESCRIPTIONS as CORNELL
from unipaith.data.harvard_field_descriptions import FIELD_DESCRIPTIONS as HARVARD
from unipaith.data.jhu_field_descriptions import FIELD_DESCRIPTIONS as JHU
from unipaith.data.northwestern_field_descriptions import FIELD_DESCRIPTIONS as NORTHWESTERN
from unipaith.data.penn_field_descriptions import FIELD_DESCRIPTIONS as PENN
from unipaith.data.purdue_catalog_maps import SLUG_PROGRAM_NAMES, clean_cip_field


# All lookup keys used by _field_from_spec in purdue_profile.
def _field_from_spec(pr: dict) -> str:
    slug = pr["slug"]
    if slug in SLUG_PROGRAM_NAMES:
        name = SLUG_PROGRAM_NAMES[slug]
        if name in ("Doctor of Pharmacy", "Doctor of Veterinary Medicine"):
            return name
        for prefix in (
            "Bachelor of Science in ",
            "Bachelor of Arts in ",
            "Master of Science in ",
            "Doctor of Philosophy in ",
            "Graduate Certificate in ",
        ):
            if name.startswith(prefix):
                return name[len(prefix) :].strip()
        return name
    fn = pr.get("program_name", "")
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
    ):
        if fn.startswith(prefix):
            return fn[len(prefix) :].strip()
    return clean_cip_field(fn)


FIELDS = sorted(set(_field_from_spec(pr) for pr in p.PROGRAMS))

# Purdue-specific clauses — verified against purdue.edu catalog pages.
PURDUE_MANUAL: dict[str, str] = {
    "Advanced Engineering Technology": (
        "Purdue Polytechnic applied-engineering coursework spans mechatronics, "
        "manufacturing systems, and industry-sponsored capstone projects in the "
        "School of Engineering Technology."
    ),
    "Agricultural Communication": (
        "Students in agricultural communication learn science journalism, extension "
        "messaging, and digital media for Purdue Extension and ag-industry audiences."
    ),
    "Agricultural Economics": (
        "The Department of Agricultural Economics trains analysts in commodity markets, "
        "farm policy, and agribusiness finance — a signature Purdue land-grant strength."
    ),
    "Agricultural Operations": (
        "Production-agriculture coursework covers crop and livestock operations, precision "
        "agriculture, and farm management on Purdue's research farms."
    ),
    "Agricultural Systems Management": (
        "Agricultural systems management integrates machinery, soil conservation, and "
        "technology for modern farm and agribusiness operations."
    ),
    "Agriculture": (
        "Purdue's College of Agriculture — one of the nation's top land-grant colleges — "
        "spans agronomy, animal sciences, food science, and agricultural economics."
    ),
    "Apparel Design": (
        "Apparel design in the Patti and Rusty Rueff School combines textile science, "
        "CAD patternmaking, and retail merchandising with industry internships."
    ),
    "Architectural Engineering Technologies/Technicians": (
        "Purdue Polytechnic architectural engineering technology covers building systems, "
        "HVAC design, and construction documentation in the School of Construction "
        "Management Technology."
    ),
    "Atmospheric Science": (
        "Earth, atmospheric, and planetary sciences coursework examines weather "
        "dynamics, climate modeling, and remote sensing with Purdue's mesonet and "
        "supercomputing resources."
    ),
    "Aviation Management": (
        "Purdue's School of Aviation and Transportation Technology — home of Amelia "
        "Earhart's teaching career — trains pilots, airport managers, and aviation "
        "operations leaders at Purdue University Airport."
    ),
    "Clinical/Medical Laboratory Science/Research and Allied Professions": (
        "Medical laboratory science at Purdue prepares clinical technologists in "
        "hematology, microbiology, and diagnostic testing through hospital-affiliated "
        "clinical rotations."
    ),
    "Communication": (
        "The Brian Lamb School of Communication covers rhetoric, media studies, and "
        "organizational communication — named for C-SPAN founder and Purdue alumnus "
        "Brian Lamb."
    ),
    "Computer Graphics Technology": (
        "Computer graphics technology at Purdue Polytechnic spans 3D animation, "
        "virtual-product development, and UX design for manufacturing and entertainment."
    ),
    "Computer Information Systems": (
        "Information-systems coursework in Purdue Polytechnic covers enterprise databases, "
        "network administration, and business analytics for IT leadership roles."
    ),
    "Construction Engineering": (
        "Purdue's School of Construction Engineering and Management trains builders in "
        "estimating, scheduling, and sustainable infrastructure delivery."
    ),
    "Digital Humanities and Textual Studies": (
        "Digital humanities at Purdue combines computational text analysis, archival "
        "digitization, and data visualization in the College of Science."
    ),
    "Doctor of Pharmacy": (
        "Purdue's Pharm.D. program in one of the oldest U.S. pharmacy colleges emphasizes "
        "clinical practice, drug discovery at the Purdue Institute for Drug Discovery, "
        "and interprofessional training."
    ),
    "Doctor of Veterinary Medicine": (
        "Purdue's D.V.M. program operates a full-service veterinary teaching hospital "
        "and research programs in comparative oncology, food-animal medicine, and "
        "biomedical sciences."
    ),
    "Earth Sciences": (
        "Geology and geophysics coursework in EAPS covers mineral resources, seismology, "
        "and planetary geology with field camps and analytical labs."
    ),
    "Ecology and Evolutionary Biology": (
        "Ecology and evolutionary biology at Purdue examines population dynamics, "
        "conservation genetics, and field ecology across Indiana's forests and wetlands."
    ),
    "Electrical Engineering Technology": (
        "Electrical engineering technology in Purdue Polytechnic covers power systems, "
        "industrial controls, and embedded electronics for manufacturing careers."
    ),
    "Engineering Sciences": (
        "Interdisciplinary engineering sciences coursework lets undergraduates tailor "
        "engineering fundamentals across Purdue's College of Engineering schools."
    ),
    "Engineering-Related Technology": (
        "Engineering-related technology programs in Purdue Polytechnic bridge applied "
        "design, prototyping, and industry-sponsored senior projects."
    ),
    "Family and Consumer Sciences/Human Sciences": (
        "Human development and consumer sciences coursework spans family systems, "
        "financial literacy, and community wellness in the College of Health and "
        "Human Sciences."
    ),
    "Family and Consumer Sciences/Human Sciences Business Services": (
        "Consumer sciences business coursework combines retail analytics, product "
        "development, and merchandising strategy for the apparel and food industries."
    ),
    "Fisheries and Aquatic Sciences": (
        "Fisheries and aquatic sciences at Purdue studies freshwater ecology, aquaculture, "
        "and fisheries management through the Aquaculture Research Laboratory."
    ),
    "Food Science": (
        "Purdue food science — among the nation's largest programs — covers food "
        "chemistry, processing, safety, and sensory evaluation in Whistler Hall labs."
    ),
    "General Sales, Merchandising and Related Marketing Operations": (
        "Sales and merchandising coursework in the Mitch Daniels School of Business "
        "emphasizes retail analytics, category management, and consumer behavior."
    ),
    "Health Services/Allied Health/Health Sciences": (
        "Allied health sciences at Purdue prepares practitioners in clinical support "
        "roles across the College of Health and Human Sciences."
    ),
    "Horticulture": (
        "Horticulture and landscape architecture coursework covers greenhouse production, "
        "urban forestry, and sustainable landscape design on Purdue's horticulture farms."
    ),
    "Human Development and Family Studies": (
        "Human development and family studies examines child development, family policy, "
        "and gerontology with community-based practicum placements."
    ),
    "Human Resource Management": (
        "HR management in the Mitch Daniels School covers talent analytics, labor "
        "relations, and organizational development for Fortune 500 recruiting pipelines."
    ),
    "Information Technology": (
        "Information technology at Purdue Polytechnic trains systems administrators, "
        "cybersecurity analysts, and IT project managers with industry certifications."
    ),
    "Management": (
        "Purdue's Mitch Daniels School of Business (formerly Krannert) emphasizes "
        "analytics-driven management, supply chain leadership, and entrepreneurship "
        "through the Purdue Foundry."
    ),
    "Mechanical Engineering Technology": (
        "Mechanical engineering technology in Purdue Polytechnic covers CAD, "
        "manufacturing processes, and thermal-fluid systems for applied engineering careers."
    ),
    "Military Technologies and Applied Sciences": (
        "Purdue ROTC and defense-research pathways connect engineering students to "
        "aerospace, cybersecurity, and systems programs serving national security needs."
    ),
    "Multi-/Interdisciplinary Studies": (
        "Interdisciplinary studies at Purdue lets undergraduates design cross-college "
        "curricula combining STEM, liberal arts, and professional coursework."
    ),
    "Natural Resources": (
        "Natural resources coursework in forestry and natural resources covers "
        "conservation biology, watershed management, and environmental policy."
    ),
    "Nutrition Science": (
        "Nutrition science at Purdue examines dietetics, metabolic biochemistry, and "
        "community nutrition with ACEND-accredited dietetics pathways."
    ),
    "Pharmaceutical Sciences": (
        "Pharmaceutical sciences research at Purdue spans medicinal chemistry, "
        "pharmacology, and drug delivery at the Purdue Institute for Drug Discovery."
    ),
    "Plant Science": (
        "Plant science at Purdue covers crop genetics, plant pathology, and sustainable "
        "agriculture through the Department of Botany and Plant Pathology."
    ),
    "Psychological Sciences": (
        "Psychological sciences at Purdue spans cognitive, clinical, developmental, and "
        "industrial-organizational psychology with NIH-funded research labs."
    ),
    "Soil Science": (
        "Soil science in the Department of Agronomy examines soil fertility, precision "
        "agriculture, and environmental quality on Indiana's research farms."
    ),
    "Speech, Language, and Hearing Sciences": (
        "Speech, language, and hearing sciences prepares audiologists and speech-language "
        "pathologists with clinical practica in Purdue's Lyles-Purdue Center."
    ),
    "Teacher Education (Levels and Methods)": (
        "Purdue's College of Education teacher-preparation programs lead to Indiana "
        "licensure with classroom placements in Tippecanoe County partner schools."
    ),
    "Teacher Education (Subject Areas)": (
        "Subject-area teacher education at Purdue pairs content majors with pedagogy "
        "coursework and supervised student teaching in STEM and liberal-arts fields."
    ),
    "Veterinary Biomedical Sciences": (
        "Veterinary biomedical sciences research at Purdue covers infectious disease, "
        "comparative oncology, and translational animal health in the vet college."
    ),
    "Veterinary Technology": (
        "Veterinary technology trains credentialed veterinary technicians in clinical "
        "nursing, diagnostic imaging, and laboratory procedures at the vet teaching hospital."
    ),
    "Visual Communication Design": (
        "Visual communication design in the Rueff School covers branding, typography, "
        "and interactive media with studio critiques and industry portfolio reviews."
    ),
}

# Peer clause → Purdue adaptation (regex replacements applied in order).
_ADAPT_RE: list[tuple[str, str]] = [
    (r"\bHarvard Business School\b", "Mitch Daniels School of Business"),
    (r"\bHarvard Law School\b", "Purdue (no law school)"),
    (r"\bHarvard Medical School\b", "Purdue College of Health and Human Sciences"),
    (r"\bHarvard Graduate School of Design\b", "Patti and Rusty Rueff School of Design, Art, and Performance"),
    (r"\bHarvard Graduate School of Education\b", "Purdue College of Education"),
    (r"\bHarvard Kennedy School\b", "Department of Political Science"),
    (r"\bHarvard Faculty of Arts & Sciences\b", "College of Liberal Arts"),
    (r"\bHarvard Faculty of Arts and Sciences\b", "College of Liberal Arts"),
    (r"\bHarvard SEAS\b", "College of Engineering"),
    (r"\bWhiting School of Engineering\b", "College of Engineering"),
    (r"\bWhiting\b", "College of Engineering"),
    (r"\bKrieger School of Arts and Sciences\b", "College of Liberal Arts"),
    (r"\bKrieger\b", "College of Liberal Arts"),
    (r"\bHomewood\b", "West Lafayette campus"),
    (r"\bCarey School of Business\b", "Mitch Daniels School of Business"),
    (r"\bCarey\b", "Mitch Daniels School of Business"),
    (r"\bBloomberg School of Public Health\b", "School of Public Health"),
    (r"\bSchool of Advanced International Studies\b", "College of Liberal Arts"),
    (r"\bPeabody Institute\b", "Patti and Rusty Rueff School"),
    (r"\bColumbia Business School\b", "Mitch Daniels School of Business"),
    (r"\bColumbia Law School\b", "Purdue (no law school)"),
    (r"\bVagelos College of Physicians and Surgeons\b", "College of Health and Human Sciences"),
    (r"\bColumbia Engineering\b", "College of Engineering"),
    (r"\bTeachers College\b", "College of Education"),
    (r"\bMailman School of Public Health\b", "School of Public Health"),
    (r"\bUC Berkeley\b", "Purdue University"),
    (r"\bBerkeley\b", "Purdue"),
    (r"\bCornell\b", "Purdue"),
    (r"\bNorthwestern\b", "Purdue"),
    (r"\bJohns Hopkins\b", "Purdue"),
    (r"\bJHU\b", "Purdue"),
    (r"\bHopkins\b", "Purdue"),
    (r"\bHarvard\b", "Purdue"),
    (r"\bColumbia\b", "Purdue"),
    (r"\bPenn\b", "Purdue"),
    (r"\bCambridge\b", "West Lafayette"),
    (r"\bBoston\b", "West Lafayette"),
    (r"\bBaltimore\b", "West Lafayette"),
    (r"\bNew York City\b", "West Lafayette"),
    (r"\bManhattan\b", "West Lafayette"),
    (r"\bPhiladelphia\b", "West Lafayette"),
    (r"\bIthaca\b", "West Lafayette"),
    (r"\bEast Baltimore\b", "West Lafayette"),
    (r"\bNIH-funded\b", "federally funded"),
    (r"\bNIH\b", "federal research"),
    (r"\bApplied Physics Laboratory\b", "Zucrow Laboratories"),
    (r"\bSpace Telescope Science Institute\b", "NASA partnerships"),
]

# Reverse map: Purdue clean field → peer module key (when names differ).
_PEER_KEY_ALIASES: dict[str, str] = {
    "Biology": "Biology, General",
    "Psychology": "Psychology, General",
    "Chemistry": "Chemistry, General",
    "Physics": "Physics, General",
    "Mathematics": "Mathematics, General",
    "History": "History, General",
    "English": "English Language and Literature, General",
    "Computer and Information Sciences": "Computer and Information Sciences, General",
    "Electrical Engineering": "Electrical, Electronics, and Communications Engineering",
    "Biomedical Engineering": "Biomedical/Medical Engineering",
    "Environmental Engineering": "Environmental/Environmental Health Engineering",
    "Intercultural Studies": "Ethnic, Cultural Minority, Gender, and Group Studies",
    "Liberal Arts": "Liberal Arts and Sciences, General Studies and Humanities",
    "Interdisciplinary Studies": "Multi/Interdisciplinary Studies, Other",
    "Accounting": "Accounting and Related Services",
    "Finance": "Finance and Financial Management Services",
    "Marketing": "Marketing/Marketing Management, General",
    "Management Information Systems": "Management Information Systems and Services",
    "Supply Chain Management": "Supply Chain Management/Logistics",
    "International Business": "International Business/Trade/Commerce",
    "Public Health": "Public Health, General",
    "Allied Health": "Allied Health Diagnostic, Intervention, and Treatment Professions",
    "Health Administration": "Health and Medical Administrative Services",
    "Health Sciences": "Health Professions and Related Clinical Sciences, Other",
    "Kinesiology": "Parks, Recreation, Leisure, Fitness, and Kinesiology",
    "Nutrition Sciences": "Dietetics and Clinical Nutrition Services",
    "Experimental Psychology": "Research and Experimental Psychology",
    "Clinical, Counseling and Applied Psychology": "Clinical, Counseling and Applied Psychology",
    "Political Science": "Political Science and Government",
    "Area Studies": "Area Studies",
    "Linguistics": "Linguistic, Comparative, and Related Language Studies and Services",
    "East Asian Languages": "East Asian Languages, Literatures, and Linguistics",
    "Slavic Languages": "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics",
    "Romance Languages": "Romance Languages, Literatures, and Linguistics",
    "German": "Germanic Languages, Literatures, and Linguistics",
    "Classical and Ancient Studies": "Classics and Classical Languages, Literatures, and Linguistics",
    "Visual Arts": "Fine and Studio Arts",
    "Theatre": "Drama/Theatre Arts and Stagecraft",
    "Film/Video and Photographic Arts": "Film/Cinema/Video and Photographic Arts",
    "Public Relations": "Public Relations, Advertising, and Applied Communication",
    "Journalism": "Journalism",
    "Entrepreneurial and Small Business Operations": "Entrepreneurship/Entrepreneurial Studies",
    "Hospitality Administration/Management": "Hospitality Administration/Management, General",
    "Industrial Production Technologies/Technicians": "Industrial Production Technologies/Technicians",
    "Engineering Technology": "Engineering Technologies/Technicians, General",
    "General Engineering": "Engineering, General",
    "Agricultural Engineering": "Agricultural Engineering",
    "Biochemistry, Biophysics and Molecular Biology": "Biochemistry, Biophysics and Molecular Biology",
    "Cell Biology": "Cell/Cellular Biology and Anatomical Sciences",
    "Microbiology": "Microbiological Sciences and Immunology",
    "Genetics": "Genetics, General",
    "Neurobiology and Neurosciences": "Neurobiology and Neurosciences",
    "Physiology, Pathology and Related Sciences": "Physiology, Pathology and Related Sciences",
    "Pharmacology and Toxicology": "Pharmacology and Toxicology",
    "Zoology/Animal Biology": "Zoology/Animal Biology",
    "Plant Biology": "Botany/Plant Biology",
    "Applied Mathematics": "Applied Mathematics",
    "Statistics": "Statistics, General",
    "Data Analytics": "Data Analytics, General",
    "Computer Science": "Computer Science",
    "Aerospace Engineering": "Aerospace, Aeronautical, and Astronautical/Space Engineering",
    "Mechanical Engineering": "Mechanical Engineering",
    "Chemical Engineering": "Chemical Engineering",
    "Civil Engineering": "Civil Engineering",
    "Industrial Engineering": "Industrial Engineering",
    "Materials Engineering": "Materials Engineering",
    "Nuclear Engineering": "Nuclear Engineering",
    "Computer Engineering": "Computer Engineering",
    "Information Science": "Information Science/Studies",
    "Biological Sciences": "Biological and Biomedical Sciences, Other",
    "Biotechnology": "Biotechnology",
    "Economics": "Economics",
    "Anthropology": "Anthropology",
    "Sociology": "Sociology",
    "Philosophy": "Philosophy",
    "Religious Studies": "Religion/Religious Studies",
    "Music": "Music",
    "Forestry": "Forestry",
    "Landscape Architecture": "Landscape Architecture",
    "Animal Sciences": "Animal Sciences",
    "Special Education": "Special Education and Teaching",
    "Educational Leadership": "Educational Administration and Supervision",
    "Curriculum and Instruction": "Curriculum and Instruction",
    "Education Studies": "Education, General",
    "Education": "Education, Other",
    "Educational Assessment, Evaluation, and Research": "Educational Assessment, Evaluation, and Research",
    "Educational/Instructional Media Design": "Educational/Instructional Media Design",
    "Bilingual, Multilingual, and Multicultural Education": "Bilingual, Multilingual, and Multicultural Education",
    "Nanotechnology": "Nanotechnology",
    "Systems Science and Theory": "Systems Science and Theory",
    "Science, Technology and Society": "Science, Technology and Society",
    "Cultural Studies/Critical Theory and Analysis": "Cultural Studies/Critical Theory and Analysis",
    "Intercultural/Multicultural and Diversity Studies": "Intercultural/Multicultural and Diversity Studies",
    "Geography and Cartography": "Geography and Cartography",
    "Social Sciences": "Social Sciences, General",
    "Rhetoric and Composition/Writing Studies": "Rhetoric and Composition/Writing Studies",
    "Business/Corporate Communications": "Business/Corporate Communications",
    "Management Sciences and Quantitative Methods": "Management Sciences and Quantitative Methods",
    "Mental and Social Health Services and Allied Professions": "Mental and Social Health Services and Allied Professions",
    "Sports, Kinesiology, and Physical Education/Fitness": "Parks, Recreation, Leisure, Fitness, and Kinesiology",
    "Integrated Science": "Biological and Physical Sciences",
    "Mathematics and Computer Science": "Mathematics and Computer Science",
    "Gerontology": "Gerontology",
    "Veterinary Medicine": "Veterinary Medicine",
}

SLUG_DESCRIPTIONS: dict[str, str] = {
    "purdue-computer-science-bs": (
        "Purdue's Department of Computer Science — consistently top-ranked nationally — "
        "covers algorithms, systems, AI, and security with ties to the Birck Nanotechnology "
        "Center and industry recruiting from Amazon, Google, and Microsoft."
    ),
    "purdue-aerospace-engineering-bs": (
        "Purdue's School of Aeronautics and Astronautics — the 'Cradle of Astronauts' — "
        "trains propulsion, structures, and flight-dynamics engineers with Zucrow "
        "Laboratories and NASA research partnerships."
    ),
    "purdue-mechanical-engineering-bs": (
        "Mechanical engineering at Purdue spans thermofluids, design, robotics, and "
        "manufacturing with Herrick Laboratories and industry-sponsored senior design."
    ),
    "purdue-electrical-engineering-bs": (
        "The Elmore Family School of Electrical and Computer Engineering covers power "
        "systems, semiconductors, signal processing, and embedded systems — a Purdue "
        "signature feeding the semiconductor workforce."
    ),
    "purdue-nursing-bs": (
        "Purdue's School of Nursing BSN program combines clinical rotations, simulation "
        "labs, and community health practica with Indiana hospital partners."
    ),
    "purdue-pharmacy-prof": (
        "Purdue's Pharm.D. in one of the oldest U.S. pharmacy colleges emphasizes "
        "clinical practice, drug discovery, and interprofessional training at the "
        "Purdue Institute for Drug Discovery."
    ),
    "purdue-veterinary-medicine-prof": (
        "Purdue's D.V.M. program operates a full-service veterinary teaching hospital "
        "with research in comparative oncology, food-animal medicine, and biomedical sciences."
    ),
    "purdue-business-administration-bs": (
        "The Mitch Daniels School of Business B.S. in Management emphasizes analytics, "
        "supply chain, and entrepreneurship through the Purdue Foundry and Krannert "
        "legacy recruiting networks."
    ),
    "purdue-agricultural-economics-bs": (
        "Agricultural economics at Purdue — a land-grant flagship — covers commodity "
        "markets, farm policy, and agribusiness finance with Extension outreach."
    ),
    "purdue-psychology-bs": (
        "Psychological sciences at Purdue spans cognitive, clinical, developmental, and "
        "industrial-organizational psychology with federally funded research labs."
    ),
}


def _adapt(text: str) -> str:
    out = text
    for pat, repl in _ADAPT_RE:
        out = re.sub(pat, repl, out)
    return out


def _clause_for(field: str) -> str:
    if field in PURDUE_MANUAL:
        return PURDUE_MANUAL[field]
    peer_key = _PEER_KEY_ALIASES.get(field, field)
    for src in (JHU, PENN, NORTHWESTERN, CORNELL, BERKELEY, COLUMBIA, HARVARD):
        if peer_key in src:
            return _adapt(src[peer_key])
        if field in src:
            return _adapt(src[field])
    raise KeyError(f"No source clause for {field!r} (peer_key={peer_key!r})")


def main() -> None:
    out_path = (
        Path(__file__).resolve().parents[1]
        / "src/unipaith/data/purdue_field_descriptions.py"
    )
    lines = [
        '"""Field-specific program description clauses for Purdue University.',
        "",
        "Each entry states something concrete about what Purdue's program in that field",
        "covers — never a credential/school classification stub. Sources: Purdue Academics",
        "(purdue.edu/academics/), college and department catalog pages, Purdue Polytechnic",
        "Institute (polytechnic.purdue.edu), Mitch Daniels School of Business",
        "(business.purdue.edu), College of Agriculture (ag.purdue.edu), College of",
        "Engineering (engineering.purdue.edu), College of Science (science.purdue.edu),",
        "College of Pharmacy (pharmacy.purdue.edu), and College of Veterinary Medicine",
        "(vet.purdue.edu).",
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
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(FIELDS)} fields, {len(SLUG_DESCRIPTIONS)} slug overrides)")


if __name__ == "__main__":
    main()
