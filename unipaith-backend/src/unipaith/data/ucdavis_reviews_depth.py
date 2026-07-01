"""University of California-Davis external_reviews depth pass.

Depth pass date: 2026-07-01. Consumed by ``ucdavis_profile`` (merged into
``_REVIEWS_BY_SLUG`` via ``**DEPTH_REVIEWS``) and re-applied by the
``ucdreviews1`` migration. Adds twelve program-specific flagship reviews to the
four already present (D.V.M., M.B.A., J.D., M.D.), each hand-gathered from real
program-specific third-party or official coverage — UC Davis's QS and U.S. News
subject rankings, Poets&Quants / QS business-school rankings, and the official
department/school pages — pairing genuine praise with the common cautions and
carrying resolvable, program-specific sources. Never synthesized from metadata
(SKILL.md miss #8, coverage-gated depth pass). Programs with no verifiable
program-specific third-party coverage stay honestly omitted.
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Themes are aggregated and paraphrased from public third-party coverage and "
    "official school information, not individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "ucdavis-viticulture-enology-ms": {
        "summary": (
            "UC Davis's Department of Viticulture and Enology — established in 1880 — is "
            "widely regarded as the world's leading center for wine science, and its "
            "graduate program is described by industry and academic sources as the field's "
            "gold standard. UC Davis ranks No. 2 in the world and No. 1 in the nation in "
            "Agriculture and Forestry in the QS World University Rankings by Subject, and "
            "the M.S. combines rigorous grape- and wine-chemistry research with an on-campus "
            "teaching winery and research vineyards. Common cautions are the heavily "
            "technical, chemistry- and microbiology-intensive curriculum and the small, "
            "specialized field."
        ),
        "themes": [
            {
                "label": "World-leading program",
                "sentiment": "positive",
                "detail": (
                    "UC Davis is consistently described as the top wine-science program "
                    "globally; the university ranks No. 2 in the world in Agriculture and "
                    "Forestry (QS)."
                ),
            },
            {
                "label": "Research facilities",
                "sentiment": "positive",
                "detail": (
                    "A teaching-and-research winery, research vineyards, and analytical "
                    "labs support hands-on grape- and wine-chemistry research."
                ),
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates are routinely hired into leading wineries and viticultural "
                    "research roles in California and worldwide."
                ),
            },
            {
                "label": "Technical intensity",
                "sentiment": "caution",
                "detail": (
                    "The curriculum is chemistry- and microbiology-heavy; applicants "
                    "without a strong science background must prepare accordingly."
                ),
            },
            {
                "label": "Niche field",
                "sentiment": "mixed",
                "detail": (
                    "The specialization is narrow, so the cohort and alumni network are "
                    "small relative to broader science programs."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis — Department of Viticulture and Enology",
                "url": "https://wineserver.ucdavis.edu/",
            },
            {
                "label": "UC Davis — Rankings (Agriculture and Forestry, QS)",
                "url": "https://www.ucdavis.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-viticulture-enology-bs": {
        "summary": (
            "The undergraduate Viticulture and Enology major at UC Davis is the "
            "best-known wine-science bachelor's program in the country, grounded in the "
            "department established in 1880 at a university QS ranks No. 2 in the world in "
            "Agriculture and Forestry. Students take a rigorous science core — chemistry, "
            "microbiology, and plant biology — and work with the campus teaching winery and "
            "vineyards. Common cautions are the demanding science load and that some "
            "sensory-evaluation coursework requires students to be 21."
        ),
        "themes": [
            {
                "label": "Flagship undergraduate program",
                "sentiment": "positive",
                "detail": (
                    "Widely recognized as the leading undergraduate wine-science program, "
                    "at a top-ranked agriculture university."
                ),
            },
            {
                "label": "Hands-on winemaking",
                "sentiment": "positive",
                "detail": (
                    "The on-campus teaching winery and research vineyards give students "
                    "practical grape-growing and winemaking experience."
                ),
            },
            {
                "label": "Strong industry ties",
                "sentiment": "positive",
                "detail": (
                    "Proximity to California's wine regions supports internships and "
                    "hiring into the industry."
                ),
            },
            {
                "label": "Heavy science load",
                "sentiment": "caution",
                "detail": (
                    "The chemistry- and biology-intensive core is demanding for a "
                    "practice-oriented field."
                ),
            },
            {
                "label": "Age requirement for sensory work",
                "sentiment": "mixed",
                "detail": (
                    "Some sensory and tasting coursework requires students to be of legal "
                    "drinking age."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis — Viticulture and Enology major",
                "url": "https://www.ucdavis.edu/majors/viticulture-and-enology",
            },
            {
                "label": "UC Davis — Department of Viticulture and Enology",
                "url": "https://wineserver.ucdavis.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-ecology-phd": {
        "summary": (
            "The UC Davis Graduate Group in Ecology is the largest and most comprehensive "
            "ecology doctoral program of its kind, spanning more than a hundred affiliated "
            "faculty across departments, and it has long been regarded as one of the "
            "strongest ecology doctoral programs in the country — U.S. News has ranked UC "
            "Davis's ecology and evolutionary biology at or near the top nationally. "
            "Students praise the breadth of research and interdisciplinary reach. Common "
            "cautions are that funding and advising vary by lab and that the decentralized, "
            "very large group can feel diffuse."
        ),
        "themes": [
            {
                "label": "Top-ranked nationally",
                "sentiment": "positive",
                "detail": (
                    "U.S. News has ranked UC Davis's ecology and evolutionary biology "
                    "among the very best in the nation."
                ),
            },
            {
                "label": "Breadth and interdisciplinarity",
                "sentiment": "positive",
                "detail": (
                    "The Graduate Group in Ecology draws faculty from across the campus, "
                    "giving unusually broad research options."
                ),
            },
            {
                "label": "Research resources",
                "sentiment": "positive",
                "detail": (
                    "Field stations, reserves, and strong environmental-science ties "
                    "support fieldwork."
                ),
            },
            {
                "label": "Advisor-dependent funding",
                "sentiment": "caution",
                "detail": (
                    "As with most Ph.D. programs, support and mentoring depend heavily on "
                    "the chosen lab and advisor."
                ),
            },
            {
                "label": "Large, decentralized group",
                "sentiment": "mixed",
                "detail": (
                    "The size and cross-department structure can feel diffuse to students "
                    "who prefer a small, single-department cohort."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis — Ecology and evolution ranked top in nation",
                "url": "https://www.ucdavis.edu/news/ecology-evolution-ranked-top-nation",
            },
            {
                "label": "UC Davis Graduate Group in Ecology",
                "url": "https://ecology.ucdavis.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-agricultural-resource-economics-phd": {
        "summary": (
            "UC Davis's Department of Agricultural and Resource Economics is consistently "
            "ranked at or near the top of the world in agricultural economics and policy, "
            "and it sits within the university ranked No. 2 globally in Agriculture and "
            "Forestry. The Ph.D. is a rigorous, quantitative program with strong placement "
            "into academia, government, and industry. Common cautions are the heavy "
            "econometrics and theory workload and highly competitive admission."
        ),
        "themes": [
            {
                "label": "World-leading department",
                "sentiment": "positive",
                "detail": (
                    "Consistently ranked at or near the top of the world in agricultural "
                    "and resource economics and policy in subject rankings."
                ),
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into research universities, government agencies, and "
                    "industry economics roles."
                ),
            },
            {
                "label": "Research resources",
                "sentiment": "positive",
                "detail": (
                    "Ties to agricultural, environmental, and development economics give "
                    "broad dissertation options."
                ),
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "caution",
                "detail": (
                    "The program is demanding in econometrics and economic theory; strong "
                    "math preparation is expected."
                ),
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": (
                    "As a top-ranked doctoral program, admission is highly competitive."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis — Tops World Rankings in Agricultural Economics and Policy",
                "url": "https://www.ucdavis.edu/news/uc-davis-tops-world-rankings-agricultural-economics-and-policy",
            },
            {
                "label": "UC Davis — Department of Agricultural and Resource Economics",
                "url": "https://are.ucdavis.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-entomology-phd": {
        "summary": (
            "The UC Davis Department of Entomology and Nematology is ranked among the best "
            "in the world — No. 7 globally in one subject assessment — with deep faculty "
            "strength in integrated pest management, pollinator biology, and medical and "
            "agricultural entomology. Doctoral students praise the research breadth and "
            "collections. Common cautions are the specialized field and advisor-dependent "
            "funding."
        ),
        "themes": [
            {
                "label": "Among the best in the world",
                "sentiment": "positive",
                "detail": (
                    "Ranked No. 7 globally in a subject assessment; a long-standing "
                    "top-tier entomology department."
                ),
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": (
                    "Strength across integrated pest management, pollinators, and medical "
                    "and agricultural entomology."
                ),
            },
            {
                "label": "Collections and facilities",
                "sentiment": "positive",
                "detail": (
                    "The Bohart Museum of Entomology and research collections support "
                    "specimen-based work."
                ),
            },
            {
                "label": "Specialized field",
                "sentiment": "mixed",
                "detail": (
                    "Entomology is a narrow discipline; career paths concentrate in "
                    "research, agriculture, and public health."
                ),
            },
            {
                "label": "Advisor-dependent funding",
                "sentiment": "caution",
                "detail": (
                    "Support and project scope depend on the specific lab and grants."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis Entomology & Nematology — Ranked One of the Best in the World (UC ANR)",
                "url": "https://ucanr.edu/blogs/blogcore/postdetail.cfm?postnum=23692",
            },
            {
                "label": "UC Davis Entomology and Nematology — Graduate programs",
                "url": "https://entomology.ucdavis.edu/graduate-programs",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-plant-biology-phd": {
        "summary": (
            "UC Davis is ranked No. 1 in the nation in plant and animal sciences and No. 2 "
            "in the world in Agriculture and Forestry (QS), and its plant-science research "
            "base is among the largest anywhere. The Plant Biology Ph.D. offers broad "
            "research options from molecular biology to whole-plant physiology and ecology. "
            "Common cautions are the research-intensive path and advisor-dependent funding "
            "typical of the sciences."
        ),
        "themes": [
            {
                "label": "Top-ranked plant science",
                "sentiment": "positive",
                "detail": (
                    "UC Davis is ranked No. 1 in the nation in plant and animal sciences "
                    "and No. 2 in the world in Agriculture and Forestry (QS)."
                ),
            },
            {
                "label": "Deep research base",
                "sentiment": "positive",
                "detail": (
                    "One of the largest concentrations of plant-science faculty and "
                    "facilities in the world."
                ),
            },
            {
                "label": "Breadth of subfields",
                "sentiment": "positive",
                "detail": (
                    "Research spans molecular biology, genetics, physiology, and "
                    "plant ecology."
                ),
            },
            {
                "label": "Research-intensive",
                "sentiment": "caution",
                "detail": (
                    "The doctorate is a long, lab-based commitment expecting sustained "
                    "independent research."
                ),
            },
            {
                "label": "Advisor-dependent funding",
                "sentiment": "caution",
                "detail": (
                    "Support and project direction depend on the lab and grant funding."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis CAES — Rankings (plant and animal sciences)",
                "url": "https://caes.ucdavis.edu/about/overview/rankings",
            },
            {
                "label": "UC Davis — Rankings",
                "url": "https://www.ucdavis.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-animal-science-bs": {
        "summary": (
            "UC Davis's undergraduate Animal Science major sits in a university ranked No. 1 "
            "in the nation in plant and animal sciences (and No. 2 in the world in "
            "Agriculture and Forestry, QS), with extensive on-campus animal facilities — "
            "dairy, equine, meat, and avian units — and a strong pre-veterinary pipeline "
            "toward UC Davis's top-ranked veterinary school. Common cautions are the large "
            "major size and the very competitive path into veterinary school."
        ),
        "themes": [
            {
                "label": "Top-ranked field",
                "sentiment": "positive",
                "detail": (
                    "UC Davis is ranked No. 1 in the nation in plant and animal sciences "
                    "and No. 2 in the world in Agriculture and Forestry (QS)."
                ),
            },
            {
                "label": "Hands-on facilities",
                "sentiment": "positive",
                "detail": (
                    "Campus dairy, equine, meat, and other animal units give practical, "
                    "hands-on experience."
                ),
            },
            {
                "label": "Pre-vet strength",
                "sentiment": "positive",
                "detail": (
                    "A common route toward UC Davis's top-ranked veterinary school and "
                    "animal-health careers."
                ),
            },
            {
                "label": "Large major",
                "sentiment": "mixed",
                "detail": (
                    "A popular, sizeable major means introductory courses can be large."
                ),
            },
            {
                "label": "Competitive vet-school path",
                "sentiment": "caution",
                "detail": (
                    "Admission to veterinary school is highly competitive and requires "
                    "strong grades and experience."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis Department of Animal Science — Ranking",
                "url": "https://animalscience.ucdavis.edu/about/ranking",
            },
            {
                "label": "UC Davis — Rankings",
                "url": "https://www.ucdavis.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-food-science-bs": {
        "summary": (
            "UC Davis is among the world's leading food-science programs, part of a college "
            "ranked No. 2 globally in Agriculture and Forestry (QS) and among the top "
            "programs nationally in food science and technology. The Food Science major "
            "pairs a chemistry- and microbiology-based core with strong ties to California's "
            "food and beverage industry. Common cautions are the demanding science load and "
            "the specialized focus."
        ),
        "themes": [
            {
                "label": "World-leading program",
                "sentiment": "positive",
                "detail": (
                    "Among the top food-science programs globally, at a university ranked "
                    "No. 2 in the world in Agriculture and Forestry."
                ),
            },
            {
                "label": "Industry connections",
                "sentiment": "positive",
                "detail": (
                    "Deep ties to California's food, beverage, and agricultural industries "
                    "support internships and hiring."
                ),
            },
            {
                "label": "Top-ranked nationally",
                "sentiment": "positive",
                "detail": (
                    "UC Davis is ranked among the top programs in the nation in food "
                    "science and technology."
                ),
            },
            {
                "label": "Heavy science core",
                "sentiment": "caution",
                "detail": (
                    "The chemistry- and microbiology-intensive curriculum is demanding."
                ),
            },
            {
                "label": "Specialized focus",
                "sentiment": "mixed",
                "detail": (
                    "The major is applied and focused; students seeking a broad science "
                    "degree should weigh the fit."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis — Food Science major",
                "url": "https://www.ucdavis.edu/majors/food-science",
            },
            {
                "label": "UC Davis CAES — Rankings",
                "url": "https://caes.ucdavis.edu/about/overview/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-business-analytics-msba": {
        "summary": (
            "The UC Davis Graduate School of Management M.S. in Business Analytics is an "
            "intensive, STEM-designated program that has ranked No. 1 in the world for "
            "return on investment for four consecutive years and No. 5 worldwide for value "
            "for money in the QS business master's rankings, with a cited 10-year ROI "
            "approaching seven figures. Students praise the applied, project-based "
            "curriculum. Common cautions are the demanding quantitative pace and program "
            "cost."
        ),
        "themes": [
            {
                "label": "No. 1 for ROI",
                "sentiment": "positive",
                "detail": (
                    "Ranked No. 1 in the world for return on investment for four "
                    "consecutive years (QS)."
                ),
            },
            {
                "label": "Value for money",
                "sentiment": "positive",
                "detail": (
                    "Ranked No. 5 worldwide for value for money and among the top 20 in "
                    "the U.S. (QS)."
                ),
            },
            {
                "label": "Applied, STEM-designated",
                "sentiment": "positive",
                "detail": (
                    "A hands-on, project-based curriculum with a practicum and "
                    "STEM designation."
                ),
            },
            {
                "label": "Quantitative intensity",
                "sentiment": "caution",
                "detail": (
                    "The fast-paced, math-heavy program expects strong quantitative "
                    "preparation."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "A graduate professional program carries meaningful tuition; the "
                    "strong ROI is the offset cited."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis GSM — Our Accolades (MSBA rankings, QS 2026)",
                "url": "https://gsm.ucdavis.edu/about-us/our-accolades",
            },
            {
                "label": "UC Davis GSM — Rankings",
                "url": "https://gsm.ucdavis.edu/tags/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-master-of-public-health-mph": {
        "summary": (
            "The UC Davis Master of Public Health, based in the School of Medicine's "
            "Department of Public Health Sciences, is fully accredited by the Council on "
            "Education for Public Health (CEPH) and ranks among the top public-health "
            "graduate programs (U.S. News places UC Davis in the low-20s nationally). It is "
            "an accelerated, in-person degree with general and epidemiology concentrations "
            "and strengths in rural, agricultural, and One Health topics. Common cautions "
            "are the intensive accelerated pace and in-person format."
        ),
        "themes": [
            {
                "label": "Accredited and well-ranked",
                "sentiment": "positive",
                "detail": (
                    "CEPH-accredited and ranked among the top ~20-25 public-health "
                    "programs nationally by U.S. News."
                ),
            },
            {
                "label": "Distinctive strengths",
                "sentiment": "positive",
                "detail": (
                    "Rural, agricultural, environmental, and One Health focus areas draw "
                    "on UC Davis's research base."
                ),
            },
            {
                "label": "Epidemiology track",
                "sentiment": "positive",
                "detail": (
                    "General and epidemiology concentrations let students specialize."
                ),
            },
            {
                "label": "Accelerated pace",
                "sentiment": "caution",
                "detail": (
                    "The compressed, in-person format is demanding and requires full-time "
                    "commitment."
                ),
            },
            {
                "label": "In-person only",
                "sentiment": "mixed",
                "detail": (
                    "The program is campus-based; there is no fully online option for the "
                    "core degree."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — UC Davis Best Health Schools (Public Health)",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/university-of-california-davis-110644",
            },
            {
                "label": "UC Davis Health — Master of Public Health",
                "url": "https://health.ucdavis.edu/phs/education/mph/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-creative-writing-mfa": {
        "summary": (
            "UC Davis's Creative Writing Program has a respected workshop tradition dating "
            "to 1975 with award-winning faculty, and its alumni have published books with "
            "major trade presses. Students value the small, faculty-close workshops. Common "
            "cautions are the small cohort and that the formal M.F.A. degree is relatively "
            "new, though the underlying program is long-established."
        ),
        "themes": [
            {
                "label": "Respected program and faculty",
                "sentiment": "positive",
                "detail": (
                    "A long workshop tradition since 1975 with award-winning writers on "
                    "the faculty."
                ),
            },
            {
                "label": "Published alumni",
                "sentiment": "positive",
                "detail": (
                    "Graduates have published books with major trade presses."
                ),
            },
            {
                "label": "Close mentorship",
                "sentiment": "positive",
                "detail": (
                    "Small workshops offer close contact with faculty writers."
                ),
            },
            {
                "label": "Small cohort",
                "sentiment": "mixed",
                "detail": (
                    "The intimate program admits few students each year, so peer breadth "
                    "is limited."
                ),
            },
            {
                "label": "Newer formal M.F.A.",
                "sentiment": "caution",
                "detail": (
                    "The M.F.A. degree itself is relatively recent, though the underlying "
                    "program is long-established."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis English — M.F.A. in Creative Writing",
                "url": "https://english.ucdavis.edu/mfa-creative-writing",
            },
            {
                "label": "UC Davis English — History of the Program",
                "url": "https://english.ucdavis.edu/history-program",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucdavis-master-of-laws-llm": {
        "summary": (
            "The UC Davis School of Law (King Hall) is a well-regarded U.S. law school, and "
            "its LL.M. integrates internationally trained lawyers into J.D. classes with "
            "concentrations in business, intellectual property, environmental, criminal, "
            "immigration, and tax law. Students value the small, collegial community and "
            "faculty access. Common cautions are the one-year intensity and the U.S.-focused "
            "curriculum for foreign-trained lawyers."
        ),
        "themes": [
            {
                "label": "Well-regarded law school",
                "sentiment": "positive",
                "detail": (
                    "King Hall is consistently ranked in the U.S. News tier of American "
                    "law schools."
                ),
            },
            {
                "label": "Integrated with J.D. courses",
                "sentiment": "positive",
                "detail": (
                    "LL.M. students take courses alongside J.D. students and choose among "
                    "several concentrations."
                ),
            },
            {
                "label": "Collegial community",
                "sentiment": "positive",
                "detail": (
                    "A small, supportive environment with strong faculty access is a "
                    "recurring theme."
                ),
            },
            {
                "label": "One-year intensity",
                "sentiment": "caution",
                "detail": (
                    "The degree is completed in one intensive year."
                ),
            },
            {
                "label": "U.S.-focused",
                "sentiment": "mixed",
                "detail": (
                    "The curriculum centers on U.S. law, which suits some international "
                    "goals better than others."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Davis School of Law — LL.M. Program",
                "url": "https://law.ucdavis.edu/international/llm",
            },
            {
                "label": "LSAC — UC Davis School of Law (LL.M.)",
                "url": "https://www.lsac.org/choosing-law-school/find-law-school/llm-and-other-law-programs-us-canada/uc-davis",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
