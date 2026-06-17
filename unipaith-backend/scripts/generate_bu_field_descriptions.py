#!/usr/bin/env python3
"""Generate ``bu_field_descriptions.py`` from peer-university clauses + BU overrides."""

from __future__ import annotations

# ruff: noqa: E501
import ast
import re
from pathlib import Path

from unipaith.data.berkeley_field_descriptions import FIELD_DESCRIPTIONS as BERKELEY
from unipaith.data.columbia_field_descriptions import FIELD_DESCRIPTIONS as COLUMBIA
from unipaith.data.harvard_field_descriptions import FIELD_DESCRIPTIONS as HARVARD
from unipaith.data.jhu_field_descriptions import FIELD_DESCRIPTIONS as JHU
from unipaith.data.northwestern_field_descriptions import FIELD_DESCRIPTIONS as NORTHWESTERN
from unipaith.data.penn_field_descriptions import FIELD_DESCRIPTIONS as PENN
from unipaith.data.profile_catalog_utils import BARE_DEGREE_ABBREVIATIONS, disambiguate_program_name
from unipaith.data.rice_field_descriptions import FIELD_DESCRIPTIONS as RICE


def _clean_segment(seg: str) -> str:
    s = seg.replace("-", " ").title()
    for prefix in (
        "Ba In ", "Ba ", "Bs In ", "Bs ", "Ms In ", "Ms ", "Ma In ", "Ma ",
        "Phd In ", "Phd ", "Msd ", "Cags ", "Programs ",
    ):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s.strip()


def _field_from_url(url: str) -> str:
    m = re.search(r"/programs/(.+)", url.rstrip("/"))
    if not m:
        return ""
    parts = [p for p in m.group(1).split("/") if p and p != "programs"]
    deg_tokens = (
        "ba", "bs", "ms", "ma", "phd", "jd", "md", "mba", "dmd", "mph", "msw",
        "meng", "cags", "msd", "dscd", "llm", "edd", "dpt", "otd", "dnp", "dsc",
    )
    while parts and parts[-1].lower() in deg_tokens:
        parts.pop()
    if not parts:
        return ""
    return " — ".join(_clean_segment(p) for p in parts)


