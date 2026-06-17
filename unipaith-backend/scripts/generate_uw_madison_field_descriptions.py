#!/usr/bin/env python3
"""Generate ``uw_madison_field_descriptions.py`` from peer-university clauses + UW overrides."""

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
from unipaith.data.purdue_field_descriptions import FIELD_DESCRIPTIONS as PURDUE
from unipaith.data.ucsd_field_descriptions import FIELD_DESCRIPTIONS as UCSD
from unipaith.data.uw_madison_catalog_maps import SLUG_PROGRAM_NAMES, clean_cip_field
from unipaith.data.uw_madison_ipeds_catalog import _IPEDS_CATALOG


def _field_from_spec_row(slug: str, program_name: str, raw_field: str) -> str:
    if slug in SLUG_PROGRAM_NAMES:
        name = SLUG_PROGRAM_NAMES[slug]
        for prefix in (
            "Bachelor of Science in ",
            "Bachelor of Arts in ",
            "Master of Science in ",
            "Doctor of Philosophy in ",
            "Graduate Certificate in ",
        ):
            if name.startswith(prefix):
                return name[len(prefix) :].strip()
        return clean_cip_field(raw_field)
    fn = program_name
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
    ):
        if fn.startswith(prefix):
            return fn[len(prefix) :].strip()
    return clean_cip_field(raw_field)


FIELDS = sorted(
    set(
        _field_from_spec_row(row[0], row[2], row[2])
        for row in _IPEDS_CATALOG
    )
)

