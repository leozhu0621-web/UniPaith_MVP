"""Purdue catalog field aliases and department mappings for structural repair.

Maps federal CIP taxonomy titles to Purdue's published field and department names.
Sources: Purdue Academics degree index, college/school websites, IPEDS UNITID 243780.
"""

# ruff: noqa: E501

from __future__ import annotations

import re

# Verbatim CIP rollup titles → Purdue's published field-of-study name.
FIELD_ALIASES: dict[str, str] = {
    "Agriculture, General": "Agriculture",
    "Biology, General": "Biology",
    "Psychology, General": "Psychology",
    "Chemistry, General": "Chemistry",
    "Physics, General": "Physics",
    "Mathematics, General": "Mathematics",
    "History, General": "History",
    "English Language and Literature, General": "English",
    "Computer and Information Sciences, General": "Computer and Information Sciences",
    "Electrical, Electronics, and Communications Engineering": "Electrical Engineering",
    "Aerospace, Aeronautical, and Astronautical/Space Engineering": "Aerospace Engineering",
    "Biomedical/Medical Engineering": "Biomedical Engineering",
    "Business Administration and Management": "Management",
    "Business Administration, Management and Operations": "Management",
    "Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing": "Nursing",
    "Registered Nursing/Registered Nurse": "Nursing",
    "Mechanical Engineering Related Technologies/Technicians": "Mechanical Engineering Technology",
    "Engineering Technologies/Technicians, General": "Engineering Technology",
    "Engineering-Related Fields": "Engineering-Related Technology",
    "Engineering/Engineering-Related Technologies/Technicians, Other": "Advanced Engineering Technology",
    "Electrical/Electronic Engineering Technologies/Technicians": "Electrical Engineering Technology",
    "Computer/Information Technology Administration and Management": "Information Technology",
    "Computer Software and Media Applications": "Computer Graphics Technology",
    "Information Science/Studies": "Information Science",
    "Natural Resources Conservation and Research": "Natural Resources",
    "Ethnic, Cultural Minority, Gender, and Group Studies": "Intercultural Studies",
    "Communication and Media Studies": "Communication",
    "Political Science and Government": "Political Science",
    "Research and Experimental Psychology": "Experimental Psychology",
    "Teacher Education and Professional Development, Specific Levels and Methods": "Teacher Education (Levels and Methods)",
    "Teacher Education and Professional Development, Specific Subject Areas": "Teacher Education (Subject Areas)",
    "Educational Administration and Supervision": "Educational Leadership",
    "Special Education and Teaching": "Special Education",
    "Curriculum and Instruction": "Curriculum and Instruction",
    "Education, General": "Education Studies",
    "Education, Other": "Education",
    "Engineering, General": "General Engineering",
    "Engineering, Other": "Engineering Sciences",
    "Biological and Biomedical Sciences, Other": "Biological Sciences",
    "Health Professions and Related Clinical Sciences, Other": "Health Sciences",
    "Multi/Interdisciplinary Studies, Other": "Interdisciplinary Studies",
    "Liberal Arts and Sciences, General Studies and Humanities": "Liberal Arts",
    "Area Studies": "Area Studies",
    "Fine and Studio Arts": "Visual Arts",
    "Drama/Theatre Arts and Stagecraft": "Theatre",
    "Music": "Music",
    "Journalism": "Journalism",
    "Public Relations, Advertising, and Applied Communication": "Public Relations",
    "Radio, Television, and Digital Communication": "Film and Video",
    "Accounting and Related Services": "Accounting",
    "Finance and Financial Management Services": "Finance",
    "Marketing/Marketing Management, General": "Marketing",
    "Management Information Systems and Services": "Management Information Systems",
    "Human Resources Management and Services": "Human Resource Management",
    "International Business/Trade/Commerce": "International Business",
    "Supply Chain Management/Logistics": "Supply Chain Management",
    "Atmospheric Sciences and Meteorology": "Atmospheric Science",
    "Geological and Earth Sciences/Geosciences": "Earth Sciences",
    "Ecology, Evolution, Systematics, and Population Biology": "Ecology and Evolutionary Biology",
    "Cell/Cellular Biology and Anatomical Sciences": "Cell Biology",
    "Microbiological Sciences and Immunology": "Microbiology",
    "Pharmacy, Pharmaceutical Sciences, and Administration": "Pharmaceutical Sciences",
    "Public Health, General": "Public Health",
    "Health and Medical Administrative Services": "Health Administration",
    "Allied Health Diagnostic, Intervention, and Treatment Professions": "Allied Health",
    "Communication Disorders Sciences and Services": "Speech, Language, and Hearing Sciences",
    "Dietetics and Clinical Nutrition Services": "Nutrition Science",
    "Human Development, Family Studies, and Related Services": "Human Development and Family Studies",
    "Parks, Recreation, Leisure, Fitness, and Kinesiology": "Kinesiology",
    "Veterinary Biomedical and Clinical Sciences": "Veterinary Biomedical Sciences",
    "Veterinary/Animal Health Technologies/Technicians": "Veterinary Technology",
    "Veterinary Medicine": "Veterinary Medicine",
    "Applied Horticulture and Horticultural Business Services": "Horticulture",
    "Agricultural Production Operations": "Agricultural Operations",
    "Agricultural Public Services": "Agricultural Communication",
    "Agricultural Mechanization": "Agricultural Systems Management",
    "Food Science and Technology": "Food Science",
    "Plant Sciences": "Plant Science",
    "Soil Sciences": "Soil Science",
    "Animal Sciences": "Animal Sciences",
    "Forestry": "Forestry",
    "Fishing and Fisheries Sciences and Management": "Fisheries and Aquatic Sciences",
    "Landscape Architecture": "Landscape Architecture",
    "Architecture": "Architecture",
    "Interior Architecture": "Interior Design",
    "Design and Applied Arts": "Visual Communication Design",
    "Air Transportation": "Aviation Management",
    "Linguistic, Comparative, and Related Language Studies and Services": "Linguistics",
    "East Asian Languages, Literatures, and Linguistics": "East Asian Languages",
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": "Slavic Languages",
    "Romance Languages, Literatures, and Linguistics": "Romance Languages",
    "Germanic Languages, Literatures, and Linguistics": "German",
    "Classics and Classical Languages, Literatures, and Linguistics": "Classics",
    "Anthropology": "Anthropology",
    "Sociology": "Sociology",
    "Economics": "Economics",
    "Philosophy": "Philosophy",
    "Religion/Religious Studies": "Religious Studies",
    "Criminal Justice and Corrections": "Criminal Justice",
    "Public Administration": "Public Administration",
    "Public Policy Analysis": "Public Policy",
    "Social Work": "Social Work",
    "Computer Systems Analysis": "Computer Information Systems",
    "Computer Science": "Computer Science",
    "Biotechnology": "Biotechnology",
    "Botany/Plant Biology": "Plant Biology",
    "Biological and Physical Sciences": "Integrated Science",
    "Apparel and Textiles": "Apparel Design",
    "Nanotechnology": "Nanotechnology",
    "Construction Engineering": "Construction Engineering",
    "Industrial Engineering": "Industrial Engineering",
    "Materials Engineering": "Materials Engineering",
    "Mechanical Engineering": "Mechanical Engineering",
    "Nuclear Engineering": "Nuclear Engineering",
    "Chemical Engineering": "Chemical Engineering",
    "Civil Engineering": "Civil Engineering",
    "Environmental/Environmental Health Engineering": "Environmental Engineering",
    "Agricultural Engineering": "Agricultural Engineering",
    "Agricultural Business and Management": "Agricultural Economics",
    "Agricultural Economics": "Agricultural Economics",
    # Slash / comma-and CIP rollups → Purdue's real published program name
    # (verified against admissions.purdue.edu and the Purdue catalog, 2026-06-19).
    "Hospitality Administration/Management": "Hospitality and Tourism Management",
    "Industrial Production Technologies/Technicians": "Industrial Engineering Technology",
    "Sports, Kinesiology, and Physical Education/Fitness": "Kinesiology",
}

