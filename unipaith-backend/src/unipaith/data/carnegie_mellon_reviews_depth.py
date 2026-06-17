"""Carnegie Mellon University external_reviews depth pass — 66 coverable programs.

Depth pass date: 2026-06-15. Consumed by the ``cmuprof4`` migration to merge
``DEPTH_REVIEWS`` into ``carnegie_mellon_profile._REVIEWS_BY_SLUG`` for programs
not covered by the initial eight flagship reviews.
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "cmu-cs-phd": {
        "summary": (
            "Students and academic guides describe CMU's Ph.D. in Computer Science as a "
            "top-tier research doctorate within the nation's #1-ranked CS school, with deep "
            "faculty mentorship across AI, systems, and theory; common cautions are extreme "
            "selectivity, a long time-to-degree, and intense research expectations."
        ),
        "themes": [
            {
                "label": "Elite CS research",
                "sentiment": "positive",
                "detail": (
                    "Doctoral students join leading labs across SCS departments and institutes."
                ),
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": (
                    "Pioneering research groups in AI, robotics, and systems anchor the program."
                ),
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into faculty roles, industry R&D labs, and startups."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with a small incoming cohort.",
            },
            {
                "label": "Research intensity",
                "sentiment": "caution",
                "detail": (
                    "The dissertation path demands sustained, publication-oriented work."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU CSD — Ph.D. overview",
                "url": "https://csd.cmu.edu/academics/doctoral/overview",
            },
            {
                "label": "U.S. News — Best Computer Science Schools",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-science-schools/"
                    "computer-science-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mcds": {
        "summary": (
            "The Master of Computational Data Science is regarded as a practitioner-oriented "
            "SCS master's that blends large-scale data engineering, distributed systems, and "
            "machine learning through team capstones; students praise industry-relevant projects "
            "but note steep systems prerequisites and a demanding project workload."
        ),
        "themes": [
            {
                "label": "Industry capstone",
                "sentiment": "positive",
                "detail": (
                    "Team-based practicum projects mirror real data-engineering deliverables."
                ),
            },
            {
                "label": "Systems + ML blend",
                "sentiment": "positive",
                "detail": (
                    "Curriculum spans distributed computing, storage, and applied ML pipelines."
                ),
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": (
                    "Strong programming and systems background is expected from day one."
                ),
            },
            {
                "label": "Project pace",
                "sentiment": "caution",
                "detail": "Capstone semesters are consistently described as workload-heavy.",
            },
        ],
        "sources": [
            {
                "label": "CMU LTI — MCDS program",
                "url": "https://lti.cmu.edu/academics/masters-programs/mcds.html",
            },
            {
                "label": "Niche — Carnegie Mellon University",
                "url": "https://www.niche.com/colleges/carnegie-mellon-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msle": {
        "summary": (
            "CMU's MS in Learning Engineering (METALS) is highlighted as an interdisciplinary "
            "master's linking HCI, cognitive science, and educational technology design; "
            "students value the project-based curriculum and ed-tech placement, while noting "
            "a niche field footprint and an accelerated schedule."
        ),
        "themes": [
            {
                "label": "Learning science + design",
                "sentiment": "positive",
                "detail": (
                    "Combines HCII design methods with evidence-based learning research."
                ),
            },
            {
                "label": "Project-based curriculum",
                "sentiment": "positive",
                "detail": (
                    "Studio courses produce portfolio-ready educational technology prototypes."
                ),
            },
            {
                "label": "Ed-tech career paths",
                "sentiment": "positive",
                "detail": (
                    "Alumni enter instructional design, learning analytics, and product roles."
                ),
            },
            {
                "label": "Niche specialization",
                "sentiment": "caution",
                "detail": (
                    "Roles concentrate in ed-tech and research rather than general software."
                ),
            },
            {
                "label": "Accelerated timeline",
                "sentiment": "caution",
                "detail": (
                    "The program packs studio and research work into a short master's calendar."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU METALS — Learning Engineering",
                "url": "https://metals.hcii.cmu.edu/",
            },
            {
                "label": "CMU HCII — Academic programs",
                "url": "https://www.hcii.cmu.edu/academics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mse": {
        "summary": (
            "The on-campus Master of Software Engineering is known as a rigorous, cohort-based "
            "professional master's for experienced developers, emphasizing architecture, "
            "quality, and team delivery; praise centers on industry-aligned projects, while "
            "cautions include prerequisite experience requirements and a demanding studio pace."
        ),
        "themes": [
            {
                "label": "Professional cohort model",
                "sentiment": "positive",
                "detail": "Structured for developers with prior industry experience.",
            },
            {
                "label": "Architecture & quality focus",
                "sentiment": "positive",
                "detail": (
                    "Core coursework stresses scalable design, testing, and process."
                ),
            },
            {
                "label": "Studio projects",
                "sentiment": "positive",
                "detail": "Team software deliverables mirror industry development cycles.",
            },
            {
                "label": "Experience gate",
                "sentiment": "caution",
                "detail": (
                    "Applicants without sufficient work experience may find the pace challenging."
                ),
            },
            {
                "label": "Intense schedule",
                "sentiment": "caution",
                "detail": "Studio semesters require long hours on group deliverables.",
            },
        ],
        "sources": [
            {
                "label": "CMU MSE — Applicants",
                "url": "https://mse.s3d.cmu.edu/applicants/mse-as/index.html",
            },
            {
                "label": "GradReports — Carnegie Mellon University",
                "url": "https://www.gradreports.com/colleges/carnegie-mellon-university",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mse-online": {
        "summary": (
            "The online Master of Software Engineering extends CMU's professional software "
            "engineering curriculum to part-time learners, with praise for flexible pacing "
            "and the same architecture-focused core; cautions include limited synchronous "
            "networking and the need to self-manage remote team projects."
        ),
        "themes": [
            {
                "label": "Flexible delivery",
                "sentiment": "positive",
                "detail": "Part-time online format suits working software professionals.",
            },
            {
                "label": "Architecture curriculum",
                "sentiment": "positive",
                "detail": (
                    "Shares the on-campus emphasis on design, quality, and process."
                ),
            },
            {
                "label": "Remote collaboration",
                "sentiment": "mixed",
                "detail": (
                    "Distributed team projects build async skills but reduce in-person bonding."
                ),
            },
            {
                "label": "Self-directed pace",
                "sentiment": "caution",
                "detail": (
                    "Success depends on managing coursework alongside full-time employment."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU MSE — Online program",
                "url": "https://mse.s3d.cmu.edu/applicants/mse-as-online/index.html",
            },
            {
                "label": "CMU Software and Societal Systems Department",
                "url": "https://s3d.cmu.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msit-privacy": {
        "summary": (
            "CMU's MSIT Privacy Engineering track is cited as a pioneering graduate program "
            "in privacy-by-design, blending policy, systems, and software engineering; "
            "students highlight unique career positioning in privacy engineering roles, with "
            "cautions around a specialized job market and technically dense coursework."
        ),
        "themes": [
            {
                "label": "Privacy engineering pioneer",
                "sentiment": "positive",
                "detail": (
                    "Among the first dedicated graduate tracks in privacy engineering."
                ),
            },
            {
                "label": "Policy + systems blend",
                "sentiment": "positive",
                "detail": (
                    "Connects regulation, threat modeling, and implementable controls."
                ),
            },
            {
                "label": "Specialized careers",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter privacy engineering, compliance tech, and security roles."
                ),
            },
            {
                "label": "Niche hiring market",
                "sentiment": "caution",
                "detail": (
                    "Privacy roles are growing but less ubiquitous than general software jobs."
                ),
            },
            {
                "label": "Technical depth",
                "sentiment": "caution",
                "detail": (
                    "Expectations span cryptography basics, systems, and legal frameworks."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU Privacy Engineering — MSIT Privacy",
                "url": "https://privacy.cs.cmu.edu/masters/index.html",
            },
            {
                "label": "CMU News — U.S. News cybersecurity #1",
                "url": (
                    "https://www.cmu.edu/news/stories/archives/2024/september/"
                    "us-news-and-world-report-ranks-carnegie-mellon-university-"
                    "no-1-in-5-categories-21st-among-national"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-se-phd": {
        "summary": (
            "The Ph.D. in Software Engineering at CMU is recognized for empirically grounded "
            "research on software quality, architecture, and human factors in development; "
            "students praise close industry-linked labs, while noting a smaller community than "
            "core CS and a dissertation path oriented toward empirical methods."
        ),
        "themes": [
            {
                "label": "Empirical SE research",
                "sentiment": "positive",
                "detail": (
                    "Doctoral work emphasizes measurable software engineering phenomena."
                ),
            },
            {
                "label": "Industry-linked labs",
                "sentiment": "positive",
                "detail": (
                    "Faculty collaborations connect research to real development practice."
                ),
            },
            {
                "label": "Smaller doctoral community",
                "sentiment": "mixed",
                "detail": "Fewer peers than the main CS Ph.D., but closer faculty access.",
            },
            {
                "label": "Research expectations",
                "sentiment": "caution",
                "detail": (
                    "Dissertation work requires sustained empirical or systems contributions."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU Ph.D. in Software Engineering",
                "url": "https://se-phd.s3d.cmu.edu/",
            },
            {
                "label": "CMU Software and Societal Systems Department",
                "url": "https://s3d.cmu.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-cheme-bs": {
        "summary": (
            "Undergraduate chemical engineering at CMU is described as a rigorous College of "
            "Engineering major with strong foundations in transport, thermodynamics, and process "
            "design plus research access; students praise small upper-level classes and industry "
            "recruiting, while noting a heavy math-science load and competitive grading."
        ),
        "themes": [
            {"label": "Core engineering rigor", "sentiment": "positive", "detail": "Fundamentals in transport, reaction engineering, and process analysis."},
            {"label": "Research opportunities", "sentiment": "positive", "detail": "Undergraduates join labs in energy, materials, and biotechnology."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates enter process engineering, pharma, and energy sectors."},
            {"label": "Heavy workload", "sentiment": "caution", "detail": "Math, chemistry, and lab sequences demand sustained effort."},
            {"label": "Competitive grading", "sentiment": "caution", "detail": "Engineering core courses are consistently described as demanding."},
        ],
        "sources": [
            {"label": "CMU — College of Engineering majors", "url": "https://www.cmu.edu/admission/majors-programs/college-of-engineering"},
            {"label": "Niche — Carnegie Mellon University", "url": "https://www.niche.com/colleges/carnegie-mellon-university/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-civil-bs": {
        "summary": (
            "CMU's undergraduate civil engineering program is noted for quantitative infrastructure "
            "and environmental systems training within a top-ranked engineering college; praise focuses "
            "on design-oriented coursework and faculty research, with cautions about limited elective "
            "capacity and Pittsburgh's smaller local construction market versus coastal hubs."
        ),
        "themes": [
            {"label": "Infrastructure focus", "sentiment": "positive", "detail": "Core covers structures, geotechnics, and transportation systems."},
            {"label": "Design integration", "sentiment": "positive", "detail": "Project-based courses connect analysis to real infrastructure problems."},
            {"label": "Research labs", "sentiment": "positive", "detail": "Students access CEE faculty work in sustainability and smart cities."},
            {"label": "Regional job market", "sentiment": "mixed", "detail": "National recruiting is strong, but local construction hiring is modest."},
            {"label": "Rigorous core", "sentiment": "caution", "detail": "Engineering math and mechanics sequences are workload-intensive."},
        ],
        "sources": [
            {"label": "CMU CEE — Department overview", "url": "https://cee.engineering.cmu.edu/"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-environ-bs": {
        "summary": (
            "Environmental engineering undergraduates at CMU highlight interdisciplinary training "
            "spanning water, air, and sustainability systems within CEE; students value research tied "
            "to climate and infrastructure resilience, while noting overlap with civil coursework and "
            "the need to seek federal or coastal employers for some specialty roles."
        ),
        "themes": [
            {"label": "Sustainability systems", "sentiment": "positive", "detail": "Curriculum addresses water quality, air pollution, and green infrastructure."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Faculty connect environmental engineering to policy and public health."},
            {"label": "CEE integration", "sentiment": "positive", "detail": "Shared department resources with civil engineering design labs."},
            {"label": "Specialty job geography", "sentiment": "caution", "detail": "Some environmental roles cluster in government and coastal markets."},
            {"label": "Technical breadth", "sentiment": "caution", "detail": "Expect chemistry, biology, and engineering fundamentals together."},
        ],
        "sources": [
            {"label": "CMU CEE — Department overview", "url": "https://cee.engineering.cmu.edu/"},
            {"label": "CMU — College of Engineering majors", "url": "https://www.cmu.edu/admission/majors-programs/college-of-engineering"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ece-bs": {
        "summary": (
            "Electrical and computer engineering undergraduates at CMU praise deep coverage of circuits, "
            "signals, and computing systems within a highly ranked ECE department; common themes include "
            "strong robotics and embedded-systems research access, with cautions about a fast-paced core "
            "and large lower-division sections."
        ),
        "themes": [
            {"label": "Circuits & systems depth", "sentiment": "positive", "detail": "Core spans analog, digital, and computer engineering foundations."},
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join labs in robotics, VLSI, and wireless systems."},
            {"label": "Tech placement", "sentiment": "positive", "detail": "Graduates enter hardware, embedded systems, and software roles."},
            {"label": "Pace & workload", "sentiment": "caution", "detail": "The ECE core is consistently described as fast-moving and demanding."},
            {"label": "Large intro sections", "sentiment": "caution", "detail": "Popular major means bigger classes in early required courses."},
        ],
        "sources": [
            {"label": "CMU ECE — Department", "url": "https://www.ece.cmu.edu/"},
            {"label": "Niche — Carnegie Mellon University Academics", "url": "https://www.niche.com/colleges/carnegie-mellon-university/academics/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mse-bs": {
        "summary": (
            "Materials science and engineering undergraduates describe a quantitative major bridging "
            "physics, chemistry, and manufacturing within CMU's MSE department; students highlight "
            "nanotechnology and energy materials research, with cautions about specialized career "
            "paths and lab-intensive scheduling."
        ),
        "themes": [
            {"label": "Materials fundamentals", "sentiment": "positive", "detail": "Training spans structure, properties, processing, and performance."},
            {"label": "Research labs", "sentiment": "positive", "detail": "Faculty work in energy storage, metallurgy, and computational materials."},
            {"label": "Graduate school pipeline", "sentiment": "positive", "detail": "Strong preparation for Ph.D. programs and R&D roles."},
            {"label": "Specialized industry paths", "sentiment": "mixed", "detail": "Roles cluster in manufacturing, semiconductors, and research labs."},
            {"label": "Lab workload", "sentiment": "caution", "detail": "Experimental courses require significant hands-on time."},
        ],
        "sources": [
            {"label": "CMU MSE — Department", "url": "https://mse.engineering.cmu.edu/"},
            {"label": "CMU — College of Engineering majors", "url": "https://www.cmu.edu/admission/majors-programs/college-of-engineering"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-meche-bs": {
        "summary": (
            "Mechanical engineering undergraduates at CMU emphasize rigorous mechanics, thermodynamics, "
            "and design with access to robotics-adjacent labs; praise centers on maker culture and "
            "interdisciplinary projects, while cautions include a demanding core and competition for "
            "popular design electives."
        ),
        "themes": [
            {"label": "Design & mechanics core", "sentiment": "positive", "detail": "Fundamentals in dynamics, thermodynamics, and mechanical design."},
            {"label": "Robotics crossover", "sentiment": "positive", "detail": "MechE connects naturally to CMU's robotics and manufacturing research."},
            {"label": "Project-based learning", "sentiment": "positive", "detail": "Design courses produce tangible prototypes and team deliverables."},
            {"label": "Core intensity", "sentiment": "caution", "detail": "Required sequences are fast-paced with heavy problem sets."},
            {"label": "Elective demand", "sentiment": "caution", "detail": "Popular design and robotics electives can fill quickly."},
        ],
        "sources": [
            {"label": "CMU MechE — Department", "url": "https://www.meche.engineering.cmu.edu/"},
            {"label": "Niche — Carnegie Mellon University", "url": "https://www.niche.com/colleges/carnegie-mellon-university/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-bme-bs": {
        "summary": (
            "Biomedical engineering as an additional major at CMU is praised for bridging engineering "
            "with biology and clinical applications through the BME department; students value "
            "interdisciplinary research and health-tech pathways, with cautions about scheduling as "
            "an additional major and competitive med-device hiring."
        ),
        "themes": [
            {"label": "Bio + engineering blend", "sentiment": "positive", "detail": "Connects physiology, instrumentation, and data-driven health tech."},
            {"label": "Clinical & lab research", "sentiment": "positive", "detail": "Faculty collaborations span medical devices and computational biology."},
            {"label": "Health-tech careers", "sentiment": "positive", "detail": "Graduates enter med-tech, pharma engineering, and graduate health programs."},
            {"label": "Additional major load", "sentiment": "caution", "detail": "Pursued atop a primary major, increasing scheduling complexity."},
            {"label": "Specialized hiring", "sentiment": "caution", "detail": "Med-device roles can be geographically concentrated."},
        ],
        "sources": [
            {"label": "CMU BME — Department", "url": "https://www.cmu.edu/bme/"},
            {"label": "CMU — College of Engineering majors", "url": "https://www.cmu.edu/admission/majors-programs/college-of-engineering"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-ece": {
        "summary": (
            "CMU's MS in Electrical & Computer Engineering is regarded as a flexible, research-rich "
            "master's within a top ECE department, offering depth in circuits, systems, and AI-enabled "
            "hardware; students praise faculty access and strong tech placement, with cautions about "
            "self-directed specialization and a competitive Pittsburgh-to-coastal recruiting path."
        ),
        "themes": [
            {"label": "Flexible specialization", "sentiment": "positive", "detail": "Students tailor coursework across signals, systems, and embedded computing."},
            {"label": "Research depth", "sentiment": "positive", "detail": "Graduate courses connect to robotics, VLSI, and wireless faculty labs."},
            {"label": "Tech placement", "sentiment": "positive", "detail": "Graduates enter semiconductor, robotics, and software-hardware roles."},
            {"label": "Self-directed path", "sentiment": "mixed", "detail": "Breadth requires early focus to build a coherent specialty."},
            {"label": "Recruiting geography", "sentiment": "caution", "detail": "Many hardware roles require outreach beyond Pittsburgh's local market."},
        ],
        "sources": [
            {"label": "CMU ECE — MS program", "url": "https://www.ece.cmu.edu/academics/ms-ece/index.html"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-se-sv": {
        "summary": (
            "The Silicon Valley–based MS in Software Engineering places CMU's professional software "
            "engineering curriculum in the Bay Area, praised for proximity to tech employers and "
            "industry-aligned studio work; cautions include a premium cost of living and a cohort "
            "experience that differs from the Pittsburgh campus."
        ),
        "themes": [
            {"label": "Bay Area location", "sentiment": "positive", "detail": "Studying in Silicon Valley eases networking with tech employers."},
            {"label": "Professional SE curriculum", "sentiment": "positive", "detail": "Shares CMU's architecture, quality, and team-project emphasis."},
            {"label": "Industry studio work", "sentiment": "positive", "detail": "Projects align with software delivery practices in tech firms."},
            {"label": "Cost of living", "sentiment": "caution", "detail": "Bay Area housing costs significantly exceed Pittsburgh."},
            {"label": "Campus experience", "sentiment": "mixed", "detail": "Smaller satellite cohort versus the main Pittsburgh community."},
        ],
        "sources": [
            {"label": "CMU ECE — MS Software Engineering (SV)", "url": "https://www.ece.cmu.edu/academics/ms-se/index.html"},
            {"label": "CMU College of Engineering", "url": "https://engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msaie-ece": {
        "summary": (
            "The MS in Artificial Intelligence Engineering (ECE track) combines CMU's AI strengths "
            "with electrical and computer engineering applications, highlighting embedded ML and "
            "intelligent systems; students value interdisciplinary training, while noting heavy "
            "prerequisites in both AI and hardware domains."
        ),
        "themes": [
            {"label": "AI + hardware integration", "sentiment": "positive", "detail": "Bridges machine learning with circuits, systems, and edge computing."},
            {"label": "CMU AI ecosystem", "sentiment": "positive", "detail": "Access to SCS and engineering faculty working on intelligent systems."},
            {"label": "Industry relevance", "sentiment": "positive", "detail": "Prepares for roles in edge AI, robotics, and smart devices."},
            {"label": "Dual-domain prerequisites", "sentiment": "caution", "detail": "Expectations span ML, programming, and ECE fundamentals."},
            {"label": "Newer program footprint", "sentiment": "mixed", "detail": "Employer familiarity is still growing versus legacy ECE paths."},
        ],
        "sources": [
            {"label": "CMU ECE — MS AI Engineering", "url": "https://www.ece.cmu.edu/academics/ms-ai/index.html"},
            {"label": "CMU News — U.S. News AI #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ece-phd": {
        "summary": (
            "The Ph.D. in Electrical & Computer Engineering at CMU is recognized for pioneering "
            "research in robotics, VLSI, and wireless systems within a top-ranked department; "
            "doctoral students praise faculty mentorship and industry-linked labs, with cautions "
            "about long time-to-degree and intense publication expectations."
        ),
        "themes": [
            {"label": "Research leadership", "sentiment": "positive", "detail": "Faculty lead work in robotics, sensing, and next-generation hardware."},
            {"label": "Industry collaborations", "sentiment": "positive", "detail": "Labs partner with semiconductor and robotics firms."},
            {"label": "Academic placement", "sentiment": "positive", "detail": "Graduates join faculty posts and industrial R&D leadership."},
            {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is competitive with limited funded slots."},
            {"label": "Dissertation demands", "sentiment": "caution", "detail": "Doctoral progress requires sustained research output."},
        ],
        "sources": [
            {"label": "CMU ECE — Ph.D. program", "url": "https://www.ece.cmu.edu/academics/phd-ece/index.html"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-meche": {
        "summary": (
            "The coursework-based MS in Mechanical Engineering at CMU offers a one-year path through "
            "advanced mechanics, thermodynamics, and design electives; students appreciate the "
            "accelerated timeline and engineering rigor, with cautions about limited research "
            "exposure and a short window for recruiting."
        ),
        "themes": [
            {"label": "Accelerated timeline", "sentiment": "positive", "detail": "The coursework track can be completed in about one year."},
            {"label": "Advanced mechanics", "sentiment": "positive", "detail": "Graduate-level depth in dynamics, fluids, and design."},
            {"label": "Engineering rigor", "sentiment": "positive", "detail": "CMU MechE's quantitative culture carries into graduate work."},
            {"label": "Limited research option", "sentiment": "caution", "detail": "Coursework track offers less thesis research than the research MS."},
            {"label": "Compressed recruiting", "sentiment": "caution", "detail": "A one-year calendar leaves less time for internships."},
        ],
        "sources": [
            {"label": "CMU MechE — Coursework MS", "url": "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-meche.html"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-meche-research": {
        "summary": (
            "The research-track MS in Mechanical Engineering pairs graduate coursework with a "
            "faculty-advised thesis, praised for robotics and manufacturing lab access; students "
            "value a stepping stone to Ph.D. programs, while noting thesis timelines can extend "
            "beyond the nominal two-year plan."
        ),
        "themes": [
            {"label": "Thesis research", "sentiment": "positive", "detail": "Students produce an original research contribution with faculty guidance."},
            {"label": "Robotics & manufacturing labs", "sentiment": "positive", "detail": "MechE research connects to CMU's robotics ecosystem."},
            {"label": "Ph.D. pipeline", "sentiment": "positive", "detail": "Strong preparation for doctoral study in mechanical engineering."},
            {"label": "Timeline variability", "sentiment": "caution", "detail": "Thesis completion can extend the planned graduation date."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research support varies by lab and project availability."},
        ],
        "sources": [
            {"label": "CMU MechE — Research MS", "url": "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-research.html"},
            {"label": "CMU MechE — Department", "url": "https://www.meche.engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-meche-advanced": {
        "summary": (
            "The Advanced Study MS in Mechanical Engineering targets practicing engineers seeking "
            "deeper technical breadth without a thesis, with praise for flexible electives and "
            "part-time options; cautions include less research credentialing and self-directed "
            "specialization across MechE subfields."
        ),
        "themes": [
            {"label": "Practitioner-focused", "sentiment": "positive", "detail": "Designed for engineers advancing technical depth mid-career."},
            {"label": "Elective flexibility", "sentiment": "positive", "detail": "Students shape coursework across fluids, heat transfer, and design."},
            {"label": "Part-time friendly", "sentiment": "positive", "detail": "Schedule accommodates working professionals."},
            {"label": "No thesis credential", "sentiment": "mixed", "detail": "Less research output than the research-track MS or Ph.D."},
            {"label": "Self-directed focus", "sentiment": "caution", "detail": "Students must proactively build a coherent specialty area."},
        ],
        "sources": [
            {"label": "CMU MechE — Advanced Study MS", "url": "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-advanced-study.html"},
            {"label": "CMU College of Engineering", "url": "https://engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msaie-meche": {
        "summary": (
            "The MS in AI Engineering (Mechanical Engineering) applies machine learning to design, "
            "control, and manufacturing systems within MechE; students highlight CMU's AI-meets-"
            "physical-systems positioning, with cautions about cross-disciplinary prerequisites "
            "and a still-evolving employer category."
        ),
        "themes": [
            {"label": "AI for physical systems", "sentiment": "positive", "detail": "Connects ML to robotics, control, and advanced manufacturing."},
            {"label": "MechE + SCS crossover", "sentiment": "positive", "detail": "Leverages CMU strengths in robotics and intelligent systems."},
            {"label": "Industry relevance", "sentiment": "positive", "detail": "Prepares for roles in autonomous systems and smart manufacturing."},
            {"label": "Cross-domain prerequisites", "sentiment": "caution", "detail": "Requires comfort in both ML and mechanical engineering fundamentals."},
            {"label": "Emerging job category", "sentiment": "mixed", "detail": "Employer demand is growing but less standardized than core MechE roles."},
        ],
        "sources": [
            {"label": "CMU MechE — MS AI Engineering", "url": "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-artificial-intelligence-engineering.html"},
            {"label": "CMU News — U.S. News AI #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-meche-phd": {
        "summary": (
            "The Ph.D. in Mechanical Engineering at CMU is known for research in robotics, "
            "manufacturing, and biomechanics within a quantitatively rigorous department; "
            "doctoral students praise interdisciplinary lab culture, with cautions about "
            "competitive funding and long dissertation timelines."
        ),
        "themes": [
            {"label": "Robotics research", "sentiment": "positive", "detail": "MechE doctoral work connects deeply to CMU's Robotics Institute."},
            {"label": "Quantitative culture", "sentiment": "positive", "detail": "Research emphasizes modeling, simulation, and experimental validation."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Smaller department enables close advisor relationships."},
            {"label": "Funding variability", "sentiment": "caution", "detail": "RA support depends on grant cycles and lab capacity."},
            {"label": "Time-to-degree", "sentiment": "caution", "detail": "Doctoral completion often spans five or more years."},
        ],
        "sources": [
            {"label": "CMU MechE — Ph.D. program", "url": "https://www.meche.engineering.cmu.edu/education/graduate-programs/phd/index.html"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-cee": {
        "summary": (
            "The coursework MS in Civil & Environmental Engineering at CMU offers applied study "
            "in infrastructure, sustainability, and smart cities; students value quantitative "
            "CEE training and faculty ties to policy research, with cautions about a smaller "
            "graduate cohort and regionally concentrated construction hiring."
        ),
        "themes": [
            {"label": "Infrastructure & sustainability", "sentiment": "positive", "detail": "Coursework spans structures, transportation, and environmental systems."},
            {"label": "Policy-linked research", "sentiment": "positive", "detail": "CEE faculty connect engineering to public infrastructure decisions."},
            {"label": "Quantitative methods", "sentiment": "positive", "detail": "Graduate work emphasizes modeling and data-driven analysis."},
            {"label": "Small cohort", "sentiment": "mixed", "detail": "Close community, but fewer peer specialties than larger programs."},
            {"label": "Regional hiring", "sentiment": "caution", "detail": "Some civil roles require relocation to active construction markets."},
        ],
        "sources": [
            {"label": "CMU CEE — MS program", "url": "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ms-cee.html"},
            {"label": "CMU CEE — Department", "url": "https://cee.engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-cee-research": {
        "summary": (
            "The research-track MS in Civil & Environmental Engineering combines graduate "
            "coursework with a thesis in areas like smart cities and environmental systems; "
            "students praise faculty-led infrastructure research, while noting thesis timelines "
            "and funding can extend the planned two-year path."
        ),
        "themes": [
            {"label": "Thesis research", "sentiment": "positive", "detail": "Students contribute to faculty projects in infrastructure and environment."},
            {"label": "Smart cities focus", "sentiment": "positive", "detail": "CEE research addresses sensing, resilience, and urban systems."},
            {"label": "Ph.D. preparation", "sentiment": "positive", "detail": "Research MS serves as a bridge to doctoral study."},
            {"label": "Timeline extension", "sentiment": "caution", "detail": "Thesis work can push graduation beyond the nominal schedule."},
            {"label": "Funding availability", "sentiment": "caution", "detail": "Research support varies by project and advisor."},
        ],
        "sources": [
            {"label": "CMU CEE — Research MS", "url": "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ms-cee-research.html"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msaie-civil": {
        "summary": (
            "The MS in AI Engineering (Civil Engineering) applies machine learning to "
            "infrastructure monitoring, transportation, and environmental systems; praise "
            "centers on a novel intersection of AI and built-environment engineering, with "
            "cautions about cross-training demands and an emerging employer category."
        ),
        "themes": [
            {"label": "AI for infrastructure", "sentiment": "positive", "detail": "Applies ML to sensing, maintenance, and smart-city systems."},
            {"label": "Interdisciplinary training", "sentiment": "positive", "detail": "Bridges CEE domain knowledge with CMU's AI strengths."},
            {"label": "Future-facing skills", "sentiment": "positive", "detail": "Prepares for data-driven roles in infrastructure and consulting."},
            {"label": "Cross-training load", "sentiment": "caution", "detail": "Requires competence in both ML and civil engineering fundamentals."},
            {"label": "Emerging roles", "sentiment": "mixed", "detail": "Job titles in AI-for-infrastructure are still coalescing."},
        ],
        "sources": [
            {"label": "CMU CEE — AI Engineering MS", "url": "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ai-engineering.html"},
            {"label": "CMU News — U.S. News AI #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-cce": {
        "summary": (
            "The MS in Civil & Computer Engineering merges infrastructure systems with computing "
            "and data methods, praised for preparing students for smart-infrastructure and "
            "construction-tech roles; cautions include a specialized career niche and coursework "
            "spanning two demanding disciplines."
        ),
        "themes": [
            {"label": "Infrastructure + computing", "sentiment": "positive", "detail": "Combines CEE systems knowledge with software and data tools."},
            {"label": "Smart infrastructure", "sentiment": "positive", "detail": "Addresses sensing, BIM, and data-driven asset management."},
            {"label": "Construction tech paths", "sentiment": "positive", "detail": "Graduates enter consulting, tech, and infrastructure analytics roles."},
            {"label": "Dual-discipline load", "sentiment": "caution", "detail": "Curriculum spans civil engineering and computing fundamentals."},
            {"label": "Niche market", "sentiment": "mixed", "detail": "Roles sit at the intersection of construction and tech hiring."},
        ],
        "sources": [
            {"label": "CMU CEE — MS CCE program", "url": "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ms-cce.html"},
            {"label": "CMU CEE — Department", "url": "https://cee.engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-cee-phd": {
        "summary": (
            "The Ph.D. in Civil & Environmental Engineering at CMU emphasizes quantitative "
            "research on infrastructure resilience, environmental systems, and smart cities; "
            "doctoral students value policy-relevant faculty work, with cautions about smaller "
            "department scale and academic-job market competition."
        ),
        "themes": [
            {"label": "Infrastructure research", "sentiment": "positive", "detail": "Doctoral work spans structures, transportation, and environmental systems."},
            {"label": "Policy relevance", "sentiment": "positive", "detail": "Faculty research informs public infrastructure and sustainability decisions."},
            {"label": "Quantitative methods", "sentiment": "positive", "detail": "Dissertations emphasize modeling, sensing, and data analysis."},
            {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller community enables close mentorship but fewer peer subfields."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Faculty hiring in CEE remains competitive nationally."},
        ],
        "sources": [
            {"label": "CMU CEE — Ph.D. programs", "url": "https://cee.engineering.cmu.edu/education/graduate/phd-programs/index.html"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-cheme": {
        "summary": (
            "The applied-study MS in Chemical Engineering at CMU emphasizes process design, "
            "energy, and biotechnology through coursework and projects; students praise "
            "quantitative ChemE training and industry connections, with cautions about a "
            "two-year timeline and limited thesis research compared with the research track."
        ),
        "themes": [
            {"label": "Process engineering depth", "sentiment": "positive", "detail": "Graduate coursework spans transport, thermodynamics, and reaction engineering."},
            {"label": "Energy & biotech focus", "sentiment": "positive", "detail": "Electives connect to CMU ChemE research in sustainable processes."},
            {"label": "Industry orientation", "sentiment": "positive", "detail": "Applied study path aligns with process and R&D industry roles."},
            {"label": "Limited thesis research", "sentiment": "mixed", "detail": "Less research credentialing than the research-oriented MS path."},
            {"label": "Two-year schedule", "sentiment": "caution", "detail": "Course load is concentrated across four semesters."},
        ],
        "sources": [
            {"label": "CMU ChemE — MS programs", "url": "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-and-mche.html"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mche": {
        "summary": (
            "The Master of Chemical Engineering (MChe) is a one-year professional master's for "
            "practicing chemical engineers seeking advanced technical depth; students value the "
            "accelerated format and CMU's quantitative culture, with cautions about a compressed "
            "recruiting calendar and less research exposure."
        ),
        "themes": [
            {"label": "One-year format", "sentiment": "positive", "detail": "Designed for rapid upskilling in advanced chemical engineering topics."},
            {"label": "Practitioner audience", "sentiment": "positive", "detail": "Targets engineers with prior industry experience."},
            {"label": "Quantitative rigor", "sentiment": "positive", "detail": "CMU ChemE's modeling and analysis culture carries into graduate work."},
            {"label": "Compressed timeline", "sentiment": "caution", "detail": "Limited time for internships or extended projects."},
            {"label": "Coursework-only path", "sentiment": "mixed", "detail": "No thesis component for research-oriented career goals."},
        ],
        "sources": [
            {"label": "CMU ChemE — MS and MChe programs", "url": "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-and-mche.html"},
            {"label": "CMU ChemE — Department", "url": "https://www.cheme.engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-cse": {
        "summary": (
            "The MS in Computational Systems Engineering applies modeling and optimization to "
            "complex chemical and energy systems; students highlight CMU's strength in "
            "process modeling and data-driven engineering, with cautions about specialized "
            "career paths and heavy computational prerequisites."
        ),
        "themes": [
            {"label": "Systems modeling", "sentiment": "positive", "detail": "Training in optimization, simulation, and process systems analysis."},
            {"label": "Data-driven engineering", "sentiment": "positive", "detail": "Connects ChemE fundamentals with computational methods."},
            {"label": "Research applications", "sentiment": "positive", "detail": "Faculty work spans energy systems and advanced manufacturing."},
            {"label": "Specialized roles", "sentiment": "mixed", "detail": "Careers cluster in process R&D, energy, and analytics-heavy engineering."},
            {"label": "Computational prerequisites", "sentiment": "caution", "detail": "Expects strong programming and numerical methods background."},
        ],
        "sources": [
            {"label": "CMU ChemE — MS CSE program", "url": "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-cse.html"},
            {"label": "CMU College of Engineering", "url": "https://engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msaie-cheme": {
        "summary": (
            "The MS in AI Engineering (Chemical Engineering) applies machine learning to process "
            "design, materials, and biomanufacturing; praise centers on a cutting-edge intersection "
            "of AI and ChemE, with cautions about dual-domain prerequisites and an evolving job "
            "category in process analytics."
        ),
        "themes": [
            {"label": "AI for processes", "sentiment": "positive", "detail": "Applies ML to reaction engineering, separations, and process control."},
            {"label": "CMU AI ecosystem", "sentiment": "positive", "detail": "Leverages university strengths in ML and computational engineering."},
            {"label": "Industry relevance", "sentiment": "positive", "detail": "Prepares for data-driven roles in pharma, energy, and manufacturing."},
            {"label": "Cross-domain load", "sentiment": "caution", "detail": "Requires competence in both ML and chemical engineering fundamentals."},
            {"label": "Emerging roles", "sentiment": "mixed", "detail": "Process-AI job titles are still maturing in industry."},
        ],
        "sources": [
            {"label": "CMU ChemE — AI Engineering MS", "url": "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/aie-che.html"},
            {"label": "CMU News — U.S. News AI #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-btpe": {
        "summary": (
            "The MS in Biotechnology & Pharmaceutical Engineering at CMU combines ChemE "
            "fundamentals with bioprocess and drug-manufacturing training; students praise "
            "industry-aligned coursework and Pittsburgh's biotech cluster, with cautions about "
            "a specialized pharma hiring market and lab-intensive scheduling."
        ),
        "themes": [
            {"label": "Bioprocess engineering", "sentiment": "positive", "detail": "Covers cell culture, downstream processing, and GMP concepts."},
            {"label": "Pharma industry alignment", "sentiment": "positive", "detail": "Curriculum maps to biologics and pharmaceutical manufacturing roles."},
            {"label": "Regional biotech", "sentiment": "positive", "detail": "Pittsburgh hosts growing life-sciences and med-tech employers."},
            {"label": "Specialized hiring", "sentiment": "caution", "detail": "Roles concentrate in pharma hubs beyond Pittsburgh."},
            {"label": "Lab intensity", "sentiment": "caution", "detail": "Experimental coursework demands significant hands-on time."},
        ],
        "sources": [
            {"label": "CMU ChemE — MS BTPE program", "url": "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-btpe.html"},
            {"label": "CMU ChemE — Department", "url": "https://www.cheme.engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-cheme-phd": {
        "summary": (
            "The Ph.D. in Chemical Engineering at CMU is recognized for research in energy, "
            "biotechnology, and computational process systems; doctoral students praise "
            "quantitative faculty mentorship, with cautions about competitive funding and "
            "long dissertation timelines typical of top engineering Ph.D. programs."
        ),
        "themes": [
            {"label": "Energy & biotech research", "sentiment": "positive", "detail": "Faculty lead work in sustainable processes and biomanufacturing."},
            {"label": "Computational modeling", "sentiment": "positive", "detail": "Strong emphasis on simulation and data-driven process design."},
            {"label": "Industry & academia placement", "sentiment": "positive", "detail": "Graduates enter R&D leadership and faculty roles."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "RA support depends on grant availability and advisor."},
            {"label": "Time-to-degree", "sentiment": "caution", "detail": "Doctoral completion commonly spans five or more years."},
        ],
        "sources": [
            {"label": "CMU ChemE — Ph.D. program", "url": "https://www.cheme.engineering.cmu.edu/education/graduate-programs/phd/index.html"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-matsci": {
        "summary": (
            "The coursework MS in Materials Science & Engineering at CMU offers advanced study "
            "in structure-property relationships and manufacturing within a year; students "
            "value quantitative MSE training and energy-materials research access, with "
            "cautions about specialized industry paths and a short recruiting window."
        ),
        "themes": [
            {"label": "Materials fundamentals", "sentiment": "positive", "detail": "Graduate depth in thermodynamics, kinetics, and characterization."},
            {"label": "Energy materials", "sentiment": "positive", "detail": "Faculty research spans batteries, metallurgy, and nanomaterials."},
            {"label": "Accelerated timeline", "sentiment": "positive", "detail": "Coursework track can be completed in about one year."},
            {"label": "Specialized careers", "sentiment": "mixed", "detail": "Roles cluster in semiconductors, energy, and R&D labs."},
            {"label": "Short recruiting window", "sentiment": "caution", "detail": "One-year path leaves limited time for internships."},
        ],
        "sources": [
            {"label": "CMU MSE — Materials Engineering MS", "url": "https://mse.engineering.cmu.edu/education/graduate/masters-programs/materials-engineering.html"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-cmse": {
        "summary": (
            "The MS in Computational Materials Science & Engineering combines materials "
            "fundamentals with simulation and data methods; students highlight CMU's strength "
            "in computational materials research, with cautions about heavy programming "
            "prerequisites and niche roles at the materials-computing intersection."
        ),
        "themes": [
            {"label": "Computational materials", "sentiment": "positive", "detail": "Training in simulation, ML, and multiscale materials modeling."},
            {"label": "Research integration", "sentiment": "positive", "detail": "Connects to MSE faculty work in energy and advanced manufacturing."},
            {"label": "Industry relevance", "sentiment": "positive", "detail": "Prepares for R&D roles in semiconductors and energy storage."},
            {"label": "Programming prerequisites", "sentiment": "caution", "detail": "Expects strong coding and numerical methods background."},
            {"label": "Niche intersection", "sentiment": "mixed", "detail": "Job titles at the materials-computing boundary are specialized."},
        ],
        "sources": [
            {"label": "CMU MSE — Computational MS", "url": "https://mse.engineering.cmu.edu/education/graduate/masters-programs/ms-computational-materials-science-engineering.html"},
            {"label": "CMU MSE — Department", "url": "https://mse.engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-matsci-phd": {
        "summary": (
            "The Ph.D. in Materials Science & Engineering at CMU is known for research in "
            "energy storage, metallurgy, and computational materials; doctoral students praise "
            "close faculty mentorship in a smaller department, with cautions about funding "
            "cycles and competitive academic hiring."
        ),
        "themes": [
            {"label": "Energy & nanomaterials", "sentiment": "positive", "detail": "Faculty lead work in batteries, alloys, and advanced manufacturing."},
            {"label": "Computational methods", "sentiment": "positive", "detail": "Strong integration of simulation and data in materials research."},
            {"label": "Close mentorship", "sentiment": "positive", "detail": "Smaller department enables direct advisor relationships."},
            {"label": "Funding variability", "sentiment": "caution", "detail": "RA support depends on grant cycles and lab capacity."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Materials-science faculty hiring remains competitive."},
        ],
        "sources": [
            {"label": "CMU MSE — Doctoral program", "url": "https://mse.engineering.cmu.edu/education/graduate/doctoral-program/index.html"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-bme": {
        "summary": (
            "The research-track MS in Biomedical Engineering at CMU pairs thesis work with "
            "graduate coursework in medical devices and computational biology; students praise "
            "interdisciplinary labs bridging engineering and medicine, with cautions about "
            "thesis timelines and competitive med-tech hiring."
        ),
        "themes": [
            {"label": "Thesis research", "sentiment": "positive", "detail": "Students produce original work in medical devices or bioengineering."},
            {"label": "Interdisciplinary labs", "sentiment": "positive", "detail": "BME connects engineering with clinical and biological collaborators."},
            {"label": "Ph.D. pipeline", "sentiment": "positive", "detail": "Research MS prepares for doctoral study and R&D roles."},
            {"label": "Thesis timeline", "sentiment": "caution", "detail": "Research completion can extend the planned graduation date."},
            {"label": "Med-tech hiring", "sentiment": "caution", "detail": "Industry roles can be geographically concentrated."},
        ],
        "sources": [
            {"label": "CMU BME — MS program", "url": "https://www.cmu.edu/bme/Academics/graduate-programs/ms_program.html"},
            {"label": "CMU BME — Department", "url": "https://www.cmu.edu/bme/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-bme-applied": {
        "summary": (
            "The applied-study MS in Biomedical Engineering at CMU emphasizes coursework in "
            "medical devices, imaging, and bioengineering without a thesis; students value "
            "flexible electives and industry-oriented training, with cautions about less "
            "research credentialing and self-directed specialization."
        ),
        "themes": [
            {"label": "Applied bioengineering", "sentiment": "positive", "detail": "Coursework spans medical devices, imaging, and computational biology."},
            {"label": "Elective flexibility", "sentiment": "positive", "detail": "Students shape study across BME subdisciplines."},
            {"label": "Industry orientation", "sentiment": "positive", "detail": "Prepares for med-tech, pharma, and health-analytics roles."},
            {"label": "No thesis output", "sentiment": "mixed", "detail": "Less research credentialing than the research-track MS."},
            {"label": "Self-directed focus", "sentiment": "caution", "detail": "Students must proactively build a coherent specialty."},
        ],
        "sources": [
            {"label": "CMU BME — MS program", "url": "https://www.cmu.edu/bme/Academics/graduate-programs/ms_program.html"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-bme-phd": {
        "summary": (
            "The Ph.D. in Biomedical Engineering at CMU emphasizes interdisciplinary research "
            "in neural engineering, medical robotics, and computational biology; doctoral "
            "students praise CMU's health-tech ecosystem, with cautions about cross-college "
            "coordination and competitive funding."
        ),
        "themes": [
            {"label": "Neural & medical robotics", "sentiment": "positive", "detail": "Faculty research spans neural interfaces and surgical systems."},
            {"label": "Interdisciplinary culture", "sentiment": "positive", "detail": "Collaborations span engineering, computer science, and clinical partners."},
            {"label": "Health-tech placement", "sentiment": "positive", "detail": "Graduates enter academia, med-tech R&D, and startups."},
            {"label": "Cross-college coordination", "sentiment": "mixed", "detail": "Advisors and coursework may span multiple CMU units."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "RA support varies by lab and grant availability."},
        ],
        "sources": [
            {"label": "CMU BME — Ph.D. program", "url": "https://www.cmu.edu/bme/Academics/graduate-programs/phd_program.html"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-epp": {
        "summary": (
            "The MS in Engineering & Public Policy at CMU is uniquely positioned at the "
            "intersection of technical analysis and policy decision-making; students praise "
            "quantitative policy methods and faculty ties to energy and technology regulation, "
            "with cautions about niche career paths in think tanks and government."
        ),
        "themes": [
            {"label": "Policy + engineering", "sentiment": "positive", "detail": "Combines technical analysis with regulatory and economic frameworks."},
            {"label": "Quantitative methods", "sentiment": "positive", "detail": "Training in decision analysis, risk, and energy systems modeling."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": "EPP faculty research informs energy, climate, and tech policy."},
            {"label": "Niche career paths", "sentiment": "mixed", "detail": "Roles cluster in policy analysis, consulting, and government."},
            {"label": "DC recruiting", "sentiment": "caution", "detail": "Many policy roles require relocation to Washington or state capitals."},
        ],
        "sources": [
            {"label": "CMU EPP — MS program", "url": "https://epp.engineering.cmu.edu/education/graduate/masters-programs/ms-in-epp/index.html"},
            {"label": "CMU EPP — Department", "url": "https://epp.engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-epp-phd": {
        "summary": (
            "The Ph.D. in Engineering & Public Policy at CMU produces scholars who combine "
            "rigorous technical analysis with policy research on energy, climate, and "
            "technology governance; praise centers on interdisciplinary faculty, with "
            "cautions about a small academic job market in policy-focused engineering."
        ),
        "themes": [
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Dissertations bridge engineering methods and public policy questions."},
            {"label": "Energy & climate focus", "sentiment": "positive", "detail": "Faculty lead work on decarbonization and technology regulation."},
            {"label": "Think tank & academia paths", "sentiment": "positive", "detail": "Graduates enter policy research, consulting, and faculty roles."},
            {"label": "Small field", "sentiment": "caution", "detail": "Academic hiring in engineering-policy remains limited nationally."},
            {"label": "Cross-unit coursework", "sentiment": "mixed", "detail": "Doctoral training spans engineering, economics, and social science."},
        ],
        "sources": [
            {"label": "CMU EPP — Ph.D. program", "url": "https://epp.engineering.cmu.edu/education/graduate/phd-program/index.html"},
            {"label": "U.S. News — CMU Engineering", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/carnegie-mellon-university-020957"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msaie-is": {
        "summary": (
            "The MS in AI Engineering (Information Security) at CMU's Information Networking "
            "Institute applies machine learning to cybersecurity and secure systems; students "
            "highlight CMU's #1-ranked cybersecurity pedigree, with cautions about dual "
            "prerequisites in AI and security engineering."
        ),
        "themes": [
            {"label": "AI for security", "sentiment": "positive", "detail": "Applies ML to threat detection, privacy, and secure system design."},
            {"label": "CMU security pedigree", "sentiment": "positive", "detail": "INI builds on CMU's leading cybersecurity research ecosystem."},
            {"label": "Industry demand", "sentiment": "positive", "detail": "Graduates enter security engineering and AI-security roles."},
            {"label": "Dual-domain load", "sentiment": "caution", "detail": "Requires competence in both ML and information security fundamentals."},
            {"label": "Fast-moving field", "sentiment": "mixed", "detail": "Curriculum must keep pace with evolving AI and threat landscapes."},
        ],
        "sources": [
            {"label": "CMU INI — MS AIE-IS program", "url": "https://www.cmu.edu/ini/academics/msaie-is/index.html"},
            {"label": "CMU News — U.S. News cybersecurity #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msmite": {
        "summary": (
            "The bicoastal MS in Mobile & IoT Engineering at CMU's INI combines Pittsburgh "
            "coursework with a Silicon Valley experience, praised for embedded-systems depth "
            "and Bay Area networking; cautions include high living costs and a demanding "
            "bicoastal travel schedule."
        ),
        "themes": [
            {"label": "Bicoastal format", "sentiment": "positive", "detail": "Pittsburgh foundations plus Silicon Valley industry exposure."},
            {"label": "Embedded & IoT depth", "sentiment": "positive", "detail": "Training in mobile systems, connectivity, and edge computing."},
            {"label": "Industry networking", "sentiment": "positive", "detail": "Bay Area term eases connections with tech employers."},
            {"label": "Travel demands", "sentiment": "caution", "detail": "Bicoastal structure requires relocation between campuses."},
            {"label": "Bay Area costs", "sentiment": "caution", "detail": "Silicon Valley housing significantly exceeds Pittsburgh."},
        ],
        "sources": [
            {"label": "CMU INI — Bicoastal programs", "url": "https://www.cmu.edu/ini/academics/bicoastal/index.html"},
            {"label": "CMU Information Networking Institute", "url": "https://www.cmu.edu/ini/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-etim": {
        "summary": (
            "The MS in Engineering & Technology Innovation Management at CMU bridges technical "
            "engineering with product and venture leadership; students praise the "
            "entrepreneurship-focused curriculum and Pittsburgh startup ecosystem, with "
            "cautions about a one-year pace and self-directed career positioning."
        ),
        "themes": [
            {"label": "Innovation management", "sentiment": "positive", "detail": "Combines engineering depth with product and venture strategy."},
            {"label": "Entrepreneurship focus", "sentiment": "positive", "detail": "Coursework covers venture creation, IP, and go-to-market planning."},
            {"label": "Interdisciplinary cohort", "sentiment": "positive", "detail": "Students from engineering and business backgrounds collaborate."},
            {"label": "One-year intensity", "sentiment": "caution", "detail": "The accelerated calendar packs coursework and projects tightly."},
            {"label": "Self-directed outcomes", "sentiment": "mixed", "detail": "Career paths vary widely across startups, PM, and consulting."},
        ],
        "sources": [
            {"label": "CMU ETIM — MS program", "url": "https://engineering.cmu.edu/etim/programs/ms-etim.html"},
            {"label": "CMU College of Engineering", "url": "https://engineering.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-africa-msece": {
        "summary": (
            "CMU-Africa's MS in Electrical & Computer Engineering in Kigali is praised for "
            "bringing CMU engineering rigor to sub-Saharan Africa with full scholarships for "
            "many students; cautions include a developing local tech market and distance from "
            "Pittsburgh's main campus resources."
        ),
        "themes": [
            {"label": "CMU engineering in Africa", "sentiment": "positive", "detail": "Delivers ECE graduate training at CMU's Kigali campus."},
            {"label": "Scholarship support", "sentiment": "positive", "detail": "Many students receive funding covering tuition and living costs."},
            {"label": "Regional impact", "sentiment": "positive", "detail": "Graduates contribute to Africa's growing tech and telecom sectors."},
            {"label": "Local job market", "sentiment": "mixed", "detail": "Tech hiring is growing but less dense than US coastal hubs."},
            {"label": "Campus resources", "sentiment": "caution", "detail": "Facilities and alumni network differ from the Pittsburgh main campus."},
        ],
        "sources": [
            {"label": "CMU-Africa — MSECE program", "url": "https://www.africa.engineering.cmu.edu/programs/msece/index.html"},
            {"label": "CMU-Africa — About", "url": "https://www.africa.engineering.cmu.edu/about/index.html"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-africa-mseai": {
        "summary": (
            "CMU-Africa's MS in Engineering Artificial Intelligence applies CMU's AI strengths "
            "to African development challenges in Kigali; students highlight applied AI "
            "training and scholarship support, with cautions about infrastructure constraints "
            "and an emerging regional AI job market."
        ),
        "themes": [
            {"label": "Applied AI for Africa", "sentiment": "positive", "detail": "Focuses on AI solutions for regional development and industry needs."},
            {"label": "CMU AI curriculum", "sentiment": "positive", "detail": "Leverages CMU's top-ranked AI research and teaching."},
            {"label": "Scholarship access", "sentiment": "positive", "detail": "Funding support enables diverse cohorts across the continent."},
            {"label": "Regional AI market", "sentiment": "mixed", "detail": "AI roles in Africa are growing but still maturing."},
            {"label": "Infrastructure constraints", "sentiment": "caution", "detail": "Compute and industry partnership resources differ from Pittsburgh."},
        ],
        "sources": [
            {"label": "CMU-Africa — MSEAI program", "url": "https://www.africa.engineering.cmu.edu/programs/mseai.html"},
            {"label": "CMU News — U.S. News AI #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-compfin-bs": {
        "summary": (
            "CMU's undergraduate computational finance major in the Mellon College of Science "
            "is widely regarded as a premier quant-finance pipeline, blending math, statistics, "
            "and finance with the MSCF ecosystem; students praise rigorous preparation for "
            "quant roles, with cautions about intense coursework and cyclical finance hiring."
        ),
        "themes": [
            {"label": "Quant finance pipeline", "sentiment": "positive", "detail": "Undergraduate training connects to CMU's renowned MSCF program."},
            {"label": "Math + finance rigor", "sentiment": "positive", "detail": "Curriculum spans stochastic calculus, programming, and markets."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates enter trading, risk, and asset-management roles."},
            {"label": "Intense workload", "sentiment": "caution", "detail": "Quantitative course load is consistently described as demanding."},
            {"label": "Cyclical hiring", "sentiment": "caution", "detail": "Finance recruiting varies with market conditions."},
        ],
        "sources": [
            {"label": "CMU — Mellon College of Science majors", "url": "https://www.cmu.edu/admission/majors-programs/mellon-college-of-science"},
            {"label": "CMU MSCF program", "url": "https://www.cmu.edu/mscf/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-ms-das": {
        "summary": (
            "The MS in Data Analytics for Science at CMU trains scientists in statistical and "
            "computational methods for research data; students value cross-disciplinary "
            "training bridging MCS sciences and data methods, with cautions about a "
            "specialized academic and R&D career niche."
        ),
        "themes": [
            {"label": "Science-focused analytics", "sentiment": "positive", "detail": "Tailored for researchers handling large scientific datasets."},
            {"label": "Statistical depth", "sentiment": "positive", "detail": "Training in inference, modeling, and reproducible analysis."},
            {"label": "Cross-disciplinary access", "sentiment": "positive", "detail": "Connects to CMU faculty across physics, biology, and chemistry."},
            {"label": "Academic career niche", "sentiment": "mixed", "detail": "Many graduates pursue research-support and Ph.D. paths."},
            {"label": "Specialized roles", "sentiment": "caution", "detail": "Industry titles for science analytics are less standardized."},
        ],
        "sources": [
            {"label": "CMU MCS — MS Data Analytics for Science", "url": "https://www.cmu.edu/mcs/academics/grad/ms-data-analytics"},
            {"label": "CMU Mellon College of Science", "url": "https://www.cmu.edu/mcs/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-econ-bs": {
        "summary": (
            "Undergraduate economics at CMU's Dietrich College is praised for quantitative, "
            "research-oriented training influenced by behavioral and decision-science "
            "faculty; students value analytical rigor and grad-school preparation, with "
            "cautions about large introductory sections and less finance recruiting than "
            "dedicated business schools."
        ),
        "themes": [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Math-intensive curriculum prepares for grad school and analytics."},
            {"label": "Research orientation", "sentiment": "positive", "detail": "Faculty ties to behavioral economics and decision science."},
            {"label": "Grad school pipeline", "sentiment": "positive", "detail": "Strong preparation for economics and public-policy Ph.D. programs."},
            {"label": "Large intro courses", "sentiment": "mixed", "detail": "Popular major means bigger sections in early coursework."},
            {"label": "Finance recruiting", "sentiment": "caution", "detail": "Less dedicated banking pipeline than standalone business schools."},
        ],
        "sources": [
            {"label": "CMU — Dietrich College majors", "url": "https://www.cmu.edu/admission/majors-programs/dietrich-college-of-humanities-social-sciences"},
            {"label": "Niche — Carnegie Mellon University Academics", "url": "https://www.niche.com/colleges/carnegie-mellon-university/academics/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mads": {
        "summary": (
            "The MS in Applied Data Science at CMU's Statistics & Data Science department "
            "is a nine-month intensive blending statistics, ML, and domain projects; students "
            "praise rigorous analytics training and CMU's data-science reputation, with "
            "cautions about a compressed timeline and steep statistical prerequisites."
        ),
        "themes": [
            {"label": "Intensive analytics", "sentiment": "positive", "detail": "Nine-month program covers statistics, ML, and applied projects."},
            {"label": "CMU data-science pedigree", "sentiment": "positive", "detail": "Housed in Statistics & Data Science with cross-campus access."},
            {"label": "Project-based learning", "sentiment": "positive", "detail": "Capstone work applies methods to real datasets."},
            {"label": "Compressed schedule", "sentiment": "caution", "detail": "The short calendar demands sustained high workload."},
            {"label": "Statistical prerequisites", "sentiment": "caution", "detail": "Strong math and statistics background is expected."},
        ],
        "sources": [
            {"label": "CMU Statistics & Data Science — MADS", "url": "https://www.cmu.edu/dietrich/statistics-datascience/academics/mads/index.html"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-barch": {
        "summary": (
            "CMU's undergraduate architecture program in the College of Fine Arts is noted for "
            "design rigor, computational design integration, and a five-year professional "
            "curriculum; students praise studio culture and interdisciplinary tech crossover, "
            "with cautions about demanding studio hours and a competitive portfolio culture."
        ),
        "themes": [
            {"label": "Design studio culture", "sentiment": "positive", "detail": "Intensive studio sequence builds design thinking and representation skills."},
            {"label": "Computational design", "sentiment": "positive", "detail": "CMU's tech culture integrates digital fabrication and parametric tools."},
            {"label": "Five-year professional path", "sentiment": "positive", "detail": "Extended curriculum prepares for NAAB-accredited professional practice."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Long hours on design projects are a consistent theme."},
            {"label": "Portfolio pressure", "sentiment": "caution", "detail": "Critique-driven culture can feel intensely competitive."},
        ],
        "sources": [
            {"label": "CMU — College of Fine Arts majors", "url": "https://www.cmu.edu/admission/majors-programs/college-of-fine-arts"},
            {"label": "CMU School of Architecture", "url": "https://www.architecture.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-march": {
        "summary": (
            "The Master of Architecture at CMU emphasizes design research, sustainability, "
            "and computational methods within a NAAB-accredited program; students value "
            "small cohorts and tech-forward studios, with cautions about architecture "
            "job-market cycles and intensive thesis or terminal-project demands."
        ),
        "themes": [
            {"label": "Design research", "sentiment": "positive", "detail": "Graduate studios explore sustainability, urbanism, and advanced fabrication."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Close faculty mentorship in studio and seminar settings."},
            {"label": "Computational methods", "sentiment": "positive", "detail": "Integrates digital design tools distinctive to CMU's culture."},
            {"label": "Job market cycles", "sentiment": "caution", "detail": "Architecture hiring varies with construction and development cycles."},
            {"label": "Thesis intensity", "sentiment": "caution", "detail": "Terminal design projects require sustained studio commitment."},
        ],
        "sources": [
            {"label": "CMU School of Architecture — Graduate programs", "url": "https://www.architecture.cmu.edu/graduate-programs"},
            {"label": "Niche — Carnegie Mellon University", "url": "https://www.niche.com/colleges/carnegie-mellon-university/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-arch-phd": {
        "summary": (
            "The Ph.D. in Architecture at CMU focuses on design research, building science, "
            "and computational methods rather than professional practice; doctoral students "
            "praise interdisciplinary faculty, with cautions about a small academic job market "
            "and the need to self-define research at the architecture-technology intersection."
        ),
        "themes": [
            {"label": "Design research focus", "sentiment": "positive", "detail": "Doctoral work emphasizes building performance, urban systems, and design theory."},
            {"label": "Interdisciplinary faculty", "sentiment": "positive", "detail": "Collaborations span engineering, computer science, and sustainability."},
            {"label": "Computational building science", "sentiment": "positive", "detail": "Research integrates simulation, sensing, and performance diagnostics."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Architecture faculty hiring is limited and competitive."},
            {"label": "Self-defined research", "sentiment": "mixed", "detail": "Students must carve a niche at the design-technology boundary."},
        ],
        "sources": [
            {"label": "CMU School of Architecture — Graduate programs", "url": "https://www.architecture.cmu.edu/graduate-programs"},
            {"label": "CMU School of Architecture", "url": "https://www.architecture.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-art-mfa": {
        "summary": (
            "The MFA in Art at CMU's School of Art is praised for interdisciplinary studio "
            "practice, critical discourse, and access to digital fabrication; students value "
            "small cohorts and conceptual rigor, with cautions about limited institutional "
            "resources versus larger art schools and competitive academic-art hiring."
        ),
        "themes": [
            {"label": "Interdisciplinary studio", "sentiment": "positive", "detail": "Students work across media with critical and conceptual emphasis."},
            {"label": "Digital fabrication access", "sentiment": "positive", "detail": "CMU's maker culture supports experimental art production."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Close faculty mentorship in studio and critique settings."},
            {"label": "Resource scale", "sentiment": "mixed", "detail": "Facilities differ from larger dedicated art-school campuses."},
            {"label": "Academic art market", "sentiment": "caution", "detail": "Teaching-artist and gallery careers remain competitive."},
        ],
        "sources": [
            {"label": "CMU School of Art — MFA program", "url": "https://art.cmu.edu/mfa/"},
            {"label": "CMU College of Fine Arts", "url": "https://www.cmu.edu/cfa/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mdes": {
        "summary": (
            "The Master of Design in Design for Interactions at CMU is widely cited as a "
            "leading graduate design program bridging interaction design, service design, and "
            "research; students praise studio-based learning and industry placement, with "
            "cautions about an intense two-year schedule and high portfolio expectations."
        ),
        "themes": [
            {"label": "Interaction design leadership", "sentiment": "positive", "detail": "Among the most recognized graduate interaction-design programs."},
            {"label": "Studio-based learning", "sentiment": "positive", "detail": "Project-driven curriculum produces portfolio-ready work."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Alumni enter UX, product design, and design-research roles at major firms."},
            {"label": "Intense schedule", "sentiment": "caution", "detail": "Two-year studio calendar is consistently described as demanding."},
            {"label": "Portfolio expectations", "sentiment": "caution", "detail": "Admission and progression require strong design portfolios."},
        ],
        "sources": [
            {"label": "CMU School of Design — MDes program", "url": "https://design.cmu.edu/about-our-programs/masters-degrees/master-design-design-interactions"},
            {"label": "Animation Career Review — Top Graduate UX/HCI Programs", "url": "https://www.animationcareerreview.com/articles/top-10-private-graduate-uxuihci-schools-and-colleges-us-2025-rankings"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-drama-mfa-directing": {
        "summary": (
            "The MFA in Directing at CMU's School of Drama is regarded as a highly selective "
            "professional training program with strong ties to regional and national theatre; "
            "students praise rigorous rehearsal culture and faculty mentorship, with cautions "
            "about intense schedules and competitive theatre-industry hiring."
        ),
        "themes": [
            {"label": "Professional training", "sentiment": "positive", "detail": "Conservatory-style directing training with production experience."},
            {"label": "Faculty practitioners", "sentiment": "positive", "detail": "Working directors and dramaturgs guide studio and production work."},
            {"label": "Industry connections", "sentiment": "positive", "detail": "Alumni work in regional theatre, TV, and commercial directing."},
            {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is highly competitive with tiny cohorts."},
            {"label": "Industry hiring", "sentiment": "caution", "detail": "Theatre and media directing careers remain competitive nationally."},
        ],
        "sources": [
            {"label": "CMU School of Drama — Graduate programs", "url": "https://drama.cmu.edu/programs/graduate-programs/"},
            {"label": "Niche — Carnegie Mellon University", "url": "https://www.niche.com/colleges/carnegie-mellon-university/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-drama-mfa-writing": {
        "summary": (
            "The MFA in Dramatic Writing at CMU's School of Drama trains playwrights and "
            "screenwriters through workshop-intensive coursework and production opportunities; "
            "students value small workshops and Pittsburgh's theatre scene, with cautions "
            "about competitive entertainment-industry placement and demanding revision cycles."
        ),
        "themes": [
            {"label": "Workshop-intensive training", "sentiment": "positive", "detail": "Small workshops provide detailed feedback on scripts and structure."},
            {"label": "Production opportunities", "sentiment": "positive", "detail": "Writers see work developed through School of Drama productions."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Working playwrights and screenwriters guide craft development."},
            {"label": "Entertainment hiring", "sentiment": "caution", "detail": "TV, film, and theatre writing careers are highly competitive."},
            {"label": "Revision demands", "sentiment": "caution", "detail": "Workshop culture requires sustained rewriting under tight deadlines."},
        ],
        "sources": [
            {"label": "CMU School of Drama — Graduate programs", "url": "https://drama.cmu.edu/programs/graduate-programs/"},
            {"label": "CMU College of Fine Arts", "url": "https://www.cmu.edu/cfa/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-drama-mfa-design": {
        "summary": (
            "The MFA in Design (Drama) at CMU trains scenic, costume, lighting, and "
            "sound designers through production-centered coursework; students praise "
            "hands-on theatre experience and faculty practitioners, with cautions about "
            "long production hours and competitive entertainment-design hiring."
        ),
        "themes": [
            {"label": "Production-centered training", "sentiment": "positive", "detail": "Designers build portfolios through realized theatre productions."},
            {"label": "Practitioner faculty", "sentiment": "positive", "detail": "Working designers mentor across scenic, costume, and lighting."},
            {"label": "Portfolio development", "sentiment": "positive", "detail": "Graduates enter theatre, opera, and entertainment design roles."},
            {"label": "Production hours", "sentiment": "caution", "detail": "Show schedules demand long tech and performance weeks."},
            {"label": "Competitive hiring", "sentiment": "caution", "detail": "Theatre and film design roles are limited nationally."},
        ],
        "sources": [
            {"label": "CMU School of Drama — Graduate programs", "url": "https://drama.cmu.edu/programs/graduate-programs/"},
            {"label": "CMU School of Drama", "url": "https://drama.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msaecm": {
        "summary": (
            "The MS in Architecture-Engineering-Construction Management at CMU bridges design, "
            "building science, and project delivery; students praise CMU's building-performance "
            "research legacy and industry-facing curriculum, with cautions about a specialized "
            "AEC career niche and technical breadth across three domains."
        ),
        "themes": [
            {"label": "AEC integration", "sentiment": "positive", "detail": "Combines architecture, engineering, and construction management methods."},
            {"label": "Building performance", "sentiment": "positive", "detail": "Leverages CMU's research in diagnostics and sustainable buildings."},
            {"label": "Industry relevance", "sentiment": "positive", "detail": "Graduates enter construction tech, consulting, and project management."},
            {"label": "Triple-domain breadth", "sentiment": "caution", "detail": "Curriculum spans design, engineering, and management fundamentals."},
            {"label": "Specialized niche", "sentiment": "mixed", "detail": "Roles sit at the intersection of architecture and construction tech."},
        ],
        "sources": [
            {"label": "CMU School of Architecture — Graduate programs", "url": "https://www.architecture.cmu.edu/graduate-programs"},
            {"label": "CMU School of Architecture", "url": "https://www.architecture.cmu.edu/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mba-online": {
        "summary": (
            "Tepper's Online Hybrid MBA delivers the STEM-designated, analytics-forward MBA "
            "with live online sessions and periodic in-person access weekends; students praise "
            "flexibility for working professionals and the Tepper quant core, with cautions "
            "about less campus immersion than the full-time program and self-managed recruiting."
        ),
        "themes": [
            {"label": "Flexible hybrid format", "sentiment": "positive", "detail": "Live online classes plus access weekends suit working professionals."},
            {"label": "STEM-designated MBA", "sentiment": "positive", "detail": "Shares Tepper's analytics and leadership curriculum."},
            {"label": "Working-professional cohort", "sentiment": "positive", "detail": "Peers bring industry experience to case discussions."},
            {"label": "Limited campus immersion", "sentiment": "mixed", "detail": "Less day-to-day Tepper community than the full-time MBA."},
            {"label": "Self-managed recruiting", "sentiment": "caution", "detail": "Career transitions require proactive outreach while employed."},
        ],
        "sources": [
            {"label": "Tepper School — Online Hybrid MBA", "url": "https://www.cmu.edu/tepper/programs/mba/online-hybrid"},
            {"label": "Poets&Quants — Tepper School profile", "url": "https://poetsandquants.com/school-profile/carnegie-mellon-university-tepper-school-of-business/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msba-online": {
        "summary": (
            "Tepper's online MS in Business Analytics extends the top-ranked analytics "
            "curriculum to part-time learners, with praise for STEM designation and "
            "quantitative depth; cautions include a longer timeline than the nine-month "
            "full-time program and remote networking limitations."
        ),
        "themes": [
            {"label": "Top-ranked analytics", "sentiment": "positive", "detail": "Shares the U.S. News #1 business-analytics curriculum in flexible format."},
            {"label": "STEM designation", "sentiment": "positive", "detail": "Analytics, ML, and optimization training for working professionals."},
            {"label": "Part-time flexibility", "sentiment": "positive", "detail": "Online delivery accommodates full-time employment."},
            {"label": "Extended timeline", "sentiment": "mixed", "detail": "Part-time pace spans more months than the full-time MSBA."},
            {"label": "Remote networking", "sentiment": "caution", "detail": "Building recruiting relationships requires extra effort online."},
        ],
        "sources": [
            {"label": "Tepper School — MS in Business Analytics", "url": "https://www.cmu.edu/tepper/programs/master-business-analytics"},
            {"label": "CMU News — U.S. News business analytics #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-tepper-phd": {
        "summary": (
            "The Ph.D. in Business Administration at Tepper is known for quantitative, "
            "economics-driven research across finance, operations, marketing, and "
            "organizational behavior; doctoral students praise rigorous methods training, "
            "with cautions about long time-to-degree and competitive academic job markets."
        ),
        "themes": [
            {"label": "Quantitative research culture", "sentiment": "positive", "detail": "Tepper emphasizes formal modeling, econometrics, and analytical rigor."},
            {"label": "Methods training", "sentiment": "positive", "detail": "Core coursework builds deep foundations in statistics and optimization."},
            {"label": "Faculty research breadth", "sentiment": "positive", "detail": "Doctoral students work across finance, OM, marketing, and OB fields."},
            {"label": "Time-to-degree", "sentiment": "caution", "detail": "Completion commonly spans five or more years of research."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Business-school faculty hiring is highly competitive nationally."},
        ],
        "sources": [
            {"label": "Tepper School — Ph.D. program", "url": "https://www.cmu.edu/tepper/programs/phd"},
            {"label": "Poets&Quants — Tepper School profile", "url": "https://poetsandquants.com/school-profile/carnegie-mellon-university-tepper-school-of-business/"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mism-bida": {
        "summary": (
            "Heinz's MISM Business Intelligence & Data Analytics track extends the top-ranked "
            "information-systems master's with deeper analytics and data-engineering coursework; "
            "students praise tech-consulting placement and CMU's analytics ecosystem, with "
            "cautions about a fast 16-month schedule and overlap with dedicated data-science programs."
        ),
        "themes": [
            {"label": "Analytics specialization", "sentiment": "positive", "detail": "BIDA track adds deeper data analytics to the core MISM curriculum."},
            {"label": "Top MIS ranking", "sentiment": "positive", "detail": "Built on U.S. News #1 management information systems foundation."},
            {"label": "Tech & consulting paths", "sentiment": "positive", "detail": "Graduates enter data, product, and consulting roles at major firms."},
            {"label": "Accelerated schedule", "sentiment": "caution", "detail": "The 16-month calendar packs internships and coursework tightly."},
            {"label": "Program overlap", "sentiment": "mixed", "detail": "Candidates must distinguish BIDA from standalone MSBA or MADS paths."},
        ],
        "sources": [
            {"label": "Heinz College — MISM BIDA track", "url": "https://www.heinz.cmu.edu/programs/information-systems-management-master/bida"},
            {"label": "CMU News — U.S. News MIS #1", "url": "https://www.cmu.edu/news/stories/archives/2024/september/us-news-and-world-report-ranks-carnegie-mellon-university-no-1-in-5-categories-21st-among-national"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-msppm-da": {
        "summary": (
            "The MSPPM Data Analytics track at Heinz combines public-policy training with "
            "quantitative analytics for government and nonprofit roles; students value "
            "interdisciplinary policy-method training, with cautions about lower private-sector "
            "salaries than tech analytics paths and DC-oriented job geography."
        ),
        "themes": [
            {"label": "Policy + analytics", "sentiment": "positive", "detail": "Combines public-policy frameworks with data analysis and visualization."},
            {"label": "Government & nonprofit paths", "sentiment": "positive", "detail": "Graduates enter policy analysis, consulting, and civic-tech roles."},
            {"label": "Heinz interdisciplinary culture", "sentiment": "positive", "detail": "Cohort blends technologists, policy analysts, and managers."},
            {"label": "Salary trade-offs", "sentiment": "mixed", "detail": "Public-sector analytics roles typically pay less than tech industry."},
            {"label": "Geographic concentration", "sentiment": "caution", "detail": "Many policy roles cluster in Washington and state capitals."},
        ],
        "sources": [
            {"label": "Heinz College — MSPPM Data Analytics", "url": "https://www.heinz.cmu.edu/programs/public-policy-management-master/data-analytics"},
            {"label": "Heinz College — MSPPM program", "url": "https://www.heinz.cmu.edu/programs/public-policy-management-master/index"},
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cmu-mshca": {
        "summary": (
            "Heinz's MS in Health Care Analytics trains students to apply data science to "
            "healthcare operations, policy, and outcomes; praise centers on a growing field "
            "and Pittsburgh's health-system presence, with cautions about regulated-industry "
            "hiring cycles and the need for domain knowledge beyond analytics."
        ),
        "themes": [
            {"label": "Healthcare analytics focus", "sentiment": "positive", "detail": "Applies data methods to clinical, operational, and policy questions."},
            {"label": "Industry growth", "sentiment": "positive", "detail": "Health-analytics roles are expanding across providers and payers."},
            {"label": "Pittsburgh health ecosystem", "sentiment": "positive", "detail": "Regional hospitals and insurers provide internship and hiring paths."},
            {"label": "Regulated industry", "sentiment": "caution", "detail": "Healthcare hiring moves slowly and requires compliance awareness."},
            {"label": "Domain knowledge needed", "sentiment": "mixed", "detail": "Success requires understanding clinical and payer workflows beyond data skills."},
        ],
        "sources": [
            {"label": "Heinz College — MS Health Care Analytics", "url": "https://www.heinz.cmu.edu/programs/health-care-analytics-master/index"},
            {"label": "GradReports — Carnegie Mellon University", "url": "https://www.gradreports.com/colleges/carnegie-mellon-university"},
        ],
        "disclaimer": _DISCLAIMER,
    },
}