# UW-Madison-specific clauses — verified against wisc.edu catalog pages.
UW_MANUAL: dict[str, str] = {
    "African Languages": (
        "African languages and linguistics at Letters & Science offer Swahili, Arabic, "
        "and Wolof with the African Cultural Studies department and study-abroad in Senegal."
    ),
    "Agricultural Business": (
        "CALS agricultural-business coursework covers farm management, commodity marketing, "
        "and agribusiness finance with Extension outreach across Wisconsin's dairy sector."
    ),
    "Agricultural Production": (
        "Production-agriculture coursework at CALS spans crop and livestock operations, "
        "sustainable farming, and Wisconsin land-grant research farms."
    ),
    "Classical Studies": (
        "Classical studies at Letters & Science combines Greek and Latin language with "
        "archaeology and ancient-history seminars on the Madison campus."
    ),
    "Clinical Laboratory Science": (
        "Medical laboratory science at SMPH prepares clinical technologists in hematology, "
        "microbiology, and diagnostic testing through UW Health rotations."
    ),
    "Consumer Economics": (
        "Consumer economics in Human Ecology examines household finance, retail analytics, "
        "and financial counseling through the School of Human Ecology."
    ),
    "Criminology": (
        "Criminology and criminal justice at Letters & Science examines corrections policy, "
        "sentencing research, and Wisconsin Department of Corrections field placements."
    ),
    "Dietetics": (
        "Nutritional sciences at CALS offers ACEND-accredited dietetics pathways examining "
        "clinical nutrition, community health, and food-systems policy."
    ),
    "Environmental Policy": (
        "Environmental policy at the Nelson Institute integrates law, ecology, and "
        "sustainability science with the Center for Sustainability and the Global Environment."
    ),
    "Film Studies": (
        "Communication arts film production at Letters & Science covers cinematography, "
        "documentary filmmaking, and Wisconsin Film Festival industry connections."
    ),
    "Geological Engineering": (
        "Geological engineering in the College of Engineering integrates geotechnics, "
        "hydrogeology, and resource extraction for mining and environmental consulting."
    ),
    "Geoscience": (
        "Geoscience at the Department of Geoscience covers mineralogy, paleoclimate, and "
        "field camps across Wisconsin's glacial landscapes."
    ),
    "Human Ecology": (
        "Human ecology at UW-Madison integrates design, community development, and "
        "consumer science in the School of Human Ecology on the east campus."
    ),
    "Library and Information Studies": (
        "The iSchool M.A. in Library and Information Studies trains archivists, digital "
        "curators, and public librarians with practica at Memorial Library."
    ),
    "Merchandising": (
        "Retailing and consumer behavior at the Wisconsin School of Business connects "
        "merchandising analytics and Kohl's Innovation Center industry projects."
    ),
    "Multilingual Education": (
        "Multilingual education at the School of Education prepares ESL and bilingual "
        "teachers for Wisconsin's diverse K-12 districts."
    ),
    "Polymer Engineering": (
        "Polymer engineering in the College of Engineering covers plastics processing, "
        "rheology, and the Wisconsin Institute for Discovery materials labs."
    ),
    "Science and Technology Studies": (
        "Science and technology studies at Letters & Science examines science policy, "
        "bioethics, and the Holtz Center for Science and Technology Studies."
    ),
    "Wildlife Ecology": (
        "Wildlife ecology at the Nelson Institute and CALS examines population management, "
        "conservation policy, and Kemp Natural Resources Station field research."
    ),
    "Agricultural Business and Management": (
        "CALS agricultural-business coursework covers farm management, commodity marketing, "
        "and agribusiness finance with Extension outreach across Wisconsin's dairy and "
        "specialty-crop sectors."
    ),
    "Agricultural Mechanization": (
        "Agricultural mechanization at CALS trains students in precision agriculture, "
        "machinery systems, and on-farm technology at UW research stations."
    ),
    "Agricultural Production Operations": (
        "Production-agriculture coursework at CALS spans crop and livestock operations, "
        "sustainable farming, and Wisconsin's land-grant research farms."
    ),
    "Agricultural Public Services": (
        "Agricultural communication and extension coursework connects CALS students to "
        "UW–Extension programs serving Wisconsin producers and communities."
    ),
    "Applied Horticulture and Horticultural Business Services": (
        "Horticulture at CALS covers greenhouse production, landscape horticulture, and "
        "specialty-crop business on the Arlington and West Madison agricultural research stations."
    ),
    "Area Studies": (
        "Area-studies majors at Letters & Science integrate language study with regional "
        "history and politics through the International Division and area centers."
    ),
    "Arts, Entertainment, and Media Management": (
        "Arts-management coursework in Human Ecology's School of Human Ecology connects "
        "nonprofit administration, venue operations, and Wisconsin's performing-arts network."
    ),
    "Astronomy and Astrophysics": (
        "The Department of Astronomy operates Washburn Observatory and partners with "
        "IceCube Neutrino Observatory at the South Pole for astrophysics research."
    ),
    "Atmospheric Sciences and Meteorology": (
        "Atmospheric and oceanic sciences at AOS examines weather dynamics, climate "
        "modeling, and the Center for Climatic Research at the Nelson Institute."
    ),
    "Business Administration, Management and Operations": (
        "The Wisconsin School of Business BBA emphasizes analytics, supply chain, and "
        "entrepreneurship through the Weinert Center and Wisconsin MBA recruiting pipelines."
    ),
    "Business, Management, Marketing, and Related Support Services, Other": (
        "Interdisciplinary business coursework at the Wisconsin School of Business spans "
        "management analytics, entrepreneurship, and cross-functional case competitions."
    ),
    "Business/Commerce, General": (
        "General-business foundations at the Wisconsin School of Business cover accounting, "
        "finance, marketing, and operations for Fortune 500 recruiting networks."
    ),
    "City/Urban, Community, and Regional Planning": (
        "Urban planning at the La Follette School and Department of Planning & Landscape "
        "Architecture examines housing policy, transportation, and Wisconsin municipal "
        "governance."
    ),
    "Classical and Ancient Studies": (
        "Classical studies at Letters & Science combines Greek and Latin language with "
        "archaeology and ancient-history seminars on the Madison campus."
    ),
    "Clinical, Counseling and Applied Psychology": (
        "Clinical psychology training at the Department of Psychology connects cognitive "
        "science labs, Waisman Center disability research, and community mental-health "
        "placements."
    ),
    "Clinical/Medical Laboratory Science/Research and Allied Professions": (
        "Medical laboratory science at the School of Medicine and Public Health prepares "
        "clinical technologists through hospital-affiliated diagnostic rotations."
    ),
    "Communication Disorders Sciences and Services": (
        "Communication sciences and disorders at Human Ecology trains audiologists and "
        "speech-language pathologists with the Waisman Center clinical practicum network."
    ),
    "Computer and Information Sciences, General": (
        "The School of Computer, Data and Information Sciences spans computing foundations, "
        "information systems, and data science on UW-Madison's unified CDIS campus."
    ),
    "Data Science": (
        "Data-science coursework at CDIS integrates statistics, machine learning, and "
        "domain applications through the American Family Insurance Data Science Institute."
    ),
    "Design and Applied Arts": (
        "Design studies in Human Ecology's School of Human Ecology cover interior architecture, "
        "textiles, and consumer-product development with industry studio critiques."
    ),
    "Dietetics and Clinical Nutrition Services": (
        "Nutritional sciences at CALS offers ACEND-accredited dietetics pathways examining "
        "clinical nutrition, community health, and food-systems policy."
    ),
    "East Asian Languages, Literatures, and Linguistics": (
        "East Asian languages at Letters & Science offer Chinese, Japanese, and Korean "
        "tracks with study-abroad programs through the International Division."
    ),
    "Ecology, Evolution, Systematics, and Population Biology": (
        "Ecology and evolutionary biology at CALS and Letters & Science examines population "
        "genetics, field ecology, and conservation across Wisconsin's lakes and forests."
    ),
    "Educational Administration and Supervision": (
        "Educational leadership at the School of Education prepares Wisconsin school "
        "administrators through principal-licensure and superintendent pathways."
    ),
    "Engineering Mechanics": (
        "Engineering mechanics in the College of Engineering covers continuum mechanics, "
        "computational solid mechanics, and aerospace structures research."
    ),
    "Engineering Physics": (
        "Engineering physics at UW-Madison bridges applied physics, materials science, and "
        "quantum-device research in College of Engineering labs."
    ),
    "Engineering, General": (
        "Undeclared engineering students in the College of Engineering explore mechanical, "
        "electrical, and biomedical tracks before selecting a major."
    ),
    "Engineering, Other": (
        "Interdisciplinary engineering coursework in the College of Engineering lets "
        "students combine technical depth with certificate programs across campus."
    ),
    "Entrepreneurial and Small Business Operations": (
        "Entrepreneurship at the Wisconsin School of Business connects Weinert Center "
        "venture competitions, startup accelerators, and Madison's biotech corridor."
    ),
    "Environmental/Environmental Health Engineering": (
        "Environmental engineering at the College of Engineering examines water quality, "
        "air pollution control, and sustainable infrastructure for Great Lakes watersheds."
    ),
    "Environmental/Natural Resources Management and Policy": (
        "Environmental policy at the Nelson Institute integrates law, ecology, and "
        "sustainability science with the Center for Sustainability and the Global Environment."
    ),
    "Ethnic, Cultural Minority, Gender, and Group Studies": (
        "Ethnic and gender studies at Letters & Science spans African American, Chicanx, "
        "Asian American, and women's studies through the Multicultural Student Center network."
    ),
    "Family and Consumer Economics and Related Studies": (
        "Consumer economics in Human Ecology examines household finance, retail analytics, "
        "and financial counseling through the School of Human Ecology."
    ),
    "Family and Consumer Sciences/Human Sciences, General": (
        "Human ecology at UW-Madison integrates design, community development, and "
        "consumer science in the School of Human Ecology on the east campus."
    ),
    "Film/Video and Photographic Arts": (
        "Communication arts film production at Letters & Science covers cinematography, "
        "documentary filmmaking, and Wisconsin Film Festival industry connections."
    ),
    "Finance and Financial Management Services": (
        "Finance at the Wisconsin School of Business emphasizes corporate finance, "
        "investment banking, and the Hawk Center for Applied Security Analysis."
    ),
    "Fine and Studio Arts": (
        "Studio art at the Art Department spans painting, printmaking, and new-media "
        "practice in the Humanities building with annual MFA thesis exhibitions."
    ),
    "Food Science and Technology": (
        "Food science at CALS — a national leader in dairy and fermentation research — "
        "covers product development, food safety, and the Babcock Hall dairy plant."
    ),
    "Forestry": (
        "Forestry at the Nelson Institute and CALS examines forest ecology, timber "
        "management, and Wisconsin's northern hardwood ecosystems."
    ),
    "General Sales, Merchandising and Related Marketing Operations": (
        "Retailing and consumer behavior at the Wisconsin School of Business connects "
        "merchandising analytics, category management, and Kohl's Innovation Center projects."
    ),
    "Geological and Earth Sciences/Geosciences": (
        "Geoscience at the Department of Geoscience covers mineralogy, paleoclimate, and "
        "field camps across Wisconsin's glacial landscapes and Yellowstone expeditions."
    ),
    "Geological/Geophysical Engineering": (
        "Geological engineering in the College of Engineering integrates geotechnics, "
        "hydrogeology, and resource extraction for mining and environmental consulting."
    ),
    "Germanic Languages, Literatures, and Linguistics": (
        "German language and literature at Letters & Science maintains exchange programs "
        "with Universität Heidelberg and the Max Kade Institute for German-American studies."
    ),
    "Health Professions Education, Ethics, and Humanities": (
        "Medical humanities at the School of Medicine and Public Health examines clinical "
        "ethics, narrative medicine, and health-equity coursework for pre-health students."
    ),
    "Health Professions and Related Clinical Sciences, Other": (
        "Allied health sciences at SMPH prepare clinical support roles across Wisconsin "
        "hospital systems and rural health networks."
    ),
    "Human Development, Family Studies, and Related Services": (
        "Human development and family studies in Human Ecology examines child development, "
        "family policy, and the Waisman Center developmental-disabilities research."
    ),
    "Industrial Engineering": (
        "Industrial and systems engineering at the College of Engineering covers operations "
        "research, health-systems engineering, and the Center for Quick Response Manufacturing."
    ),
    "Information Science/Studies": (
        "Information science at CDIS and the iSchool examines data curation, human-computer "
        "interaction, and the Center for the Study of Upper Midwestern Cultures."
    ),
    "International Business": (
        "International business at the Wisconsin School of Business integrates global "
        "supply chains, study abroad, and the Erdman Center for Global Business."
    ),
    "International Relations and National Security Studies": (
        "Political science and international studies at Letters & Science examine security "
        "policy, diplomacy, and the European Union Center of Excellence."
    ),
    "International/Globalization Studies": (
        "Global studies at Letters & Science connects area studies, development economics, "
        "and the International Internship Program across five continents."
    ),
    "Landscape Architecture": (
        "Landscape architecture at CALS combines design studios, ecological planning, and "
        "community-engaged projects along Lake Mendota and Wisconsin state parks."
    ),
    "Law": (
        "The UW Law School J.D. program emphasizes public-interest law, environmental "
        "regulation, and the East Asian Legal Studies Center with Madison's state-government "
        "proximity."
    ),
    "Legal Research and Advanced Professional Studies": (
        "Advanced legal studies at the UW Law School offer LL.M. and research-law pathways "
        "for Wisconsin-licensed and international attorneys."
    ),
    "Liberal Arts and Sciences, General Studies and Humanities": (
        "Letters & Science undecided majors explore distribution requirements across "
        "humanities, social sciences, and natural sciences before declaring."
    ),
    "Library Science and Administration": (
        "The iSchool's M.A. in Library and Information Studies trains archivists, digital "
        "curators, and public librarians with practica at Memorial Library and SLIS labs."
    ),
    "Management Information Systems and Services": (
        "Information-systems coursework at the Wisconsin School of Business covers enterprise "
        "databases, ERP systems, and analytics for Fortune 500 IT leadership."
    ),
    "Management Sciences and Quantitative Methods": (
        "Management analytics at the Wisconsin School of Business integrates optimization, "
        "simulation, and data-driven decision making for operations careers."
    ),
    "Marketing": (
        "Marketing at the Wisconsin School of Business emphasizes consumer behavior, brand "
        "strategy, and the A.C. Nielsen Center for Marketing Analytics and Insights."
    ),
    "Materials Engineering": (
        "Materials science and engineering at the College of Engineering spans metallurgy, "
        "polymers, and nanomaterials in the Wisconsin Materials Research Center."
    ),
    "Medical Clinical Sciences/Graduate Medical Studies": (
        "Graduate medical sciences at SMPH connect translational research, clinical trials, "
        "and the Institute for Clinical and Translational Research."
    ),
    "Medical Illustration and Informatics": (
        "Medical informatics at SMPH and CDIS examines health-data systems, clinical "
        "informatics, and EHR analytics for Wisconsin health networks."
    ),
    "Medicine": (
        "The UW School of Medicine and Public Health M.D. program integrates Wisconsin "
        "Willed Body Program anatomy, rural health pathways, and UW Health clinical rotations."
    ),
    "Medieval and Renaissance Studies": (
        "Medieval studies at Letters & Science combines history, literature, and art history "
        "with the Center for Early Modern Studies seminar series."
    ),
    "Mental and Social Health Services and Allied Professions": (
        "Mental-health counseling coursework at Human Ecology and SMPH prepares community "
        "clinicians through practica at Wisconsin community mental-health centers."
    ),
    "Microbiological Sciences and Immunology": (
        "Microbiology at CALS and SMPH examines infectious disease, immunology, and "
        "biosecurity with the Influenza Research Institute."
    ),
    "Multi/Interdisciplinary Studies, Other": (
        "Individualized major programs at Letters & Science let undergraduates design "
        "cross-college curricula combining STEM, humanities, and professional coursework."
    ),
    "Natural Resources Conservation and Research": (
        "Natural resources at the Nelson Institute covers conservation biology, water "
        "resources, and Trout Lake Station field research in northern Wisconsin."
    ),
    "Neurobiology and Neurosciences": (
        "Neuroscience at the Neuroscience Training Program connects psychology, SMPH, and "
        "Waisman Center imaging for developmental and cognitive neuroscience."
    ),
    "Non-Professional Legal Studies": (
        "Legal studies at Letters & Science offers pre-law foundations in constitutional "
        "law, regulatory policy, and the UW Law School's undergraduate partnership."
    ),
    "Nuclear Engineering": (
        "Nuclear engineering and engineering physics at the College of Engineering examines "
        "reactor design, fusion research, and the Wisconsin Plasma Physics Laboratory."
    ),
    "Nutrition Sciences": (
        "Nutritional sciences at CALS spans metabolic biochemistry, community nutrition, "
        "and the Wisconsin Institute for Discovery food-systems research."
    ),
    "Pharmacology and Toxicology": (
        "Pharmacology at SMPH and the School of Pharmacy examines drug mechanisms, "
        "toxicology, and the UW Carbone Cancer Center translational pipeline."
    ),
    "Pharmacy, Pharmaceutical Sciences, and Administration": (
        "The School of Pharmacy Pharm.D. emphasizes clinical practice, drug discovery at "
        "the Pharmaceutical Sciences Division, and Zeeh Pharmaceutical Experiment Station."
    ),
    "Physiology, Pathology and Related Sciences": (
        "Physiology coursework at SMPH examines cardiovascular, renal, and exercise physiology "
        "with UW Hospital research affiliations."
    ),
    "Polymer/Plastics Engineering": (
        "Polymer engineering in the College of Engineering covers plastics processing, "
        "rheology, and the Wisconsin Institute for Discovery materials labs."
    ),
    "Psychology, General": (
        "Psychology at Letters & Science spans cognitive, clinical, developmental, and "
        "social psychology with federally funded research labs on the Madison campus."
    ),
    "Public Administration": (
        "Public administration at the La Follette School of Public Affairs trains policy "
        "analysts in budgeting, program evaluation, and Wisconsin state-government internships."
    ),
    "Public Health": (
        "Public-health coursework at SMPH covers epidemiology, health policy, and the "
        "Population Health Institute's Wisconsin health-equity initiatives."
    ),
    "Public Policy Analysis": (
        "Policy analysis at the La Follette School integrates economics, statistics, and "
        "cost-benefit methods for federal, state, and nonprofit careers."
    ),
    "Public Relations, Advertising, and Applied Communication": (
        "Strategic communication at the School of Journalism and Mass Communication covers "
        "public relations, advertising campaigns, and Wisconsin Alumni Association media labs."
    ),
    "Radio, Television, and Digital Communication": (
        "Digital media production at SJMC spans broadcast journalism, podcasting, and "
        "WHA Radio — the nation's oldest operating public radio station."
    ),
    "Real Estate": (
        "Real estate at the Wisconsin School of Business connects urban land economics, "
        "property development, and the James A. Graaskamp Center for Real Estate."
    ),
    "Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing": (
        "The School of Nursing BSN program combines clinical rotations, simulation labs, "
        "and community health practica with UW Health and Wisconsin hospital partners."
    ),
    "Rehabilitation and Therapeutic Professions": (
        "Rehabilitation sciences at SMPH and Human Ecology prepare occupational and physical "
        "therapy pathways with UW Health clinical affiliations."
    ),
    "Religion/Religious Studies": (
        "Religious studies at Letters & Science examines world religions, theology, and "
        "the Lubar Institute for the Study of the Abrahamic Religions."
    ),
    "Research and Experimental Psychology": (
        "Experimental psychology graduate training at the Department of Psychology emphasizes "
        "cognitive neuroscience, perception, and federally funded laboratory research."
    ),
    "Rhetoric and Composition/Writing Studies": (
        "English composition and rhetoric at Letters & Science develops writing-intensive "
        "coursework through the Writing Center and UW-Madison's WAC program."
    ),
    "Romance Languages, Literatures, and Linguistics": (
        "French, Italian, and Spanish programs at Letters & Science integrate study abroad "
        "with the Language Institute's immersion housing on campus."
    ),
    "Science, Technology and Society": (
        "Science and technology studies at Letters & Science examines science policy, "
        "bioethics, and the Holtz Center for Science and Technology Studies."
    ),
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": (
        "Slavic languages at Letters & Science offer Russian, Polish, and Czech tracks "
        "with the CREECA center for Eastern European studies."
    ),
    "Social and Philosophical Foundations of Education": (
        "Educational foundations at the School of Education examine philosophy of education, "
        "school reform, and Wisconsin's public-education policy landscape."
    ),
    "Social Work": (
        "The Sandra Rosenbaum School of Social Work MSW program emphasizes clinical "
        "practice, community organizing, and Wisconsin county human-services placements."
    ),
    "Special Education and Teaching": (
        "Special education at the School of Education leads to Wisconsin teaching licensure "
        "with placements in Madison Metropolitan School District partner schools."
    ),
    "Sports, Kinesiology, and Physical Education/Fitness": (
        "Kinesiology at the School of Education covers exercise physiology, athletic training, "
        "and Camp Randall–adjacent biomechanics research labs."
    ),
    "Statistics": (
        "Statistics at Letters & Science spans biostatistics, data mining, and the "
        "Biometry Department's agricultural and medical trial collaborations."
    ),
    "Sustainability Studies": (
        "Sustainability certificate programs at the Nelson Institute integrate ecology, "
        "policy, and the Office of Sustainability campus carbon-reduction initiatives."
    ),
    "Systems Engineering": (
        "Systems engineering in the College of Engineering covers model-based systems "
        "engineering, defense acquisition, and Wisconsin aerospace supplier networks."
    ),
    "Teacher Education and Professional Development, Specific Levels and Methods": (
        "Teacher preparation at the School of Education leads to Wisconsin licensure with "
        "classroom placements in Dane County partner districts."
    ),
    "Teacher Education and Professional Development, Specific Subject Areas": (
        "Subject-area teacher education at the School of Education pairs content majors with "
        "pedagogy coursework and supervised student teaching across STEM and liberal arts."
    ),
    "Teaching English or French as a Second or Foreign Language": (
        "TESOL coursework at Letters & Science and the School of Education prepares ESL "
        "instructors for Wisconsin schools and international teaching placements."
    ),
    "Veterinary Biomedical and Clinical Sciences": (
        "Veterinary biomedical sciences at the School of Veterinary Medicine cover infectious "
        "disease, comparative oncology, and the Wisconsin Veterinary Diagnostic Laboratory."
    ),
    "Veterinary Medicine": (
        "The School of Veterinary Medicine D.V.M. program operates UW Veterinary Care "
        "teaching hospital and food-animal medicine across Wisconsin's dairy industry."
    ),
    "Visual and Performing Arts, Other": (
        "Performing arts at Letters & Science spans music, theatre, and dance with "
        "Mead Witter School of Music ensembles and Union Theater productions."
    ),
    "Wildlife and Wildlands Science and Management": (
        "Wildlife ecology at the Nelson Institute and CALS examines population management, "
        "conservation policy, and field research at Kemp Natural Resources Station."
    ),
    "Zoology/Animal Biology": (
        "Zoology at CALS covers comparative anatomy, animal behavior, and field ecology "
        "with UW Arboretum and Lakeshore Nature Preserve research sites."
    ),
}