# Field name (after alias) → Purdue's published owning unit.
DEPARTMENT_BY_FIELD: dict[str, str] = {
    "Aerospace Engineering": "School of Aeronautics and Astronautics",
    "Agricultural Engineering": "Agricultural and Biological Engineering",
    "Biomedical Engineering": "Weldon School of Biomedical Engineering",
    "Chemical Engineering": "Davidson School of Chemical Engineering",
    "Civil Engineering": "Lyles School of Civil Engineering",
    "Computer Engineering": "Elmore Family School of Electrical and Computer Engineering",
    "Electrical Engineering": "Elmore Family School of Electrical and Computer Engineering",
    "Environmental Engineering": "Environmental and Ecological Engineering",
    "Industrial Engineering": "School of Industrial Engineering",
    "Materials Engineering": "School of Materials Engineering",
    "Mechanical Engineering": "School of Mechanical Engineering",
    "Nuclear Engineering": "School of Nuclear Engineering",
    "Construction Engineering": "School of Construction Engineering and Management",
    "Computer Science": "Department of Computer Science",
    "Applied Mathematics": "Department of Mathematics",
    "Mathematics": "Department of Mathematics",
    "Statistics": "Department of Statistics",
    "Biology": "Department of Biological Sciences",
    "Chemistry": "Department of Chemistry",
    "Physics": "Department of Physics and Astronomy",
    "Biochemistry": "Department of Biochemistry",
    "Earth Sciences": "Department of Earth, Atmospheric, and Planetary Sciences",
    "Atmospheric Science": "Department of Earth, Atmospheric, and Planetary Sciences",
    "Management": "Mitch Daniels School of Business",
    "Accounting": "School of Accounting",
    "Finance": "School of Accounting and Finance",
    "Marketing": "Department of Marketing",
    "Supply Chain Management": "Department of Supply Chain and Operations Management",
    "Economics": "Department of Economics",
    "Psychology": "Department of Psychological Sciences",
    "Political Science": "Department of Political Science",
    "History": "Department of History",
    "English": "Department of English",
    "Communication": "Brian Lamb School of Communication",
    "Journalism": "School of Communication",
    "Sociology": "Department of Sociology",
    "Anthropology": "Department of Anthropology",
    "Philosophy": "Department of Philosophy",
    "Foreign Languages": "School of Languages and Cultures",
    "Linguistics": "Department of Linguistics",
    "Visual Arts": "Patti and Rusty Rueff School of Design, Art, and Performance",
    "Theatre": "Patti and Rusty Rueff School of Design, Art, and Performance",
    "Music": "Patti and Rusty Rueff School of Design, Art, and Performance",
    "Landscape Architecture": "Department of Horticulture and Landscape Architecture",
    "Architecture": "School of Architecture and Built Environment",
    "Nursing": "School of Nursing",
    "Public Health": "School of Public Health",
    "Nutrition Science": "Department of Nutrition Science",
    "Human Development and Family Studies": "Department of Human Development and Family Studies",
    "Kinesiology": "Department of Health and Kinesiology",
    "Pharmaceutical Sciences": "College of Pharmacy",
    "Veterinary Medicine": "College of Veterinary Medicine",
    "Veterinary Biomedical Sciences": "Department of Comparative Pathobiology",
    "Agricultural Economics": "Department of Agricultural Economics",
    "Animal Sciences": "Department of Animal Sciences",
    "Food Science": "Department of Food Science",
    "Plant Science": "Department of Botany and Plant Pathology",
    "Soil Science": "Department of Agronomy",
    "Forestry": "Department of Forestry and Natural Resources",
    "Agriculture": "College of Agriculture",
    "Education": "College of Education",
    "Engineering Technology": "Purdue Polytechnic Institute",
    "Electrical Engineering Technology": "School of Engineering Technology",
    "Mechanical Engineering Technology": "School of Engineering Technology",
    "Architectural Engineering Technology": "School of Construction Management Technology",
    "Industrial Technology": "School of Engineering Technology",
    "Aviation Management": "School of Aviation and Transportation Technology",
    "Information Technology": "Department of Computer and Information Technology",
    "Computer Graphics Technology": "Department of Computer Graphics Technology",
    # De-rolled-up CIP fields → Purdue's real owning unit (verified 2026-06-19).
    "Hospitality and Tourism Management": "White Lodging-J.W. Marriott, Jr. School of Hospitality and Tourism Management",
    "Industrial Engineering Technology": "School of Engineering Technology",
    "Medical Laboratory Sciences": "School of Health Sciences",
    "Selling and Sales Management": "Division of Consumer Science",
    "Retail Management": "White Lodging-J.W. Marriott, Jr. School of Hospitality and Tourism Management",
    "Film and Video Studies": "Patti and Rusty Rueff School of Design, Art, and Performance",
    "Learning Design and Technology": "Department of Curriculum and Instruction",
    "Biochemistry and Molecular Biology": "Department of Biochemistry",
    "Comparative Pathobiology": "Department of Comparative Pathobiology",
}

