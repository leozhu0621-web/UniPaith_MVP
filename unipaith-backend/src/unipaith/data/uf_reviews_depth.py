"""University of Florida external_reviews depth pass.

Depth pass date: 2026-06-20. Consumed by ``uf_profile._REVIEWS_BY_SLUG`` for
coverable flagship programs beyond the inline flagship reviews.
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "uf-chemical-engineering-bs": {
        "summary": (
            "UF's undergraduate chemical engineering program in the Herbert Wertheim College of "
            "Engineering is ranked among the top public programs nationally. Students cite strong "
            "placement in process industries, pharmaceuticals, and energy, though the engineering "
            "core is rigorous and lower-division courses can be large."
        ),
        "themes": [
            {"label": "Program reputation", "sentiment": "positive", "detail": "U.S. News ranks UF engineering among top public programs nationally."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Chemical, pharmaceutical, and energy firms recruit from Gainesville."},
            {"label": "Curriculum rigor", "sentiment": "caution", "detail": "Math and chemistry gateway sequence is demanding in the first two years."},
            {"label": "Research access", "sentiment": "positive", "detail": "Faculty labs in catalysis, biomaterials, and sustainable energy accept undergraduates."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate"},
            {"label": "UF Chemical Engineering", "url": "https://www.che.ufl.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uf-civil-engineering-bs": {
        "summary": (
            "UF civil and coastal engineering undergraduates benefit from Florida-focused strengths "
            "in coastal resilience, water resources, and transportation. Reviewers note strong "
            "public-sector and consulting placement in Florida, with capstone projects tied to "
            "state infrastructure needs."
        ),
        "themes": [
            {"label": "Coastal engineering", "sentiment": "positive", "detail": "Florida's coastal environment gives distinctive research and project opportunities."},
            {"label": "State placement", "sentiment": "positive", "detail": "Florida DOT, consulting firms, and municipal agencies recruit actively."},
            {"label": "Large lectures", "sentiment": "mixed", "detail": "Introductory engineering courses can feel impersonal without proactive engagement."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition and strong ROI for Florida residents."},
        ],
        "sources": [
            {"label": "UF Department of Civil and Coastal Engineering", "url": "https://www.essie.ufl.edu/people/name/ccee/"},
            {"label": "Niche — University of Florida", "url": "https://www.niche.com/colleges/university-of-florida/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uf-industrial-engineering-bs": {
        "summary": (
            "UF's industrial and systems engineering program emphasizes analytics, operations research, "
            "and supply chain optimization. Students value placement in logistics, healthcare "
            "operations, and consulting, though competition for analytics-focused internships is strong."
        ),
        "themes": [
            {"label": "Analytics focus", "sentiment": "positive", "detail": "Curriculum integrates optimization, simulation, and data-driven decision making."},
            {"label": "Consulting recruiting", "sentiment": "positive", "detail": "Operations and supply chain roles at major firms recruit from ISE."},
            {"label": "Interdisciplinary breadth", "sentiment": "positive", "detail": "Business and statistics coursework pairs well with engineering core."},
            {"label": "Selective internships", "sentiment": "caution", "detail": "Top analytics internships require early résumé building and networking."},
        ],
        "sources": [
            {"label": "UF Industrial and Systems Engineering", "url": "https://www.ise.ufl.edu/"},
            {"label": "U.S. News — University of Florida", "url": "https://www.usnews.com/best-colleges/university-of-florida-1535"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uf-public-health-ms": {
        "summary": (
            "The UF College of Public Health and Health Professions offers MPH and related graduate "
            "programs with strengths in health policy, epidemiology, and rehabilitation sciences "
            "supported by UF Health. Graduates value the health-sciences campus proximity, though "
            "funding and assistantship availability vary by department."
        ),
        "themes": [
            {"label": "UF Health proximity", "sentiment": "positive", "detail": "Shands and affiliated clinics provide practicum and research settings."},
            {"label": "Policy and epidemiology", "sentiment": "positive", "detail": "Florida-focused public health research on aging, disability, and rural health."},
            {"label": "Funding variability", "sentiment": "mixed", "detail": "Assistantships are competitive and not uniform across PHHP departments."},
            {"label": "Interprofessional training", "sentiment": "positive", "detail": "Collaboration with medicine, nursing, and pharmacy on the Gainesville campus."},
        ],
        "sources": [
            {"label": "U.S. News — Best Public Health Schools", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
            {"label": "UF College of Public Health and Health Professions", "url": "https://phhp.ufl.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uf-journalism-bs": {
        "summary": (
            "UF's College of Journalism and Communications is consistently ranked among the top "
            "undergraduate journalism programs nationally, with strengths in telecommunication, "
            "public relations, and digital media. Students praise the Innovation News Center and "
            "agency-style coursework, though admission to limited-enrollment sequences is competitive."
        ),
        "themes": [
            {"label": "National ranking", "sentiment": "positive", "detail": "U.S. News and ACEJMC accreditation support strong industry recognition."},
            {"label": "Hands-on production", "sentiment": "positive", "detail": "Innovation News Center and WUFT provide broadcast and digital publishing experience."},
            {"label": "Limited enrollment", "sentiment": "caution", "detail": "Some sequences require competitive admission after prerequisite coursework."},
            {"label": "Industry networks", "sentiment": "positive", "detail": "Alumni placement in Florida media markets and national outlets."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Journalism Programs", "url": "https://www.usnews.com/best-colleges/rankings/journalism"},
            {"label": "UF College of Journalism and Communications", "url": "https://www.jou.ufl.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
}