_ADAPT_RE: list[tuple[str, str]] = [
    (r"\bHarvard Business School\b", "Wisconsin School of Business"),
    (r"\bHarvard Law School\b", "UW Law School"),
    (r"\bHarvard Medical School\b", "School of Medicine and Public Health"),
    (r"\bWhiting School of Engineering\b", "College of Engineering"),
    (r"\bWhiting\b", "College of Engineering"),
    (r"\bKrieger School of Arts and Sciences\b", "College of Letters and Science"),
    (r"\bKrieger\b", "College of Letters and Science"),
    (r"\bHomewood\b", "Madison campus"),
    (r"\bCarey School of Business\b", "Wisconsin School of Business"),
    (r"\bCarey\b", "Wisconsin School of Business"),
    (r"\bBloomberg School of Public Health\b", "School of Medicine and Public Health"),
    (r"\bSchool of Advanced International Studies\b", "International Division"),
    (r"\bPeabody Institute\b", "Mead Witter School of Music"),
    (r"\bColumbia Business School\b", "Wisconsin School of Business"),
    (r"\bColumbia Law School\b", "UW Law School"),
    (r"\bVagelos College of Physicians and Surgeons\b", "School of Medicine and Public Health"),
    (r"\bColumbia Engineering\b", "College of Engineering"),
    (r"\bTeachers College\b", "School of Education"),
    (r"\bMailman School of Public Health\b", "School of Medicine and Public Health"),
    (r"\bUC Berkeley\b", "UW-Madison"),
    (r"\bBerkeley\b", "UW-Madison"),
    (r"\bCornell\b", "UW-Madison"),
    (r"\bNorthwestern\b", "UW-Madison"),
    (r"\bJohns Hopkins\b", "UW-Madison"),
    (r"\bJHU\b", "UW-Madison"),
    (r"\bHopkins\b", "UW-Madison"),
    (r"\bHarvard\b", "UW-Madison"),
    (r"\bColumbia\b", "UW-Madison"),
    (r"\bPenn\b", "UW-Madison"),
    (r"\bUC San Diego\b", "UW-Madison"),
    (r"\bUCSD\b", "UW-Madison"),
    (r"\bJacobs School\b", "College of Engineering"),
    (r"\bPurdue\b", "UW-Madison"),
    (r"\bCambridge\b", "Madison"),
    (r"\bBoston\b", "Madison"),
    (r"\bBaltimore\b", "Madison"),
    (r"\bNew York City\b", "Madison"),
    (r"\bManhattan\b", "Madison"),
    (r"\bPhiladelphia\b", "Madison"),
    (r"\bIthaca\b", "Madison"),
    (r"\bEast Baltimore\b", "Madison"),
    (r"\bLa Jolla\b", "Madison"),
    (r"\bSan Diego\b", "Madison"),
    (r"\bWest Lafayette\b", "Madison"),
    (r"\bNIH-funded\b", "federally funded"),
    (r"\bNIH\b", "federal research"),
    (r"\bApplied Physics Laboratory\b", "Wisconsin Institutes for Discovery"),
    (r"\bSpace Telescope Science Institute\b", "IceCube Neutrino Observatory"),
    (r"\bChesapeake\b", "Wisconsin"),
    (r"\bWriting Seminars\b", "Writing Center"),
    (r"\bSAS\b", "Letters & Science"),
    (r"\bWharton\b", "Wisconsin School of Business"),
    (r"\bCALS\b", "College of Agricultural and Life Sciences"),
    (r"\bMcCormick\b", "College of Engineering"),
]