def _load_catalog() -> list[tuple]:
    src = (
        Path(__file__).resolve().parents[1]
        / "src/unipaith/data/bu_profile.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_CATALOG" and node.value is not None:
                return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_CATALOG":
                    return ast.literal_eval(node.value)
    raise RuntimeError("_CATALOG not found in bu_profile.py")


def _base_program_name(slug: str, legacy: str, dtype: str, url: str, overrides: dict, legacy_counts: dict) -> str:
    if slug in overrides:
        return overrides[slug]
    if legacy not in BARE_DEGREE_ABBREVIATIONS and legacy_counts.get(legacy, 0) <= 1:
        return legacy.replace("&amp;", "&")
    field = _field_from_url(url)
    if legacy == "MEng":
        return f"Master of Engineering in {field.split(' — ')[0]}"
    return disambiguate_program_name(field, dtype)


def _all_catalog_fields() -> set[str]:
    """Collect every URL-derived field key _bu_description may look up."""
    catalog = _load_catalog()
    fields: set[str] = set()
    for row in catalog:
        url = row[7]
        f = _field_from_url(url)
        if f:
            fields.add(f)
        # Standalone professional programs whose URL ends in degree token only
        legacy = row[2]
        if legacy in ("MD", "JD", "MBA", "DMD", "Juris Doctor", "Master of Business Administration"):
            fields.add(legacy if legacy not in ("MD", "JD", "MBA", "DMD") else {
                "MD": "Four Year Program",
                "JD": "Juris Doctor",
                "MBA": "Master of Business Administration",
                "DMD": "Doctor Of Dental Medicine",
            }[legacy])
    return fields


FIELDS: list[str] = []  # set in main()

# BU-specific clauses — verified against bu.edu/academics catalog pages.
BU_MANUAL: dict[str, str] = {
    "Four Year Program": (
        "BU's Chobanian & Avedisian School of Medicine four-year M.D. curriculum combines "
        "foundational sciences, clinical clerkships at Boston Medical Center, and "
        "longitudinal patient-care experiences on the Medical Campus."
    ),
    "Doctor Of Dental Medicine": (
        "The Goldman School of Dental Medicine D.M.D. program trains general dentists with "
        "clinical rotations in BU's patient-care clinics and community health partnerships "
        "across Boston."
    ),
    "Combined Md Mba": (
        "BU's combined M.D./M.B.A. pathway pairs Chobanian & Avedisian medical training "
        "with Questrom's health-sector management coursework for physician-leaders."
    ),
    "Combined Mdjd": (
        "The M.D./J.D. dual degree links BU School of Medicine clinical training with "
        "health-law and bioethics coursework at the School of Law."
    ),
    "Jdmba": (
        "Questrom's J.D./M.B.A. dual degree trains attorneys in finance, strategy, and "
        "corporate governance through integrated law and business curricula."
    ),
    "Jdmba Health": (
        "The J.D./M.B.A. health-sector pathway combines BU Law health-policy clinics with "
        "Questrom coursework in healthcare management and analytics."
    ),
    "Jdmph": (
        "BU's J.D./M.P.H. dual degree pairs School of Law training with the School of "
        "Public Health's epidemiology and health-policy core."
    ),
    "Mba Mph": (
        "Questrom's M.B.A./M.P.H. trains health-sector managers in analytics, operations, "
        "and population-health policy through cross-registration with SPH."
    ),
    "Md Phd Combined Degree": (
        "BU's M.D./Ph.D. program links Chobanian & Avedisian clinical training with "
        "Graduate Medical Sciences research labs in the Medical Campus research corridor."
    ),
    "Bamph Program": (
        "The B.A./M.P.H. accelerated pathway lets CAS undergraduates begin School of "
        "Public Health coursework toward an M.P.H. in five years."
    ),
    "September Program": (
        "CGS's September Program offers a two-year liberal-arts core on the Charles River "
        "Campus before students transfer into a BU bachelor's degree."
    ),
    "Undergrad": (
        "CGS's two-year liberal-arts curriculum provides interdisciplinary humanities, "
        "social-science, and natural-science foundations before transfer to a BU bachelor's."
    ),
    "Aerospace Studies": (
        "Air Force ROTC aerospace-studies coursework at BU covers leadership, military "
        "history, and commissioning preparation alongside any major."
    ),
    "Military Science": (
        "Army ROTC military-science coursework develops leadership, land-navigation, and "
        "officer commissioning skills for BU undergraduates in any school."
    ),
    "Naval Science": (
        "Naval ROTC coursework covers seamanship, naval history, and Marine Corps or Navy "
        "commissioning pathways for BU undergraduates."
    ),
    "Gastronomy": (
        "MET's M.L.A. in Gastronomy combines food history, policy, and experiential "
        "learning with Boston's restaurant and culinary industries."
    ),
    "Ms In Data Science Online": (
        "MET's online M.S. in Data Science covers statistical modeling, machine learning, "
        "and data visualization for working professionals."
    ),
    "Ms In Business Analytics": (
        "Questrom's M.S. in Business Analytics trains students in predictive modeling, "
        "prescriptive analytics, and data-driven decision making for industry."
    ),
    "Ms In Data Science": (
        "The Faculty of Computing & Data Sciences M.S. in Data Science integrates "
        "statistics, computing, and domain applications across BU schools."
    ),
    "Ms In Finance": (
        "Questrom's M.S. in Finance emphasizes asset pricing, corporate finance, and "
        "quantitative methods with Boston financial-services recruiting."
    ),
    "Ms In Management Studies": (
        "Questrom's M.S. in Management Studies offers specialized master's tracks for "
        "recent graduates building business fundamentals."
    ),
    "Msdt": (
        "Questrom's M.S. in Digital Technology integrates product management, analytics, "
        "and digital transformation for technology-sector careers."
    ),
    "Bachelor Of Science In Business Administration Bsba To Master Of Science In Business Analytics Msba Program": (
        "Questrom's B.S.B.A.-to-M.S.B.A. pathway lets undergraduates begin analytics "
        "coursework toward a master's in business analytics."
    ),
    "Bachelor Of Science In Hospitality Administration": (
        "SHA's B.S. in Hospitality Administration combines hotel operations, revenue "
        "management, and industry internships with Boston's tourism economy."
    ),
    "Bs In Hospitality Communication": (
        "SHA's hospitality-communication major blends event management, marketing, and "
        "guest-experience design for the service industries."
    ),
    "Product Design Manufacture — Product Design Manufacture": (
        "ENG's product-design and manufacture M.S. integrates design studios, prototyping, "
        "and manufacturing systems in the Engineering Product Innovation Center."
    ),
    "Product Design Manufacture — Msmba": (
        "The product-design M.S./M.B.A. dual degree pairs ENG design studios with Questrom "
        "management coursework for product-development leaders."
    ),
    "Dual Degree In Theology And Social Work": (
        "BU's dual M.Div./M.S.W. links School of Theology ministry training with clinical "
        "social-work field placements through SSW."
    ),
    "Dual Degree Programs In Social Work And Education": (
        "Wheelock and SSW dual degrees combine educator licensure with clinical or macro "
        "social-work training for school and community settings."
    ),
    "Theological Studies Phd": (
        "STH's Ph.D. in theological studies prepares scholars in biblical, historical, and "
        "practical theology with Boston's ecumenical research community."
    ),
    "Two Year Master Of Laws Llm In American Law": (
        "BU Law's two-year LL.M. in American Law introduces foreign lawyers to U.S. "
        "common-law doctrine, legal writing, and bar-exam preparation."
    ),
    "Two Year Master Of Laws Llm In Banking Financial Law": (
        "BU Law's banking and financial-law LL.M. covers securities regulation, M&A, and "
        "financial-institution supervision in Boston's finance corridor."
    ),
    "Two Year Master Of Laws Llm In Intellectual Property Information Law": (
        "BU Law's IP LL.M. examines patent, copyright, and information-law issues with "
        "technology-transfer and life-sciences industry context."
    ),
    "Two Year Master Of Laws Llm In Tax Law": (
        "BU Law's tax LL.M. covers federal income, partnership, and international tax with "
        "the Graduate Tax Program's practitioner faculty."
    ),
    "Accelerated Llm In Banking Financial Law": (
        "BU Law's accelerated banking and financial-law LL.M. compresses securities and "
        "financial-regulation coursework for experienced attorneys."
    ),
    "Accelerated Llm In Taxation": (
        "BU Law's accelerated tax LL.M. delivers intensive federal and international tax "
        "training for practicing lawyers."
    ),
    "Graduate Program In Banking Financial Law": (
        "BU Law's Graduate Program in Banking & Financial Law offers LL.M. and certificate "
        "pathways in securities, banking regulation, and financial compliance."
    ),
    "Graduate Tax Program": (
        "BU Law's Graduate Tax Program is a nationally recognized tax-law curriculum covering "
        "corporate, partnership, and estate taxation."
    ),
    "American Law": (
        "BU Law's LL.M. in American Law introduces foreign-trained lawyers to U.S. legal "
        "method, constitutional structure, and professional practice."
    ),
    "Intellectual Property Law": (
        "BU Law's IP law programs cover patent prosecution, copyright, and technology "
        "licensing with Boston's biotech and software clusters."
    ),
    "Jd Llm In International Commercial And Investment Arbitration At Paris2": (
        "BU Law's J.D./LL.M. with Université Paris 2 trains students in cross-border "
        "commercial arbitration and investment treaty disputes."
    ),
    "Jdllm In European Law At Paris Ii": (
        "BU Law's J.D./LL.M. European Law pathway with Paris II covers EU institutions, "
        "competition law, and comparative public law."
    ),
    "Jdllm In Finance": (
        "BU Law's J.D./LL.M. in Finance combines corporate law training with financial "
        "regulation and capital-markets coursework."
    ),
    "Jdllm In International And European Business Law At Icade": (
        "BU Law's J.D./LL.M. with ICADE (Madrid) examines international business transactions "
        "and European commercial law."
    ),
    "Jdma English": (
        "BU Law's J.D./M.A. in English pairs legal training with literary and rhetorical "
        "study in CAS for law-and-humanities careers."
    ),
    "Jdma History": (
        "BU Law's J.D./M.A. in History combines legal doctrine with historical research "
        "methods for public-history and policy roles."
    ),
    "Jdma Ir": (
        "BU Law's J.D./M.A. in International Relations links Pardee global-affairs "
        "coursework with international and comparative law."
    ),
    "Jdma Philosophy": (
        "BU Law's J.D./M.A. in Philosophy integrates legal reasoning with ethics and "
        "political-philosophy seminars in CAS."
    ),
    "Jdma Preservation": (
        "BU Law's J.D./M.A. in Preservation Studies combines historic-preservation policy "
        "with land-use and cultural-heritage law."
    ),
    "Marpl": (
        "GRS's M.A.R.P.L. in literary translation trains translators in workshop critique, "
        "comparative literature, and publishing practice."
    ),
    "Pibs": (
        "GMS's Program in Biomedical Sciences (PIBS) is a gateway Ph.D. curriculum spanning "
        "molecular biology, neuroscience, and immunology on the Medical Campus."
    ),
    "Virology Immunology Microbiology Program": (
        "GMS virology, immunology, and microbiology Ph.D. training occurs alongside NEIDL "
        "and infectious-disease research on the Medical Campus."
    ),
    "Forensic Anthropology": (
        "GRS forensic anthropology combines skeletal analysis, taphonomy, and medicolegal "
        "case work with BU's archaeological and biological anthropology faculty."
    ),
    "Medical Anthropology And Cross Cultural Practice": (
        "GRS medical anthropology examines illness experience, global health, and ethnographic "
        "methods with Boston hospital and community field sites."
    ),
    "Holocaust Genocide Human Rights Studies": (
        "GRS Holocaust, genocide, and human-rights studies integrates historical research, "
        "memorial practice, and policy analysis through the Elie Wiesel Center."
    ),
    "Editorial Studies": (
        "GRS editorial studies trains scholars in textual criticism, scholarly editing, and "
        "digital humanities with rare-book resources in Mugar Library."
    ),
    "Arts Administration": (
        "MET's M.S. in Arts Administration covers nonprofit management, audience development, "
        "and cultural policy with Boston's museum and performing-arts partners."
    ),
    "American New England Studies": (
        "GRS American and New England studies examines regional history, material culture, "
        "and archival research across Boston-area collections."
    ),
    "African American Black Diaspora Studies": (
        "CAS African American and Black diaspora studies spans literature, history, and "
        "cultural politics with Boston's Black intellectual traditions."
    ),
    "Deaf Studies": (
        "Wheelock deaf studies combines American Sign Language, education policy, and "
        "disability-rights advocacy for educators and community leaders."
    ),
    "Applied Human Development — Bs Edm Applied Human Development": (
        "Wheelock's B.S./Ed.M. in applied human development pairs undergraduate child "
        "development with graduate counseling coursework."
    ),
    "Applied Human Development — Phd Counseling Psychology Applied Human Development": (
        "Wheelock's Ph.D. in counseling psychology and applied human development trains "
        "clinician-researchers in evidence-based interventions."
    ),
    "Policy Planning Administration — Bs Ma Educational Policy Studies": (
        "Wheelock's B.S./M.A. in educational policy studies accelerates undergraduates into "
        "graduate policy analysis and school leadership coursework."
    ),
    "Policy Planning Administration — Ma In Educational Policy Studies": (
        "Wheelock's M.A. in educational policy studies examines K-12 governance, equity, "
        "and data-driven school improvement."
    ),
    "Early Childhood Education — Ma In Leadership Policy Advocacy For Early Childhood Well Being": (
        "Wheelock's early-childhood leadership M.A. trains advocates in policy, program "
        "administration, and family-centered practice."
    ),
    "Bilingual Education — Bs Edm Tesol Applied Linguistics": (
        "Wheelock's B.S./Ed.M. TESOL pathway prepares ESL educators with applied "
        "linguistics and classroom practica in Boston schools."
    ),
    "Bilingual Education — Bs Ms Tesol Multilingual Learner Education": (
        "Wheelock's B.S./M.S. in TESOL and multilingual-learner education trains teachers "
        "for dual-language and ESL classrooms."
    ),
    "Health Communication And Promotion": (
        "SPH health communication and promotion examines message design, behavior change, "
        "and community health campaigns with Boston public-health partners."
    ),
    "Healthcare Emergency Management": (
        "MET's M.S. in healthcare emergency management trains leaders in disaster "
        "preparedness, hospital operations, and public-health response."
    ),
    "Mph In Health Equity": (
        "SPH's M.P.H. in health equity examines structural determinants of health, "
        "community engagement, and policy advocacy."
    ),
    "Mph — Global Health 2": (
        "SPH's global-health M.P.H. covers epidemiology, health systems, and field "
        "work with international NGO and ministry partners."
    ),
    "Medicine And Public Health": (
        "BU's M.D./M.P.H. pathway integrates Chobanian & Avedisian clinical training with "
        "SPH population-health coursework."
    ),
    "Medical Sciences And Public Health": (
        "GMS biomedical-sciences coursework paired with SPH public-health foundations for "
        "research-oriented health careers."
    ),
    "Public Health — Bs Mph": (
        "Sargent's B.S.-to-M.P.H. pathway lets health-sciences undergraduates begin SPH "
        "coursework toward an M.P.H."
    ),
    "Social Work And Public Health": (
        "BU's M.S.W./M.P.H. dual degree combines SSW clinical training with SPH "
        "population-health policy coursework."
    ),
    "Macro Social Work Practice": (
        "SSW macro practice trains community organizers, policy advocates, and nonprofit "
        "leaders with Boston-area field placements."
    ),
    "Clinical Social Work Practice": (
        "SSW clinical practice emphasizes evidence-based psychotherapy, trauma-informed "
        "care, and licensure preparation."
    ),
    "Mental Health Counseling Behavioral Medicine Program": (
        "Wheelock's mental-health counseling program trains licensed counselors in "
        "CBT, behavioral medicine, and integrated care settings."
    ),
    "Ms In Genetic Counseling Master Of Public Health Ms Mph": (
        "BU's genetic-counseling and M.P.H. dual degree pairs GMS clinical genetics "
        "training with SPH population-health coursework."
    ),
    "Ms In Child Life Family Centered Care": (
        "Wheelock's child-life M.S. prepares certified child-life specialists for "
        "pediatric hospital and family-support settings."
    ),
    "Ms In Biomedical Research Technologies": (
        "GMS biomedical research technologies covers core lab methods, imaging, and "
        " translational research support on the Medical Campus."
    ),
    "Biomedical Forensic Sciences": (
        "GMS forensic-sciences coursework covers DNA analysis, toxicology, and crime-scene "
        "investigation with Boston-area lab practica."
    ),
    "Clinical Investigation": (
        "GMS clinical investigation trains physician-scientists in trial design, biostatistics, "
        "and translational research methods."
    ),
    "Anatomy Neurobiology — Mdphd": (
        "GMS anatomy and neurobiology M.D./Ph.D. research spans neural development, "
        "neurodegeneration, and systems neuroscience."
    ),
    "Mdphd In Bioinformatics": (
        "BU's M.D./Ph.D. in bioinformatics integrates clinical training with computational "
        "genomics and biomedical data science."
    ),
    "Phd In Bioinformatics": (
        "CDS and GMS bioinformatics Ph.D. research covers computational genomics, machine "
        "learning for health data, and systems biology."
    ),
    "Ms In Bioinformatics": (
        "BU's M.S. in Bioinformatics combines statistics, programming, and molecular biology "
        "for genomics and precision-medicine careers."
    ),
    "Bs Data Science Ms Bioinformatics": (
        "CDS's B.S./M.S. bioinformatics pathway accelerates undergraduates into graduate "
        "computational biology coursework."
    ),
    "Phd In Business Economics": (
        "Questrom's Ph.D. in business economics trains scholars in industrial organization, "
        "econometrics, and applied microeconomics."
    ),
    "Phd In Computing Data Sciences": (
        "CDS's Ph.D. in computing and data sciences spans AI, systems, and interdisciplinary "
        "data-driven research across BU."
    ),
    "Phd In Management": (
        "Questrom's Ph.D. in management prepares scholars in strategy, organizational behavior, "
        "and operations research."
    ),
    "Phd In Social Work": (
        "SSW's Ph.D. trains social-work researchers in intervention science, policy analysis, "
        "and community-based participatory methods."
    ),
    "School Of Music — Music": (
        "CFA School of Music performance and composition programs combine conservatory "
        "studio training with Boston's professional orchestra and chamber scene."
    ),
    "School Of Music — Music Education": (
        "CFA music education prepares K-12 licensed teachers with pedagogy seminars and "
        "student-teaching placements in Greater Boston schools."
    ),
    "School Of Music — Music Education — Bm Mm": (
        "CFA's B.M./M.M. music-education pathway accelerates undergraduates into graduate "
        "pedagogy and licensure coursework."
    ),
    "School Of Music — Music Theory": (
        "CFA music theory graduate study examines analysis, Schenkerian and set-theory "
        "methods, and contemporary composition techniques."
    ),
    "School Of Music — Musicology": (
        "CFA musicology coursework spans historical research, ethnomusicology, and "
        "archival work with Boston-area collections."
    ),
    "School Of Theatre — Acting": (
        "CFA acting training combines Stanislavski-based studio work, voice and movement, "
        "and production seasons in the BU Theatre."
    ),
    "School Of Theatre — Theatre Arts — Bfa Design Production": (
        "CFA design and production B.F.A. students build sets, costumes, and lighting in "
        "collaborative production seasons."
    ),
    "School Of Theatre — Theatre Arts — Bfa Performance": (
        "CFA performance B.F.A. training emphasizes acting, musical theatre, and stage "
        "craft with mainstage production experience."
    ),
    "School Of Visual Arts — Ba In Art": (
        "CFA studio art B.A. coursework spans drawing, painting, printmaking, and new "
        "media with Boston gallery and museum access."
    ),
    "School Of Visual Arts — Bfa Ma": (
        "CFA's B.F.A./M.A. pathway accelerates studio-art undergraduates into graduate "
        "critique and exhibition practice."
    ),
    "School Of Visual Arts — Museum Education": (
        "CFA museum education trains educators in object-based learning, accessibility, and "
        "public programming with Boston museum partners."
    ),
    "Film Television — Film Televisionbs": (
        "COM film and television production combines cinematography, editing, and screenwriting "
        "with Boston's location-production industry."
    ),
    "Television": (
        "COM television production covers studio operations, field production, and broadcast "
        "writing with industry-standard facilities."
    ),
    "Media Science — Bs In Media Science": (
        "COM media science examines audience analytics, media effects research, and "
        "experimental methods in persuasion science."
    ),
    "Media Science — Ms In Media Science": (
        "COM's M.S. in Media Science trains researchers in survey design, psychophysiology, "
        "and digital-media analytics."
    ),
    "Emerging Media Studies": (
        "COM emerging media studies examines social platforms, digital culture, and "
        "computational communication research methods."
    ),
    "Advertising — Advertising Bs": (
        "COM advertising coursework covers creative strategy, media planning, and "
        "account management with agency internship pipelines."
    ),
    "Advertising — Advertising Ms": (
        "COM's M.S. in advertising integrates consumer research, brand strategy, and "
        "digital campaign analytics."
    ),
    "Public Relations — Bs In Public Relations": (
        "COM public relations training covers media relations, crisis communication, and "
        "corporate social responsibility campaigns."
    ),
    "Public Relations — Ms In Public Relations": (
        "COM's M.S. in public relations emphasizes strategic communication, digital "
        "storytelling, and agency management."
    ),
    "Health Communication": (
        "COM health communication examines message design, health literacy, and "
        "campaign evaluation with SPH and hospital partners."
    ),
    "Cinema Media Studies — Ba In Cinema Media Studies": (
        "COM cinema and media studies combines film history, theory, and cultural analysis "
        "with archival screening programs."
    ),
    "Occupational Therapy — Otd Phd": (
        "Sargent's O.T.D./Ph.D. pathway trains clinician-scientists in rehabilitation "
        "science and occupational therapy research."
    ),
    "Physical Therapy — Bs Dpt": (
        "Sargent's B.S./D.P.T. pathway accelerates undergraduates into doctoral physical "
        "therapy clinical training."
    ),
    "Physical Therapy — Dpt Phd": (
        "Sargent's D.P.T./Ph.D. trains rehabilitation scientists in movement analysis and "
        "clinical outcomes research."
    ),
    "Speech Language Hearing Sciences — Bs Ms": (
        "Sargent's B.S./M.S. speech-language pathology pathway combines hearing science "
        "with clinical practica toward ASHA certification."
    ),
    "Speech Language Hearing Sciences — Ms Phd": (
        "Sargent's M.S./Ph.D. pathway trains speech-language scientists in aphasia, "
        "motor speech disorders, and audiology research."
    ),
    "Bs In Behavior And Health": (
        "Sargent's behavior and health B.S. examines health psychology, exercise science, "
        "and wellness program design."
    ),
    "Human Physiology": (
        "Sargent human physiology coursework covers exercise physiology, biomechanics, and "
        "clinical measurement for health-science careers."
    ),
    "Health Science": (
        "Sargent health sciences integrates anatomy, public health, and pre-professional "
        "preparation for allied-health graduate programs."
    ),
    "Rehabilitation Sciences": (
        "Sargent rehabilitation-sciences Ph.D. research spans motor control, assistive "
        "technology, and clinical outcomes in PT and OT."
    ),
    "Physician Assistant": (
        "Sargent's M.S. physician assistant program combines didactic medicine with "
        "clinical rotations across Boston hospitals."
    ),
    "Genetic Counseling": (
        "GMS genetic counseling trains students in risk assessment, patient communication, "
        "and laboratory genomics for board certification."
    ),
    "Nutrition Dietetics": (
        "Sargent nutrition and dietetics coursework covers clinical dietetics, community "
        "nutrition, and ACEND-accredited supervised practice."
    ),
    "Nutrition Metabolism": (
        "GMS nutrition and metabolism research examines biochemistry, obesity science, and "
        "metabolic disease on the Medical Campus."
    ),
    "Bioimaging": (
        "ENG bioimaging coursework covers MRI, optical microscopy, and image reconstruction "
        "with the Photonics Center and ENG imaging labs."
    ),
    "Systems Engineering": (
        "ENG systems engineering integrates optimization, human factors, and complex "
        "systems design for defense and industry applications."
    ),
    "Mathematical Finance": (
        "Questrom mathematical finance combines stochastic calculus, derivatives pricing, "
        "and computational finance for Wall Street and Boston quant roles."
    ),
    "Actuarial Science": (
        "Questrom actuarial science covers probability, risk modeling, and SOA exam "
        "preparation with insurance-industry recruiting."
    ),
    "Administrative Sciences": (
        "MET administrative sciences offers part-time management, project leadership, and "
        "healthcare administration degrees for working professionals."
    ),
    "Criminal Justice — Mcj": (
        "MET's M.C.J. in criminal justice examines policing, corrections policy, and "
        "criminological research for practitioners."
    ),
    "Urban Affairs": (
        "MET urban affairs coursework covers housing policy, community development, and "
        "city governance with Boston-area field projects."
    ),
    "Interdisciplinary Studies": (
        "MET interdisciplinary studies lets part-time students design cross-field "
        "curricula combining liberal arts and professional coursework."
    ),
    "Developmental Studies — Cags Lit Language": (
        "Wheelock's C.A.G.S. in literacy and language supports licensed teachers pursuing "
        "reading-specialist and ESL endorsements."
    ),
    "Ba In Middle East North Africa Studies": (
        "CAS Middle East and North Africa studies combines Arabic language, political "
        "history, and Pardee-affiliated regional scholarship."
    ),
    "Ba In Science Education": (
        "Wheelock science education prepares licensed STEM teachers with content "
        "coursework in CAS and pedagogy in Wheelock."
    ),
    "Bs In Data Science": (
        "CDS's undergraduate data-science major integrates statistics, computing, and "
        "domain applications in the Center for Computing & Data Sciences."
    ),
    "Bs In Education Human Development": (
        "Wheelock's B.S. in education and human development combines child development "
        "science with educator-preparation coursework."
    ),
    "Bs Mla": (
        "MET's B.S./M.L.A. pathway accelerates undergraduates into liberal-arts graduate "
        "coursework in humanities or social sciences."
    ),
    "Bs Ms": (
        "BU's B.S./M.S. accelerated pathways let undergraduates begin graduate coursework "
        "toward a master's in their field."
    ),
    "Dental Public Health": (
        "SDM dental public health specialty training covers epidemiology, health policy, "
        "and community oral-health programs."
    ),
    "Endodontics": (
        "SDM endodontics specialty programs train dentists in root-canal therapy, "
        "microsurgery, and pulp biology."
    ),
    "Operative Dentistry": (
        "SDM operative dentistry specialty training covers restorative techniques, "
        "adhesive dentistry, and cariology research."
    ),
    "Oral And Maxillofacial Surgery": (
        "SDM oral and maxillofacial surgery residency integrates hospital surgery "
        "rotations with craniofacial trauma training."
    ),
    "Oral Biology": (
        "SDM oral biology research examines craniofacial development, biomaterials, and "
        "salivary diagnostics in GMS-affiliated labs."
    ),
    "Oral Health Sciences Ms": (
        "SDM's M.S. in oral health sciences covers research methods in craniofacial "
        "biology and dental biomaterials."
    ),
    "Orthodontics Dentofacial Orthopedics": (
        "SDM orthodontics programs train specialists in tooth movement, craniofacial "
        "growth, and aligner therapy."
    ),
    "Orthodontics Dentofacial Orthopedics — Cags Msd": (
        "SDM orthodontics C.A.G.S./M.S.D. pathways provide advanced clinical and research "
        "training for practicing orthodontists."
    ),
    "Periodontology": (
        "SDM periodontology specialty training covers implant surgery, gum disease "
        "management, and periodontal research."
    ),
    "Prosthodontics": (
        "SDM prosthodontics trains specialists in complex restorations, maxillofacial "
        "prosthetics, and implant-supported dentures."
    ),
    "Prosthodontics — Cags Dscd": (
        "SDM prosthodontics D.Sc.D. research covers digital dentistry, biomaterials, and "
        "full-mouth rehabilitation science."
    ),
    "Prosthodontics — Cags Msd": (
        "SDM prosthodontics M.S.D. programs combine advanced clinical prosthodontics with "
        "laboratory research."
    ),
    "Dermatology": (
        "SDM dermatology research pathways examine oral mucosal disease and "
        "craniofacial dermatologic conditions."
    ),
    "Dental Biomaterials — Dscd Cags": (
        "SDM dental biomaterials research covers adhesive systems, ceramic restorations, "
        "and tissue-engineering scaffolds."
    ),
    "Dental Biomaterials — Msd Cags": (
        "SDM biomaterials M.S.D. and C.A.G.S. programs train dentists in research methods "
        "for restorative and implant materials."
    ),
    "Dscd Dental Biomaterials": (
        "SDM's D.Sc.D. in dental biomaterials advances research in adhesive dentistry, "
        "digital workflows, and craniofacial materials."
    ),
    "Pediatric Dentistry": (
        "SDM pediatric dentistry specialty training covers child behavior management, "
        "special-needs dentistry, and hospital sedation."
    ),
    "Health Services Research": (
        "SPH health services research examines healthcare delivery, quality measurement, "
        "and policy evaluation with Boston hospital data partners."
    ),
    "Environmental Health": (
        "SPH environmental health covers exposure science, occupational health, and "
        "climate-related disease with NEIDL-adjacent labs."
    ),
    "Epidemiology": (
        "SPH epidemiology training spans biostatistics, infectious-disease modeling, and "
        "cohort study design — SPH ranks among top U.S. public-health schools."
    ),
    "World Languages Literatures — Ba German": (
        "CAS German language and literature coursework combines Berlin study-abroad, "
        "linguistics, and literary analysis."
    ),
    "World Languages Literatures — Ba In Comparative Literature Mfa In Literary Translation": (
        "CAS/GRS comparative literature and literary translation integrates workshop "
        "critique with multilingual textual study."
    ),
    "Romance Studies — Ba French": (
        "CAS French studies combines Paris and Grenoble study-abroad with literature, "
        "linguistics, and francophone culture."
    ),
    "Romance Studies — Ma French": (
        "GRS French graduate coursework examines literary theory, linguistics, and "
        "francophone studies with research in Mugar Library collections."
    ),
    "Romance Studies — Phd French": (
        "GRS French Ph.D. research spans medieval through contemporary literature and "
        "applied linguistics."
    ),
    "Romance Studies — Phd Hispanic": (
        "GRS Hispanic studies Ph.D. research covers Latin American, Peninsular, and "
        "U.S. Latina/o literary and cultural production."
    ),
    "Linguistics — Ba Linguistics": (
        "CAS linguistics examines phonology, syntax, and psycholinguistics with experimental "
        "and fieldwork methods."
    ),
    "Linguistics — Bama In Linguistics": (
        "CAS/GRS B.A./M.A. linguistics accelerates undergraduates into graduate syntax, "
        "semantics, and fieldwork coursework."
    ),
    "Linguistics — Ma In Linguistics": (
        "GRS linguistics M.A. covers formal grammar, language acquisition, and "
        "computational linguistics."
    ),
    "Linguistics — Phd In Linguistics": (
        "GRS linguistics Ph.D. research spans theoretical syntax, sociolinguistics, and "
        "language documentation."
    ),
    "Classical Studies — Ba Latin": (
        "CAS Latin language and literature coursework combines philology, Roman history, "
        "and advanced translation seminars."
    ),
    "Classical Studies — Ba Ma": (
        "CAS/GRS classical studies B.A./M.A. pathway accelerates undergraduates into "
        "graduate Greek and Latin philology."
    ),
    "Classical Studies — Ma Phd Phil": (
        "GRS classical philology graduate research covers Greek and Latin literature, "
        "papyrology, and ancient history."
    ),
    "Archaeology — Ba Ma": (
        "CAS/GRS archaeology B.A./M.A. combines field schools, material analysis, and "
        "Old World and New World excavation projects."
    ),
    "Astronomy — Ba Ma Astrophysics": (
        "CAS/GRS astronomy and astrophysics coursework covers observational techniques, "
        "stellar structure, and cosmology with the Perkins telescope."
    ),
    "Chemistry — Ba Ma": (
        "CAS/GRS chemistry B.A./M.A. pathway accelerates undergraduates into graduate "
        "synthesis, spectroscopy, and chemical biology."
    ),
    "Economics — Ba Ma": (
        "CAS/GRS economics B.A./M.A. pathway lets undergraduates begin graduate "
        "microeconomics, econometrics, and field courses."
    ),
    "Economics — Ma Phd": (
        "GRS economics graduate research spans macroeconomics, labor, and development with "
        "Institute for Economic Development affiliations."
    ),
    "English — Bama In English": (
        "CAS/GRS English B.A./M.A. pathway accelerates undergraduates into graduate "
        "literary theory, creative writing, and rhetoric."
    ),
    "History Art Architecture": (
        "GRS history of art and architecture examines visual culture, preservation, and "
        "museum studies with Boston-area collections."
    ),
    "International Relations — Ba In International Relationsma In International Affairs": (
        "Pardee's B.A./M.A. international affairs pathway accelerates undergraduates into "
        "graduate security, development, and diplomacy coursework."
    ),
    "International Relations — International Relations Ma Mba": (
        "Pardee/Questrom M.A./M.B.A. dual degree trains global business leaders in "
        "international policy and management."
    ),
    "Latin American Studies Ma": (
        "GRS Latin American studies graduate coursework examines politics, culture, and "
        "development across the Americas."
    ),
    "Mathematics Statistics — Ba Ma": (
        "CAS/GRS mathematics B.A./M.A. pathway accelerates undergraduates into graduate "
        "analysis, algebra, and probability."
    ),
    "Mathematics Statistics — Ma Statistics": (
        "GRS statistics M.A. covers probability, regression, and applied methods for "
        "research and industry roles."
    ),
    "Mathematics Statistics — Phd Mathematics": (
        "GRS mathematics Ph.D. research spans pure and applied mathematics with ties to "
        "CDS and ENG computational groups."
    ),
    "Mathematics Statistics — Phd Statistics": (
        "GRS statistics Ph.D. research covers Bayesian methods, high-dimensional inference, "
        "and biostatistics collaborations with SPH."
    ),
    "Physics — Ba Ma": (
        "CAS/GRS physics B.A./M.A. pathway accelerates undergraduates into graduate "
        "quantum mechanics, condensed matter, and astrophysics."
    ),
    "Biochemistry Molecular Biology — Ba Ma": (
        "CAS/GRS biochemistry B.A./M.A. pathway accelerates undergraduates into graduate "
        "protein chemistry and molecular biology research."
    ),
    "Biochemistry — Mdphd": (
        "GMS biochemistry M.D./Ph.D. research spans enzymology, structural biology, and "
        "drug discovery on the Medical Campus."
    ),
    "Computer Science — Ba Ms": (
        "CAS/GRS computer science B.A./M.S. pathway accelerates undergraduates into "
        "graduate algorithms, systems, and AI coursework."
    ),
    "Computer Science — Bs Accelerated": (
        "CAS accelerated B.S. computer science compresses the major for transfer and "
        "degree-completion students."
    ),
    "Anthropology — Biological Anthropology": (
        "CAS biological anthropology examines human evolution, primatology, and skeletal "
        "biology with lab and field methods."
    ),
    "Sociology — Sociology Social Work": (
        "CAS/SSW sociology and social work dual degree combines social theory with "
        "clinical social-work training."
    ),
    "Earth Environment — Ba Environmental Analysis Policy": (
        "CAS earth and environment B.A. in environmental analysis and policy examines "
        "climate science, GIS, and sustainability policy."
    ),
    "Earth Environment — Bama Energy Environment": (
        "CAS/GRS energy and environment B.A./M.A. combines earth science with renewable "
        "energy and environmental economics."
    ),
    "Earth Environment — Geoarchaeology Ma": (
        "GRS geoarchaeology M.A. integrates geological methods with archaeological "
        "fieldwork and landscape reconstruction."
    ),
    "Religious Studies — Ma In Religious Studies": (
        "GRS religious studies M.A. covers comparative religion, theology, and "
        "religion-and-culture research methods."
    ),
    "Science Education": (
        "Wheelock science education prepares licensed biology, chemistry, and physics "
        "teachers with CAS content partnerships."
    ),
    "Social Studies Education": (
        "Wheelock social studies education trains history and civics teachers with "
        "Boston Public Schools practicum placements."
    ),
    "Modern Foreign Language Education": (
        "Wheelock modern language education prepares licensed Spanish, French, and Mandarin "
        "teachers with CAS language departments."
    ),
    "Literacy Education": (
        "Wheelock literacy education covers reading specialist licensure, dyslexia "
        "intervention, and K-12 literacy coaching."
    ),
    "Special Education": (
        "Wheelock special education prepares teachers for inclusive classrooms, autism "
        "support, and disability-law compliance."
    ),
    "Elementary Education": (
        "Wheelock elementary education combines child development science with "
        "classroom management and licensure practica."
    ),
    "Early Childhood Education": (
        "Wheelock early childhood education trains pre-K through grade-2 teachers with "
        "play-based pedagogy and family engagement."
    ),
    "Curriculum Teaching": (
        "Wheelock curriculum and teaching graduate programs examine instructional design, "
        "assessment, and school improvement."
    ),
    "Bilingual Education": (
        "Wheelock bilingual education prepares dual-language and ESL teachers for "
        "multilingual Boston classrooms."
    ),
    "Policy Planning Administration": (
        "Wheelock educational policy and planning examines school finance, leadership, "
        "and equity in urban districts."
    ),
    "Applied Human Development": (
        "Wheelock applied human development spans child psychology, family systems, and "
        "community-based youth programs."
    ),
    "Marine Science": (
        "CAS marine science at BU's Marine Program (Woods Hole partnership) covers "
        "oceanography, marine biology, and coastal fieldwork."
    ),
    "African American Studies": (
        "CAS African American studies spans literature, history, sociology, and "
        "cultural politics with Boston's Black intellectual and community traditions."
    ),
    "Anatomy Neurobiology": (
        "GMS anatomy and neurobiology coursework covers gross anatomy, neuroanatomy, "
        "and systems neuroscience on the Medical Campus."
    ),
    "Behavior And Health": (
        "Sargent behavior and health examines health psychology, exercise science, "
        "and wellness program design for allied-health careers."
    ),
    "Biomedical Research Technologies": (
        "GMS biomedical research technologies covers core lab methods, imaging, and "
        "translational research support on the Medical Campus."
    ),
    "Biostatistics": (
        "SPH and GRS biostatistics training covers regression, survival analysis, and "
        "clinical trial design with Medical Campus data collaborations."
    ),
    "Business Economics": (
        "Questrom business economics Ph.D. research spans industrial organization, "
        "econometrics, and applied microeconomics."
    ),
    "Child Life Family Centered Care": (
        "Wheelock's child-life M.S. prepares certified child-life specialists for "
        "pediatric hospital and family-support settings."
    ),
    "Cinema Media Studies — Cinema Media Studies": (
        "COM cinema and media studies combines film history, theory, and cultural analysis "
        "with archival screening programs."
    ),
    "Computing Data Sciences": (
        "CDS doctoral research spans responsible AI, computational social science, and "
        "large-scale data systems in the Center for Computing & Data Sciences."
    ),
    "Criminal Justice": (
        "MET criminal justice coursework examines policing, corrections policy, and "
        "criminological research for practitioners."
    ),
    "Data Science Ms Bioinformatics": (
        "CDS's B.S./M.S. bioinformatics pathway accelerates undergraduates into graduate "
        "computational biology coursework."
    ),
    "Data Science Online": (
        "MET's online M.S. in Data Science covers statistical modeling, machine learning, "
        "and data visualization for working professionals."
    ),
    "Dental Biomaterials — Cags": (
        "SDM biomaterials C.A.G.S. programs train dentists in research methods for "
        "restorative and implant materials."
    ),
    "Developmental Studies — Lit Language": (
        "Wheelock's C.A.G.S. in literacy and language supports licensed teachers pursuing "
        "reading-specialist and ESL endorsements."
    ),
    "Earth Environment — Environmental Analysis Policy": (
        "CAS earth and environment B.A. in environmental analysis and policy examines "
        "climate science, GIS, and sustainability policy."
    ),
    "Education Human Development": (
        "Wheelock's B.S. in education and human development combines child development "
        "science with educator-preparation coursework."
    ),
    "English Education": (
        "Wheelock English education prepares licensed secondary English teachers with "
        "CAS literature coursework and classroom practica."
    ),
    "Genetic Counseling Master Of Public Health Ms Mph": (
        "BU's genetic-counseling and M.P.H. dual degree pairs GMS clinical genetics "
        "training with SPH population-health coursework."
    ),
    "Genetics Genomics": (
        "GMS genetics and genomics research covers gene regulation, sequencing technologies, "
        "and precision medicine on the Medical Campus."
    ),
    "Hospitality Communication": (
        "SHA hospitality communication blends event management, marketing, and "
        "guest-experience design for the service industries."
    ),
    "Latin American Studies": (
        "CAS Latin American studies combines language training, politics, and cultural "
        "study with Pardee-affiliated regional scholarship."
    ),
    "MSW Online": (
        "SSW's online M.S.W. delivers clinical and macro social-work training with "
        "remote field placements for working professionals."
    ),
    "Management": (
        "Questrom management coursework covers strategy, organizational behavior, and "
        "operations for business leadership roles."
    ),
    "Master's in Communication": (
        "COM graduate communication programs examine media effects, strategic messaging, "
        "and research methods in persuasion science."
    ),
    "Master's in Hospitality Administration": (
        "SHA's M.S. in Hospitality Administration covers revenue management, real-estate "
        "finance, and global tourism with industry internships."
    ),
    "Mathematics Education": (
        "Wheelock mathematics education prepares licensed secondary math teachers with "
        "CAS content coursework and pedagogy seminars."
    ),
    "Mathematics Statistics": (
        "CAS mathematics and statistics coursework spans calculus, linear algebra, "
        "probability, and proof-based analysis."
    ),
    "Mathematics Statistics — Ma": (
        "GRS mathematics M.A. covers real and complex analysis, algebra, and applied "
        "probability for research and industry roles."
    ),
    "Mathematics Statistics — Mathematics": (
        "GRS mathematics graduate coursework spans pure and applied analysis, algebra, "
        "and geometry with CDS computational collaborations."
    ),
    "Mathematics Statistics — Statistics": (
        "GRS statistics graduate training covers probability, inference, and applied "
        "methods for research and data-science roles."
    ),
    "Media Science — Media Science": (
        "COM media science examines audience analytics, media effects research, and "
        "experimental methods in persuasion science."
    ),
    "Middle East North Africa Studies": (
        "CAS Middle East and North Africa studies combines Arabic language, political "
        "history, and Pardee-affiliated regional scholarship."
    ),
    "Mla": (
        "MET's M.L.A. programs offer part-time graduate study in liberal arts, "
        "administrative sciences, and professional fields."
    ),
    "Molecular Medicine": (
        "GMS molecular medicine research spans translational genomics, immunotherapy, "
        "and clinical trial science on the Medical Campus."
    ),
    "Ms": (
        "BU master's programs deliver advanced coursework, research methods, and "
        "professional preparation across BU's graduate schools."
    ),
    "Pathology Laboratory Medicine": (
        "GMS pathology and laboratory medicine research covers diagnostic pathology, "
        "transfusion medicine, and clinical laboratory science."
    ),
    "Physical Therapy — Dpt": (
        "Sargent's Doctor of Physical Therapy program combines movement analysis, "
        "clinical practica, and rehabilitation science."
    ),
    "Romance Studies — French": (
        "CAS and GRS French studies combine language immersion, literary analysis, "
        "and francophone cultural research."
    ),
    "Romance Studies — Hispanic": (
        "CAS and GRS Hispanic studies span Peninsular, Latin American, and U.S. Latina/o "
        "literature and cultural production."
    ),
    "School Of Visual Arts — Art": (
        "CFA studio art coursework spans drawing, painting, printmaking, and new "
        "media with Boston gallery and museum access."
    ),
    "Speech Language Hearing Sciences": (
        "Sargent speech, language, and hearing sciences covers audiology, speech pathology, "
        "and hearing science toward ASHA certification."
    ),
    "Speech Language Hearing Sciences — Ms": (
        "Sargent's M.S. in speech-language pathology combines hearing science with "
        "clinical practica toward ASHA certification."
    ),
    "Speech Language Hearing Sciences — Phd": (
        "Sargent speech-language-hearing Ph.D. research spans aphasia, motor speech "
        "disorders, and audiology science."
    ),
    "World Languages Literatures — Comparative Literature Mfa In Literary Translation": (
        "CAS/GRS comparative literature and literary translation integrates workshop "
        "critique with multilingual textual study."
    ),
    "World Languages Literatures — German": (
        "CAS German language and literature coursework combines Berlin study-abroad, "
        "linguistics, and literary analysis."
    ),
    "World Languages Literatures — Chinese": (
        "CAS Chinese language and literature coursework combines Beijing study-abroad, "
        "linguistics, and East Asian cultural studies."
    ),
    "World Languages Literatures — Japanese": (
        "CAS Japanese language and literature coursework combines Kyoto study-abroad, "
        "linguistics, and modern and classical Japanese texts."
    ),
    "World Languages Literatures — Korean": (
        "CAS Korean language and literature coursework combines language immersion, "
        "linguistics, and contemporary Korean culture."
    ),
    "World Languages Literatures — Italian": (
        "CAS Italian language and literature coursework combines Florence study-abroad, "
        "literary analysis, and Renaissance studies."
    ),
    "World Languages Literatures — Spanish": (
        "CAS Spanish language and literature coursework combines Madrid study-abroad, "
        "linguistics, and Latin American cultural studies."
    ),
    "World Languages Literatures — Russian": (
        "CAS Russian language and literature coursework combines language immersion, "
        "Slavic linguistics, and literary analysis."
    ),
    "Classical Studies — Ancient Greek Latin": (
        "CAS classical studies in ancient Greek and Latin combines philology, "
        "advanced translation, and survey of Greek and Roman literature."
    ),
    "Classical Studies — Ancient Greek": (
        "CAS ancient Greek coursework covers Attic prose, Homer, and advanced "
        "translation seminars in the Department of Classical Studies."
    ),
    "Classical Studies — Classical Civilization": (
        "CAS classical civilization examines Greek and Roman history, art, and "
        "literature in translation without the language-intensive track."
    ),
    "Classical Studies — Classics Archaeology": (
        "CAS classics and archaeology combines philology with field methods and "
        "Mediterranean excavation projects."
    ),
    "Classical Studies — Classics Philosophy": (
        "CAS classics and philosophy integrates ancient Greek and Latin texts with "
        "history of philosophy seminars."
    ),
    "Classical Studies — Classics Religion": (
        "CAS classics and religion examines Greco-Roman religious texts alongside "
        "comparative religion coursework."
    ),
    "Classical Studies — Phd": (
        "GRS classical studies Ph.D. research spans philology, ancient history, and "
        "archaeology with Mediterranean field opportunities."
    ),
    "Classical Studies — Ma In Classics Archaeology": (
        "GRS classics and archaeology M.A. combines philology with field methods and "
        "material-culture analysis."
    ),
    "Classical Studies — Ba In Classics Archaeology": (
        "CAS classics and archaeology B.A. combines language study with archaeological "
        "field methods and Mediterranean history."
    ),
    "Classical Studies — Ba Ma In Classics Archaeology": (
        "CAS/GRS classics and archaeology B.A./M.A. accelerates undergraduates into "
        "graduate philology and fieldwork coursework."
    ),
    "Earth Environment — Bama In Remote Sensing Geospatial Sciences": (
        "CAS/GRS remote sensing and geospatial sciences combines GIS, satellite imagery, "
        "and environmental analysis with earth-science field methods."
    ),
    "Earth Environment — Earth Environmental Sciences": (
        "CAS earth and environmental sciences B.A. covers climate, ecosystems, and "
        "geological processes along the Charles River research corridor."
    ),
    "Earth Environment — Energy Environment": (
        "CAS/GRS energy and environment coursework examines renewable systems, climate "
        "policy, and environmental economics."
    ),
    "Earth Environment — Energy Environment Mba Dual Degree Program": (
        "CAS/Questrom energy-and-environment M.B.A. dual degree trains sustainability "
        "leaders in policy, finance, and clean-energy markets."
    ),
    "Earth Environment — Remote Sensing": (
        "GRS remote sensing graduate coursework covers GIS, satellite data, and "
        "geospatial analysis for environmental research."
    ),
    "Mph — Chronic And Non Communicable Diseases": (
        "SPH's chronic-disease M.P.H. concentration examines epidemiology, prevention, "
        "and health-system responses to NCDs."
    ),
    "Mph — Community Assessment": (
        "SPH community-assessment M.P.H. training covers needs assessment, program "
        "evaluation, and community-engaged research methods."
    ),
    "Mph — Environmental Health": (
        "SPH environmental-health M.P.H. coursework covers exposure science, occupational "
        "health, and climate-related disease."
    ),
    "Mph — Epidemiology And Biostatistics": (
        "SPH epidemiology and biostatistics M.P.H. training spans study design, regression, "
        "and infectious-disease modeling."
    ),
    "Mph — Health Policy And Law": (
        "SPH health-policy and law M.P.H. examines insurance systems, regulation, and "
        "healthcare governance with BU Law cross-registration."
    ),
    "Mph — Healthcare Management": (
        "SPH healthcare-management M.P.H. trains leaders in hospital operations, quality "
        "improvement, and health-system analytics."
    ),
    "Mph — Human Rights And Social Justice": (
        "SPH human-rights M.P.H. concentration examines health equity, advocacy, and "
        "global social-determinants research."
    ),
    "Mph — Infectious Disease": (
        "SPH infectious-disease M.P.H. coursework covers outbreak investigation, "
        "vaccinology, and NEIDL-adjacent research training."
    ),
    "Mph — Maternal And Child Health": (
        "SPH maternal and child health M.P.H. examines perinatal epidemiology, "
        "family policy, and community health programs."
    ),
    "Mph — Mental Health And Substance Use": (
        "SPH mental-health M.P.H. concentration covers psychiatric epidemiology, "
        "addiction policy, and community behavioral-health systems."
    ),
    "Mph — Monitoring And Evaluation": (
        "SPH monitoring-and-evaluation M.P.H. training covers program metrics, "
        "impact assessment, and global health project design."
    ),
    "Mph — Pharmaceutical Development Delivery And Access": (
        "SPH pharmaceutical-access M.P.H. examines drug policy, global supply chains, "
        "and regulatory pathways for essential medicines."
    ),
    "Mph — Sex Sexuality And Gender": (
        "SPH sex, sexuality, and gender M.P.H. coursework examines LGBTQ+ health, "
        "reproductive justice, and gender-based violence prevention."
    ),
    "Romance Studies — Ancient Greek Mfa In Literary Translation": (
        "GRS ancient Greek literary translation combines philology workshops with "
        "M.F.A. critique in comparative literature."
    ),
    "Romance Studies — Chinese Mfa In Literary Translation": (
        "GRS Chinese literary translation M.F.A. integrates language proficiency with "
        "workshop-based translation of modern and classical texts."
    ),
    "Romance Studies — French Studies Mfa In Literary Translation": (
        "GRS French literary translation M.F.A. combines Paris field study with "
        "workshop critique and publishing practice."
    ),
    "Romance Studies — German Mfa In Literary Translation": (
        "GRS German literary translation M.F.A. integrates Berlin study-abroad with "
        "workshop-based translation of German-language texts."
    ),
    "Romance Studies — Italian": (
        "CAS and GRS Italian studies combine language immersion, literature, and "
        "Renaissance cultural history."
    ),
    "Romance Studies — Japanese Mfa In Literary Translation": (
        "GRS Japanese literary translation M.F.A. combines language study with "
        "workshop critique of modern and classical Japanese texts."
    ),
    "Romance Studies — Latin Mfa In Literary Translation": (
        "GRS Latin literary translation M.F.A. combines philology with workshop "
        "critique of classical and medieval Latin texts."
    ),
    "Romance Studies — Spanish": (
        "CAS and GRS Spanish studies span Peninsular and Latin American literature, "
        "linguistics, and cultural production."
    ),
    "Romance Studies — Spanish Mfa In Literary Translation": (
        "GRS Spanish literary translation M.F.A. integrates Madrid study-abroad with "
        "workshop-based translation practice."
    ),
    "School Of Music — Composition — Bm": (
        "CFA composition B.M. students study counterpoint, orchestration, and "
        "contemporary techniques with faculty composers."
    ),
    "School Of Music — Composition — Dma": (
        "CFA composition D.M.A. candidates pursue advanced portfolio work in "
        "contemporary classical composition."
    ),
    "School Of Music — Composition — Mm": (
        "CFA composition M.M. coursework covers analysis, orchestration, and "
        "studio composition with Boston ensemble readings."
    ),
    "School Of Music — Conducting — Dma": (
        "CFA conducting D.M.A. training emphasizes score study, rehearsal technique, "
        "and orchestral or choral leadership."
    ),
    "School Of Music — Conducting — Mm": (
        "CFA conducting M.M. students develop podium skills with BU ensembles and "
        "guest conductor masterclasses."
    ),
    "School Of Music — Historical Performance — Dma": (
        "CFA historical performance D.M.A. focuses on period instruments, baroque "
        "repertoire, and scholarly performance practice."
    ),
    "School Of Music — Historical Performance — Mm": (
        "CFA historical performance M.M. combines baroque technique with ensemble "
        "work in the Boston early-music community."
    ),
    "School Of Music — Music Education — Bm": (
        "CFA music education B.M. prepares K-12 licensed teachers with pedagogy "
        "seminars and Boston school placements."
    ),
    "School Of Music — Music Education — Mm": (
        "CFA music education M.M. covers advanced pedagogy, curriculum design, and "
        "ensemble leadership for licensed educators."
    ),
    "School Of Music — Musicology — Mm": (
        "CFA musicology M.M. coursework spans historical research, ethnomusicology, "
        "and archival study."
    ),
    "School Of Music — Performance — Bm": (
        "CFA performance B.M. provides conservatory-level studio training with "
        "Boston's professional orchestra and chamber scene."
    ),
    "School Of Music — Performance — Dma": (
        "CFA performance D.M.A. is a terminal studio credential for advanced "
        "instrumentalists and vocalists."
    ),
    "School Of Music — Performance — Mm": (
        "CFA performance M.M. combines studio work, recitals, and ensemble "
        "experience for pre-professional musicians."
    ),
    "School Of Theatre — Lighting Design — Bfa": (
        "CFA lighting design B.F.A. covers drafting, programming, and production "
        "design for BU Theatre seasons."
    ),
    "School Of Theatre — Scene Design — Bfa": (
        "CFA scene design B.F.A. integrates drafting, model building, and "
        "collaborative production work."
    ),
    "School Of Theatre — Sound Design — Bfa": (
        "CFA sound design B.F.A. covers live mixing, system design, and audio "
        "for theatre and media production."
    ),
    "School Of Theatre — Stage Management — Bfa": (
        "CFA stage management B.F.A. trains production leaders in scheduling, "
        "cue calling, and company management."
    ),
    "School Of Theatre — Technical Production — Bfa": (
        "CFA technical production B.F.A. covers rigging, carpentry, and "
        "production engineering for live performance."
    ),
    "School Of Visual Arts — Art Education — Art Education With Initial License": (
        "CFA art education M.A. with initial licensure prepares K-12 art teachers "
        "with studio practice and pedagogy seminars."
    ),
    "School Of Visual Arts — Art Education — Bfa": (
        "CFA art education B.F.A. combines studio art with teacher-preparation "
        "coursework and school placements."
    ),
    "School Of Visual Arts — Art Education — Online Ma In Art Education": (
        "CFA online M.A. in art education serves working educators with studio "
        "modules and curriculum design coursework."
    ),
    "School Of Visual Arts — Graphic Design — Bfa": (
        "CFA graphic design B.F.A. covers typography, branding, and digital "
        "media with portfolio reviews."
    ),
    "School Of Visual Arts — Painting — Bfa": (
        "CFA painting B.F.A. combines figure study, critique seminars, and "
        "solo exhibition preparation."
    ),
    "School Of Visual Arts — Printmaking 2 — Bfa": (
        "CFA printmaking B.F.A. covers intaglio, lithography, and contemporary "
        "print media in studio critiques."
    ),
    "School Of Visual Arts — Sculpture — Bfa": (
        "CFA sculpture B.F.A. integrates woodworking, metal fabrication, and "
        "installation practice with critique seminars."
    ),
    "World Languages Literatures — Bachelor Of Arts In Middle Eastern And South Asian Languages Literatures": (
        "CAS Middle Eastern and South Asian languages and literatures combines "
        "Arabic, Hindi-Urdu, or Persian with regional cultural study."
    ),
    "World Languages Literatures — Comparative Literature": (
        "CAS comparative literature examines multilingual texts, translation theory, "
        "and global literary traditions."
    ),
    "World Languages Literatures — Korean — Korean Language Literature": (
        "CAS Korean language and literature coursework combines Seoul study-abroad "
        "with modern and classical Korean texts."
    ),
    "Juris Doctor": (
        "BU Law's J.D. program combines clinical training in health law, IP, and "
        "international law with Boston's federal courts and financial-services employers."
    ),
    "Master of Business Administration": (
        "Questrom's M.B.A. emphasizes data-driven management, health-sector analytics, "
        "and social impact with Boston's finance, biotech, and consulting recruiting."
    ),
}

_ADAPT_RE: list[tuple[str, str]] = [
    (r"\bHarvard Business School\b", "Questrom School of Business"),
    (r"\bHarvard Law School\b", "BU School of Law"),
    (r"\bHarvard Medical School\b", "Chobanian & Avedisian School of Medicine"),
    (r"\bHarvard Graduate School of Design\b", "College of Fine Arts"),
    (r"\bHarvard Graduate School of Education\b", "Wheelock College of Education & Human Development"),
    (r"\bHarvard Kennedy School\b", "Pardee School of Global Studies"),
    (r"\bHarvard Faculty of Arts & Sciences\b", "College of Arts & Sciences"),
    (r"\bHarvard Faculty of Arts and Sciences\b", "College of Arts & Sciences"),
    (r"\bWharton\b", "Questrom School of Business"),
    (r"\bWhiting School of Engineering\b", "College of Engineering"),
    (r"\bKrieger School of Arts and Sciences\b", "College of Arts & Sciences"),
    (r"\bCarey School of Business\b", "Questrom School of Business"),
    (r"\bBloomberg School of Public Health\b", "School of Public Health"),
    (r"\bColumbia Business School\b", "Questrom School of Business"),
    (r"\bColumbia Law School\b", "BU School of Law"),
    (r"\bVagelos College of Physicians and Surgeons\b", "Chobanian & Avedisian School of Medicine"),
    (r"\bTeachers College\b", "Wheelock College of Education & Human Development"),
    (r"\bMailman School of Public Health\b", "School of Public Health"),
    (r"\bKellogg School of Management\b", "Questrom School of Business"),
    (r"\bPritzker School of Law\b", "BU School of Law"),
    (r"\bFeinberg School of Medicine\b", "Chobanian & Avedisian School of Medicine"),
    (r"\bMcCormick School of Engineering\b", "College of Engineering"),
    (r"\bWeinberg College of Arts and Sciences\b", "College of Arts & Sciences"),
    (r"\bMedill School\b", "College of Communication"),
    (r"\bLongwood Medical Area\b", "BU Medical Campus"),
    (r"\bCambridge\b", "Boston"),
    (r"\bEvanston\b", "Boston"),
    (r"\bWest Lafayette\b", "Boston"),
    (r"\bIthaca\b", "Boston"),
    (r"\bBaltimore\b", "Boston"),
    (r"\bPhiladelphia\b", "Boston"),
    (r"\bManhattan\b", "Boston"),
    (r"\bNew York City\b", "Boston"),
    (r"\bHouston\b", "Boston"),
    (r"\bChicago\b", "Boston"),
    (r"\bChesapeake\b", "Boston Harbor"),
    (r"\bFinger Lakes\b", "Boston Harbor"),
    (r"\bCentral Valley\b", "Greater Boston"),
    (r"\bHarvard\b", "Boston University"),
    (r"\bColumbia\b", "Boston University"),
    (r"\bNorthwestern\b", "Boston University"),
    (r"\bJohns Hopkins\b", "Boston University"),
    (r"\bJHU\b", "Boston University"),
    (r"\bHopkins\b", "Boston University"),
    (r"\bPenn\b", "Boston University"),
    (r"\bCornell\b", "Boston University"),
    (r"\bBerkeley\b", "Boston University"),
    (r"\bRice\b", "Boston University"),
    (r"\bPurdue\b", "Boston University"),
    (r"\bMIT\b", "Boston University"),
    (r"\bCaltech\b", "Boston University"),
    (r"\bPrinceton\b", "Boston University"),
    (r"\bYale\b", "Boston University"),
    (r"\bStanford\b", "Boston University"),
    (r"\bUCLA\b", "Boston University"),
    (r"\bUSC\b", "Boston University"),
    (r"\bWriting Seminars\b", "CAS Writing Program"),
    (r"\bSAS\b", "College of Arts & Sciences"),
    (r"\bCALS\b", "College of Arts & Sciences"),
    (r"\bWeill Cornell\b", "BU Medical Campus"),
    (r"\bSibley School\b", "College of Engineering"),
    (r"\bRausser\b", "College of Arts & Sciences"),
    (r"\bNIH-funded\b", "federally funded"),
]

_PEER_KEY_ALIASES: dict[str, str] = {
    "Anthropology": "Anthropology",
    "Biology": "Biology, General",
    "Chemistry": "Chemistry, General",
    "Computer Science": "Computer Science",
    "Economics": "Economics",
    "English": "English Language and Literature, General",
    "History": "History, General",
    "Mathematics": "Mathematics, General",
    "Physics": "Physics, General",
    "Psychology": "Psychology, General",
    "Political Science": "Political Science and Government",
    "Philosophy": "Philosophy",
    "Sociology": "Sociology",
    "Statistics": "Statistics, General",
    "Biochemistry": "Biochemistry, Biophysics and Molecular Biology",
    "Biomedical Engineering": "Biomedical/Medical Engineering",
    "Electrical Engineering": "Electrical, Electronics, and Communications Engineering",
    "Mechanical Engineering": "Mechanical Engineering",
    "Materials Science Engineering": "Materials Engineering",
    "Computer Engineering": "Computer Engineering",
    "Neuroscience": "Neurobiology and Neurosciences",
    "Journalism": "Journalism",
    "International Relations": "International Relations and Affairs",
    "Public Health": "Public Health, General",
    "Social Work": "Social Work",
    "Law": "Law",
    "Medicine": "Medicine",
    "Architecture": "Architecture",
    "Art History": "Art History, Criticism and Conservation",
    "Music": "Music",
    "Theatre": "Drama/Theatre Arts and Stagecraft",
    "Film": "Film/Cinema/Video and Photographic Arts",
    "Communication": "Communication and Media Studies",
    "Accounting": "Accounting and Related Services",
    "Finance": "Finance and Financial Management Services",
    "Marketing": "Marketing/Marketing Management, General",
    "Management": "Business Administration and Management, General",
    "Biostatistics": "Biostatistics",
    "Genetics Genomics": "Genetics, General",
    "Physiology Biophysics": "Physiology, Pathology and Related Sciences",
    "Pharmacology Experimental Therapeutics": "Pharmacology and Toxicology",
    "Pathology Laboratory Medicine": "Pathology/Experimental Pathology",
    "Anatomy Neurobiology": "Anatomy",
    "Molecular Biology Cell Biology Biochemistry": "Cell/Cellular Biology and Anatomical Sciences",
    "Medical Sciences": "Medical Sciences",
    "Behavioral Neuroscience": "Neurobiology and Neurosciences",
    "Cognitive Neural Systems": "Neurobiology and Neurosciences",
    "Astronomy": "Astronomy and Astrophysics",
    "Archaeology": "Archeology",
    "Classical Studies": "Classics and Classical Languages, Literatures, and Linguistics",
    "Religion": "Religion/Religious Studies",
    "European Studies": "European Studies/Civilization",
    "Latin American Studies": "Latin American Studies",
    "African American Studies": "African American/Black Studies",
    "Linguistics": "Linguistic, Comparative, and Related Language Studies and Services",
    "Earth Environment": "Geology/Earth Science, General",
    "Environmental Health": "Environmental Health",
    "Epidemiology": "Epidemiology",
    "Occupational Therapy": "Occupational Therapy/Therapist",
    "Physical Therapy": "Physical Therapy/Therapist",
    "Speech Language Hearing Sciences": "Speech-Language Pathology/Pathologist",
    "Nutrition Dietetics": "Dietetics/Dietitian",
    "Health Communication": "Public Relations, Advertising, and Applied Communication",
    "Advertising": "Public Relations, Advertising, and Applied Communication",
    "Criminal Justice": "Criminal Justice/Safety Studies",
    "Actuarial Science": "Actuarial Science",
    "Mathematical Finance": "Financial Mathematics",
    "Systems Engineering": "Systems Engineering",
    "Bioimaging": "Biomedical/Medical Engineering",
    "Biology — Master Of Science In Biology": "Biology, General",
    "Preservation Studies": "Historic Preservation and Conservation",
    "History Art Architecture": "Art History, Criticism and Conservation",
    "Cinema Media Studies — Ba In Cinema Media Studies": "Film/Cinema/Video and Photographic Arts",
    "Biochemistry Molecular Biology": "Biochemistry, Biophysics and Molecular Biology",
    "Applied Mathematics": "Applied Mathematics",
    "Genetic Counseling": "Genetic Counseling/Counselor",
    "Physician Assistant": "Physician Assistant",
    "Dental Public Health": "Dental Public Health and Education",
    "Endodontics": "Advanced/Graduate Dentistry and Oral Sciences",
    "Operative Dentistry": "Advanced/Graduate Dentistry and Oral Sciences",
    "Oral Biology": "Advanced/Graduate Dentistry and Oral Sciences",
    "Pediatric Dentistry": "Advanced/Graduate Dentistry and Oral Sciences",
    "Periodontology": "Advanced/Graduate Dentistry and Oral Sciences",
    "Prosthodontics": "Advanced/Graduate Dentistry and Oral Sciences",
    "Orthodontics Dentofacial Orthopedics": "Advanced/Graduate Dentistry and Oral Sciences",
    "Oral And Maxillofacial Surgery": "Advanced/Graduate Dentistry and Oral Sciences",
}

SLUG_DESCRIPTIONS: dict[str, str] = {
    "bu-academics-questrom-mba": (
        "Questrom's M.B.A. emphasizes data-driven management, health-sector analytics, "
        "and social impact with Boston's finance, biotech, and consulting recruiting pipelines."
    ),
    "bu-academics-law-jd": (
        "BU Law's J.D. program combines clinical training in health law, IP, and international "
        "law with Boston's federal courts and financial-services employers."
    ),
    "bu-academics-busm-four-year-program": (
        "BU's Chobanian & Avedisian School of Medicine four-year M.D. curriculum combines "
        "foundational sciences, clinical clerkships at Boston Medical Center, and "
        "longitudinal patient-care experiences on the Medical Campus."
    ),
    "bu-academics-cas-computer-science-ba": (
        "CAS computer science covers algorithms, systems, and AI with ties to the Hariri "
        "Institute and Boston's technology sector — U.S. News ranks BU CS among top programs."
    ),
    "bu-academics-cds-bs-in-data-science": (
        "CDS's undergraduate data-science major integrates statistics, computing, and "
        "domain applications in the Center for Computing & Data Sciences tower."
    ),
    "bu-academics-cds-msds": (
        "CDS's M.S. in Data Science trains students in machine learning, responsible AI, "
        "and interdisciplinary data projects across BU schools."
    ),
    "bu-academics-questrom-msba": (
        "Questrom's M.S. in Business Analytics emphasizes predictive modeling, prescriptive "
        "analytics, and data-driven decision making for industry."
    ),
    "bu-academics-cas-economics-ba": (
        "CAS economics combines micro and macro theory, econometrics, and policy analysis "
        "with Boston's finance and nonprofit research institutions."
    ),
    "bu-academics-com-journalism-bs": (
        "COM journalism combines reporting, multimedia production, and media law with "
        "internships at Boston's newsrooms and NPR affiliates."
    ),
    "bu-academics-eng-biomedical-engineering-bs": (
        "ENG biomedical engineering integrates device design, imaging, and tissue engineering "
        "with the Photonics Center and Medical Campus research labs."
    ),
    "bu-academics-sph-mph": (
        "SPH's M.P.H. covers epidemiology, biostatistics, and health policy — BU ranks among "
        "the top U.S. schools of public health."
    ),
    "bu-academics-ssw-msw": (
        "SSW's M.S.W. emphasizes clinical practice, trauma-informed care, and macro policy "
        "with field placements across Greater Boston."
    ),
}


def _adapt(text: str) -> str:
    out = text
    for pat, repl in _ADAPT_RE:
        out = re.sub(pat, repl, out)
    return out


def _clause_for(field: str) -> str:
    if field in BU_MANUAL:
        return BU_MANUAL[field]
    peer_key = _PEER_KEY_ALIASES.get(field, field)
    for src in (PENN, JHU, NORTHWESTERN, HARVARD, COLUMBIA, BERKELEY, RICE):
        if peer_key in src:
            return _adapt(src[peer_key])
        if field in src:
            return _adapt(src[field])
    # Try normalized field (strip credential suffix after em dash)
    base = field.split(" — ")[0].strip()
    if base in BU_MANUAL:
        return BU_MANUAL[base]
    peer_key = _PEER_KEY_ALIASES.get(base, base)
    for src in (PENN, JHU, NORTHWESTERN, HARVARD, COLUMBIA, BERKELEY, RICE):
        if peer_key in src:
            return _adapt(src[peer_key])
        if base in src:
            return _adapt(src[base])
    raise KeyError(f"No source clause for {field!r} (peer_key={peer_key!r})")


def main() -> None:
    global FIELDS
    FIELDS = sorted(_all_catalog_fields())
    missing: list[str] = []
    clauses: dict[str, str] = {}
    for field in FIELDS:
        try:
            clauses[field] = _clause_for(field)
        except KeyError:
            missing.append(field)

    if missing:
        print(f"MISSING {len(missing)} fields:")
        for f in missing:
            print(f"  {f!r}")
        raise SystemExit(1)

    out_path = (
        Path(__file__).resolve().parents[1]
        / "src/unipaith/data/bu_field_descriptions.py"
    )
    lines = [
        '"""Field-specific program description clauses for Boston University.',
        "",
        "Each entry states something concrete about what BU's program in that field",
        "covers — never a credential/school classification stub. Sources: BU Academics",
        "(bu.edu/academics/), college and department catalog pages, Questrom, COM, ENG,",
        "CAS, CDS, Wheelock, Sargent, GRS, GMS, SDM, SPH, Law, SSW, MET, and CFA.",
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