# Slug → full published program name (explicit flagship rows).
SLUG_PROGRAM_NAMES: dict[str, str] = {
    "purdue-computer-science-bs": "Bachelor of Science in Computer Science",
    "purdue-aerospace-engineering-bs": "Bachelor of Science in Aerospace Engineering",
    "purdue-mechanical-engineering-bs": "Bachelor of Science in Mechanical Engineering",
    "purdue-electrical-engineering-bs": "Bachelor of Science in Electrical Engineering",
    "purdue-nursing-bs": "Bachelor of Science in Nursing",
    "purdue-pharmacy-prof": "Doctor of Pharmacy",
    "purdue-veterinary-medicine-prof": "Doctor of Veterinary Medicine",
    "purdue-business-administration-bs": "Bachelor of Science in Management",
    "purdue-agricultural-economics-bs": "Bachelor of Science in Agricultural Economics",
    "purdue-psychology-bs": "Bachelor of Science in Psychological Sciences",
}

SLUG_DEPARTMENTS: dict[str, str] = {
    "purdue-computer-science-bs": "Department of Computer Science",
    "purdue-aerospace-engineering-bs": "School of Aeronautics and Astronautics",
    "purdue-mechanical-engineering-bs": "School of Mechanical Engineering",
    "purdue-electrical-engineering-bs": "Elmore Family School of Electrical and Computer Engineering",
    "purdue-nursing-bs": "School of Nursing",
    "purdue-pharmacy-prof": "College of Pharmacy",
    "purdue-veterinary-medicine-prof": "College of Veterinary Medicine",
    "purdue-business-administration-bs": "Mitch Daniels School of Business",
    "purdue-agricultural-economics-bs": "Department of Agricultural Economics",
    "purdue-psychology-bs": "Department of Psychological Sciences",
}