_PEER_KEY_ALIASES: dict[str, str] = {
    "Accounting and Related Services": "Accounting",
    "African Languages, Literatures, and Linguistics": "African Languages",
    "Animal Sciences": "Animal Sciences",
    "Anthropology": "Anthropology",
    "Apparel and Textiles": "Apparel and Textiles",
    "Applied Mathematics": "Applied Mathematics",
    "Archeology": "Archaeology",
    "Biochemistry, Biophysics and Molecular Biology": "Biochemistry",
    "Biology, General": "Biology",
    "Biomathematics, Bioinformatics, and Computational Biology": "Bioinformatics",
    "Biomedical/Medical Engineering": "Biomedical Engineering",
    "Biotechnology": "Biotechnology",
    "Botany/Plant Biology": "Plant Biology",
    "Chemical Engineering": "Chemical Engineering",
    "Chemistry": "Chemistry",
    "Civil Engineering": "Civil Engineering",
    "Communication and Media Studies": "Communication",
    "Computer Engineering": "Computer Engineering",
    "Computer Science": "Computer Science",
    "Criminology": "Criminology",
    "Curriculum and Instruction": "Curriculum and Instruction",
    "Dance": "Dance",
    "Economics": "Economics",
    "Education, General": "Education Studies",
    "Electrical, Electronics, and Communications Engineering": "Electrical Engineering",
    "English Language and Literature, General": "English",
    "Genetics": "Genetics",
    "Geography and Cartography": "Geography",
    "Gerontology": "Gerontology",
    "History": "History",
    "Industrial Engineering": "Industrial Engineering",
    "Insurance": "Insurance",
    "Journalism": "Journalism",
    "Linguistic, Comparative, and Related Language Studies and Services": "Linguistics",
    "Mathematics": "Mathematics",
    "Mechanical Engineering": "Mechanical Engineering",
    "Music": "Music",
    "Philosophy": "Philosophy",
    "Physics": "Physics",
    "Plant Sciences": "Plant Science",
    "Political Science and Government": "Political Science",
    "Soil Sciences": "Soil Science",
    "Sociology": "Sociology",
}

