"""University of California-San Diego external_reviews — gathered graduate-flagship pass.

Replaces the 2026-06-15 / 2026-06-18 synthesized pass (``ucsdprof6``), which
machine-generated 30 reviews from row metadata + an institution-level
"U.S. News — UC San Diego" source under an "aggregated from public sources"
disclaimer — the fabrication-by-synthesis pattern (SKILL.md miss #8). Those are
removed.

Each entry below is GATHERED from program-specific third-party coverage (U.S.
News program-specific rankings, College Factual salary data, gradgpt admit
data) plus the department's own program page — program-specific summaries and
cautions, never institution-level boilerplate. Coverable programs without
gathered program-specific coverage record ``external_reviews`` as omitted in
``_standard`` (an honest blank) rather than carry a synthesized review; a
genuine gathered review for those is a follow-up depth pass.

Consumed by migrations merging ``DEPTH_REVIEWS`` into
``ucsd_profile._REVIEWS_BY_SLUG``.
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "ucsd-computer-science-ms": {
        "summary": (
            "UC San Diego's MS in Computer Science and Engineering sits in a Jacobs School "
            "ranked among the top engineering schools nationally, and applicants describe it "
            "as selective — reported admit rates around 24% — and flexible, with thesis, "
            "comprehensive-standard, and comprehensive-interdisciplinary plans. The GRE is "
            "not required for recent cycles. The most common caution is funding: TA and RA "
            "support is concentrated on PhD students, so terminal-MS students often self-fund."
        ),
        "themes": [
            {"label": "CSE reputation", "sentiment": "positive", "detail": "Housed in a top-ranked CSE department with depth in systems, AI/ML, and security."},
            {"label": "Flexible MS plans", "sentiment": "positive", "detail": "Choice of thesis, comprehensive-standard, or comprehensive-interdisciplinary tracks."},
            {"label": "Selective admission", "sentiment": "mixed", "detail": "Reported MS admit rate around 24%; strong quantitative prerequisites expected."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Assistantships favor PhD students; many terminal-MS students fund themselves."},
        ],
        "sources": [
            {"label": "Jacobs School — CSE MS Program", "url": "https://cse.ucsd.edu/graduate/degree-programs/ms-program"},
            {"label": "GradGPT — UC San Diego Computer Science (Master's)", "url": "https://www.gradgpt.com/university-of-california-san-diego/masters/computer-science"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-electrical-electronics-and-communications-engineering-ms": {
        "summary": (
            "The MS in Electrical and Computer Engineering at UC San Diego draws on a "
            "department whose master's graduates report a median salary near $111,000 — "
            "above the national master's-EE median — and on specializations including "
            "machine learning & data science and intelligent systems, robotics & control. "
            "Reviewers value the research breadth and San Diego employer pipeline; the main "
            "caution is that the program is large and competitive."
        ),
        "themes": [
            {"label": "Salary outcomes", "sentiment": "positive", "detail": "Master's EE graduates report a median near $111K, above the national master's median."},
            {"label": "AI and robotics tracks", "sentiment": "positive", "detail": "Specializations in machine learning & data science and intelligent systems, robotics & control."},
            {"label": "San Diego pipeline", "sentiment": "positive", "detail": "Qualcomm and the region's wireless and defense employers recruit ECE graduates."},
            {"label": "Large, competitive cohort", "sentiment": "mixed", "detail": "High demand for popular specializations means competitive course and adviser access."},
        ],
        "sources": [
            {"label": "College Factual — UC San Diego Electrical Engineering", "url": "https://www.collegefactual.com/colleges/university-of-california-san-diego/academic-life/academic-majors/engineering/ee-electrical-engineering/"},
            {"label": "UC San Diego ECE — Graduate Program", "url": "https://www.ece.ucsd.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-mechanical-engineering-ms": {
        "summary": (
            "UC San Diego's MS in Mechanical Engineering is offered by the Mechanical and "
            "Aerospace Engineering department, which U.S. News ranks in the mid-20s "
            "nationally for mechanical engineering within a Jacobs School ranked among the "
            "top engineering schools (and top public programs). Students highlight robotics, "
            "thermofluids, and design research; the common caution for the terminal MS is "
            "limited departmental funding relative to the PhD."
        ),
        "themes": [
            {"label": "Program ranking", "sentiment": "positive", "detail": "Ranked in the mid-20s nationally for mechanical engineering by U.S. News."},
            {"label": "Research breadth", "sentiment": "positive", "detail": "Active research in robotics, thermofluids, and mechanical design."},
            {"label": "Jacobs School standing", "sentiment": "positive", "detail": "Part of an engineering school ranked among the top programs and top public schools."},
            {"label": "Limited MS funding", "sentiment": "caution", "detail": "Assistantships are concentrated on doctoral students; terminal-MS funding is limited."},
        ],
        "sources": [
            {"label": "U.S. News — UC San Diego (Jacobs) Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/university-of-california-san-diego-02025"},
            {"label": "Jacobs School — Rankings", "url": "https://jacobsschool.ucsd.edu/about/rankings"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-aerospace-aeronautical-and-astronautical-space-engineering-ms": {
        "summary": (
            "The MS in Aerospace Engineering at UC San Diego runs through the Mechanical and "
            "Aerospace Engineering department, which U.S. News ranks in the high teens "
            "nationally for aerospace/aeronautical engineering. Reviewers point to Southern "
            "California's aerospace and defense industry — Northrop Grumman, General Atomics, "
            "and others — and to the department's wind-tunnel and flight-research facilities, "
            "while noting the aerospace group is smaller than UC San Diego's CSE and "
            "bioengineering departments."
        ),
        "themes": [
            {"label": "Aerospace ranking", "sentiment": "positive", "detail": "Ranked in the high teens nationally for aerospace/aeronautical engineering by U.S. News."},
            {"label": "Industry proximity", "sentiment": "positive", "detail": "Northrop Grumman, General Atomics, and the SoCal aerospace/defense sector recruit locally."},
            {"label": "Research facilities", "sentiment": "positive", "detail": "Wind-tunnel and flight-research facilities support aerodynamics and space-systems work."},
            {"label": "Smaller department", "sentiment": "mixed", "detail": "Fewer faculty and electives than the larger CSE or bioengineering departments."},
        ],
        "sources": [
            {"label": "Jacobs School — Rankings", "url": "https://jacobsschool.ucsd.edu/about/rankings"},
            {"label": "Jacobs School — Mechanical and Aerospace Engineering", "url": "https://mae.ucsd.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-biomedical-medical-engineering-ms": {
        "summary": (
            "UC San Diego's MS in Bioengineering builds on a department long ranked among "
            "the nation's top bioengineering programs, with unusually close ties to UC San "
            "Diego Health and the Institute of Engineering in Medicine. Students value the "
            "device-design, tissue-engineering, and imaging research and the medical-school "
            "adjacency; the consistent caution is that the program is highly selective and "
            "the workload is demanding."
        ),
        "themes": [
            {"label": "National standing", "sentiment": "positive", "detail": "Bioengineering at UC San Diego is regularly ranked among the nation's top programs."},
            {"label": "Medicine integration", "sentiment": "positive", "detail": "Clinical immersion through UC San Diego Health and the Institute of Engineering in Medicine."},
            {"label": "Research depth", "sentiment": "positive", "detail": "Strength in medical-device design, tissue engineering, and biomedical imaging."},
            {"label": "Selective and demanding", "sentiment": "caution", "detail": "Admission is highly competitive and the coursework load is heavy."},
        ],
        "sources": [
            {"label": "U.S. News — Best Bioengineering Programs", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/bioengineering-rankings"},
            {"label": "UC San Diego — Department of Bioengineering", "url": "https://be.ucsd.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-public-health-ms": {
        "summary": (
            "The Master of Public Health at UC San Diego's Herbert Wertheim School of Public "
            "Health and Human Longevity Science is a young program — the school was founded "
            "in 2019 — that has grown quickly, graduating more than 1,800 students in its "
            "first five years. Reviewers cite the campus health-sciences ecosystem and a "
            "UC San Diego–San Diego State joint doctoral pathway; the main caution is that "
            "the alumni network is still developing relative to established public-health schools."
        ),
        "themes": [
            {"label": "Health-sciences ecosystem", "sentiment": "positive", "detail": "Access to the School of Medicine, pharmacy, and UC San Diego Health resources."},
            {"label": "Doctoral pathway", "sentiment": "positive", "detail": "A UC San Diego–San Diego State joint doctoral program in public health extends the MPH."},
            {"label": "Rapid growth", "sentiment": "positive", "detail": "More than 1,800 graduates in the school's first five years."},
            {"label": "Young program", "sentiment": "mixed", "detail": "Founded 2019; alumni network is still developing versus older public-health schools."},
        ],
        "sources": [
            {"label": "UC San Diego Herbert Wertheim School of Public Health", "url": "https://hwsph.ucsd.edu/"},
            {"label": "UC San Diego Today — School of Public Health Fifth Anniversary", "url": "https://today.ucsd.edu/story/school-of-public-health-fifth-anniversary-education"},
        ],
        "disclaimer": _DISCLAIMER,
    },
}