# Per-slug full resolution for CIP-rollup rows whose real Purdue name / owning unit /
# college differs from the federal taxonomy or diverges across credential levels.
# (program_name, department, school) — verified against admissions.purdue.edu + catalog.
SLUG_OVERRIDES: dict[str, tuple[str, str, str]] = {
    "purdue-clinical-medical-laboratory-science-research-and-allied-professions-bs": (
        "Bachelor of Science in Medical Laboratory Sciences",
        "School of Health Sciences",
        "College of Health and Human Sciences",
    ),
    "purdue-film-video-and-photographic-arts-bs": (
        "Bachelor of Arts in Film and Video Studies",
        "Patti and Rusty Rueff School of Design, Art, and Performance",
        "College of Liberal Arts",
    ),
    "purdue-educational-instructional-media-design-cert": (
        "Graduate Certificate in Learning Design and Technology",
        "Department of Curriculum and Instruction",
        "College of Education",
    ),
    "purdue-family-and-consumer-sciences-human-sciences-business-services-bs": (
        "Bachelor of Science in Retail Management",
        "White Lodging-J.W. Marriott, Jr. School of Hospitality and Tourism Management",
        "College of Health and Human Sciences",
    ),
    "purdue-family-and-consumer-sciences-human-sciences-general-bs": (
        "Bachelor of Science in Selling and Sales Management",
        "Division of Consumer Science",
        "College of Health and Human Sciences",
    ),
    "purdue-biochemistry-biophysics-and-molecular-biology-bs": (
        "Bachelor of Science in Biochemistry",
        "Department of Biochemistry",
        "College of Agriculture",
    ),
    "purdue-biochemistry-biophysics-and-molecular-biology-ms": (
        "Master of Science in Biochemistry and Molecular Biology",
        "Department of Biochemistry",
        "College of Agriculture",
    ),
    "purdue-physiology-pathology-and-related-sciences-ms": (
        "Master of Science in Comparative Pathobiology",
        "Department of Comparative Pathobiology",
        "College of Veterinary Medicine",
    ),
}