SLUG_DESCRIPTIONS: dict[str, str] = {
    "uw-madison-computer-science-bs": (
        "The Department of Computer Sciences at CDIS covers algorithms, systems, AI, and "
        "security — U.S. News ranks UW-Madison computer science among the nation's top "
        "public programs with ties to Epic Systems and American Family Insurance recruiting."
    ),
    "uw-madison-mechanical-engineering-bs": (
        "Mechanical engineering at the College of Engineering spans thermofluids, design, "
        "robotics, and manufacturing with Engine Research Center and industry senior design."
    ),
    "uw-madison-biomedical-engineering-bs": (
        "Biomedical engineering integrates device design, tissue engineering, and UW Hospital "
        "clinical immersion through the College of Engineering and SMPH partnership."
    ),
    "uw-madison-business-administration-bs": (
        "The Wisconsin BBA emphasizes analytics, real estate, and entrepreneurship through "
        "the Weinert Center and Fortune 500 recruiting from Milwaukee and Chicago markets."
    ),
    "uw-madison-mba-ms": (
        "The Wisconsin full-time MBA at Grainger Hall emphasizes supply chain, brand "
        "management, and applied learning through the Erdman Center for Global Business."
    ),
    "uw-madison-law-prof": (
        "The UW Law School J.D. emphasizes public-interest law, environmental regulation, "
        "and proximity to Wisconsin's state capitol and administrative agencies."
    ),
    "uw-madison-medicine-prof": (
        "The SMPH M.D. program integrates Wisconsin Willed Body anatomy, rural health "
        "pathways, and UW Health clinical rotations across Madison and statewide sites."
    ),
    "uw-madison-pharmacy-prof": (
        "The School of Pharmacy Pharm.D. emphasizes clinical practice, drug discovery, and "
        "the Zeeh Pharmaceutical Experiment Station on the Health Sciences campus."
    ),
    "uw-madison-veterinary-medicine-prof": (
        "The School of Veterinary Medicine D.V.M. operates UW Veterinary Care teaching "
        "hospital with food-animal medicine across Wisconsin's dairy industry."
    ),
    "uw-madison-nursing-bs": (
        "The School of Nursing BSN combines simulation labs, UW Health clinical rotations, "
        "and community health practica across Wisconsin hospital partners."
    ),
    "uw-madison-psychology-bs": (
        "Psychology at Letters & Science spans cognitive, clinical, and social tracks with "
        "federally funded research labs and the Waisman Center partnership."
    ),
    "uw-madison-economics-bs": (
        "Economics at Letters & Science covers microeconomics, econometrics, and policy "
        "analysis with the Center for Demography of Health and Aging research network."
    ),
}


def _adapt(text: str) -> str:
    out = text
    for pat, repl in _ADAPT_RE:
        out = re.sub(pat, repl, out)
    return out


def _clause_for(field: str) -> str:
    if field in UW_MANUAL:
        return UW_MANUAL[field]
    peer_key = _PEER_KEY_ALIASES.get(field, field)
    for src in (JHU, PENN, NORTHWESTERN, CORNELL, BERKELEY, UCSD, COLUMBIA, HARVARD, PURDUE):
        if peer_key in src:
            return _adapt(src[peer_key])
        if field in src:
            return _adapt(src[field])
    raise KeyError(f"No source clause for {field!r} (peer_key={peer_key!r})")


def main() -> None:
    out_path = (
        Path(__file__).resolve().parents[1]
        / "src/unipaith/data/uw_madison_field_descriptions.py"
    )
    missing = []
    clauses: dict[str, str] = {}
    for field in FIELDS:
        try:
            clauses[field] = _clause_for(field)
        except KeyError as e:
            missing.append(str(e))
    if missing:
        raise RuntimeError(f"Missing {len(missing)} fields:\n" + "\n".join(missing[:20]))

    lines = [
        '"""Field-specific program description clauses for University of Wisconsin-Madison.',
        "",
        "Each entry states something concrete about what UW-Madison's program in that field",
        "covers — never a credential/school classification stub. Sources: UW-Madison Academics",
        "(wisc.edu/academics/), college and department catalog pages, College of Agricultural",
        "and Life Sciences (cals.wisc.edu), College of Engineering (engr.wisc.edu), Wisconsin",
        "School of Business (business.wisc.edu), School of Computer, Data and Information",
        "Sciences (cdis.wisc.edu), School of Medicine and Public Health (med.wisc.edu),",
        "School of Education (education.wisc.edu), Nelson Institute (nelson.wisc.edu), and",
        "School of Veterinary Medicine (vetmed.wisc.edu).",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "FIELD_DESCRIPTIONS: dict[str, str] = {",
    ]
    for field in FIELDS:
        clause = clauses[field]
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