# Field (after alias) → real owning COLLEGE override, where the IPEDS row's college was wrong.
SCHOOL_OVERRIDE_BY_FIELD: dict[str, str] = {
    "Hospitality and Tourism Management": "College of Health and Human Sciences",
    "Kinesiology": "College of Health and Human Sciences",
}

# CIP-rollup rows dropped because no single real Purdue degree name can be verified for
# that (CIP × credential), or because the resolution would duplicate an existing real row.
# Omitting an unverifiable row is correct; a guessed real name would be fabrication, and a
# rollup name ("X/Y", "X, Y, and Z") is itself a defect (enrich-profile miss #2).
DROP_SLUGS: frozenset[str] = frozenset({
    # CIP 15.0101 Architectural Eng. Tech. — no single verified Purdue degree across levels
    "purdue-architectural-engineering-technologies-technicians-bs",
    "purdue-architectural-engineering-technologies-technicians-cert",
    "purdue-architectural-engineering-technologies-technicians-ms",
    # Business/Corporate Communications — ambiguous (Strategic Comm. cert vs MS)
    "purdue-business-corporate-communications-cert",
    "purdue-business-corporate-communications-ms",
    "purdue-cultural-studies-critical-theory-and-analysis-cert",
    # duplicates the existing real "Bachelor of Science in Health Sciences" row
    "purdue-health-services-allied-health-health-sciences-general-bs",
    "purdue-intercultural-multicultural-and-diversity-studies-cert",
    # duplicates the existing real "Graduate Certificate in Interdisciplinary Studies"; MS unverified
    "purdue-multi-interdisciplinary-studies-general-cert",
    "purdue-multi-interdisciplinary-studies-general-ms",
    # Rhetoric & Composition/Writing Studies — real name diverges by level; not a Purdue BS
    "purdue-rhetoric-and-composition-writing-studies-bs",
    "purdue-rhetoric-and-composition-writing-studies-cert",
    # No standalone Purdue Zoology degree (covered under Biological Sciences / Animal Sciences)
    "purdue-zoology-animal-biology-bs",
    "purdue-zoology-animal-biology-cert",
    "purdue-zoology-animal-biology-ms",
    # overlaps the real Retail Management / Selling and Sales Management majors
    "purdue-general-sales-merchandising-and-related-marketing-operations-bs",
    "purdue-clinical-counseling-and-applied-psychology-cert",
    "purdue-bilingual-multilingual-and-multicultural-education-cert",
    "purdue-educational-assessment-evaluation-and-research-cert",
    # Physiology/Pathology — only the MS (Comparative Pathobiology) is verifiable; BS/cert dropped
    "purdue-physiology-pathology-and-related-sciences-bs",
    "purdue-physiology-pathology-and-related-sciences-cert",
    # uncertain certificate; the BS (Biochemistry) and MS (Biochem & Molecular Biology) are kept
    "purdue-biochemistry-biophysics-and-molecular-biology-cert",
    # CIP rollups with no verifiable single Purdue degree name
    "purdue-mental-and-social-health-services-and-allied-professions-cert",
    "purdue-military-technologies-and-applied-sciences-other-ms",
})


# Liberal-arts fields that confer a B.A. at Purdue (College of Liberal Arts).
BA_FIELDS = frozenset({
    "Anthropology", "Area Studies", "Classics", "Communication", "East Asian Languages",
    "Economics", "English", "Film and Video", "Foreign Languages", "German", "History",
    "Intercultural Studies", "Journalism", "Linguistics", "Philosophy", "Political Science",
    "Public Relations", "Religious Studies", "Romance Languages", "Slavic Languages",
    "Sociology", "Theatre", "Visual Arts", "Interdisciplinary Studies", "Liberal Arts",
    "Criminal Justice", "Public Policy",
})

_ROLLUP_SUFFIX_RE = re.compile(r",\s*(General|Other)$")


def clean_cip_field(name: str) -> str:
    """Strip federal CIP rollup suffixes and apply alias table."""
    cleaned = _ROLLUP_SUFFIX_RE.sub("", name.strip())
    return FIELD_ALIASES.get(name, FIELD_ALIASES.get(cleaned, cleaned))
