"""Cornell University — universal, program-DISTINCT ``who_its_for``.

REPAIR_BACKLOG #4b (``who_its_for`` TYPE-GAMING), SKILL miss #8 (universal depth
field). The base ``cornell_profile`` catalog (222 real, field-specific,
structurally-clean programs) shipped ``who_its_for`` filled but TYPE-GAMED: every
graduate row carried one ``_WHO_GRAD_BASELINE`` template and every undergraduate row
one ``_WHO_BASELINE`` template, so a CS Ph.D. and a Public-Policy Ph.D. read
identically (distinct/total ≈ 0.10).

This module builds a field-specific, program-DISTINCT statement of the applicant each
program fits: ``WHO_BY_FIELD[field]`` (the subject + the applicant it fits, derived
strictly from the program's own field — no fabricated facts, rankings, numbers, or
named centers) followed by ``LEVEL_TAIL[degree_type]`` (the credential-appropriate
readiness / typical next step), so a bachelor's survey, a professional master's, a
focused certificate, and a funded research doctorate of the SAME field read
differently. Because every ``(field, credential)`` pair is unique in this catalog,
every composed string is distinct (distinct/total ≈ 1.0, never a one-per-degree-type
template), matching the field-specific gold bar (Brown / Emory / Purdue / Rice /
UW-Madison). The hand-written ``_WHO_BY_SLUG`` flagship overrides in
``cornell_profile`` win first; this covers the breadth (IPEDS) rows.
"""

from __future__ import annotations

# ruff: noqa: E501

# ---------------------------------------------------------------------------
# WHO_BY_FIELD — the field-specific lead: the subject and the applicant it fits
# (background / interest), written from the Cornell catalog field name alone, with
# no fabricated facts. Keyed on the field portion of each breadth program_name
# (``_field_from_program_name`` in cornell_profile). The LEVEL_TAIL adds the
# credential-appropriate next step.
# ---------------------------------------------------------------------------
WHO_BY_FIELD: dict[str, str] = {
    "Aerospace Engineering": "Students drawn to the design and analysis of aircraft, spacecraft, propulsion, and the systems that fly and navigate",
    "Agricultural Business and Management": "Students who want to apply economics and management to farms, food businesses, and agricultural enterprises",
    "Agricultural Engineering": "Students who want to engineer the machinery, water, and biological systems behind food and agricultural production",
    "Agricultural Sciences": "Students drawn to the science of crops, soils, and food systems and how research improves agriculture",
    "Animal Sciences": "Students fascinated by animal biology, nutrition, genetics, and management across livestock and companion species",
    "Anthropology": "Students drawn to human cultures, societies, and our biological and historical past",
    "Apparel and Textiles": "Students interested in the design, science, and business of fiber, fabric, and apparel",
    "Applied Horticulture and Horticultural Business Services": "Students drawn to the science and business of growing plants, from greenhouse production to landscape and nursery management",
    "Applied Mathematics": "Students who want to use mathematical modeling and computation to solve real scientific and engineering problems",
    "Archeology": "Students fascinated by past societies and how material remains reveal how people lived",
    "Architectural Sciences and Technology": "Students drawn to the technical side of building — structures, environmental systems, and the science of how buildings perform",
    "Architecture": "Students who want to design buildings and shape the built environment through studio practice, history, and technology",
    "Asian Studies": "Students drawn to the languages, literatures, histories, and cultures of Asia",
    "Astronomy and Astrophysics": "Students fascinated by stars, galaxies, planets, and the physics of the universe",
    "Atmospheric Sciences and Meteorology": "Students who want to understand weather, climate, and the dynamics of the atmosphere",
    "Biochemistry, Molecular and Cell Biology": "Students drawn to the molecules and reactions that drive life, from genes and proteins to cellular machinery",
    "Biological Engineering": "Students at the interface of engineering and the life sciences who want to engineer biological and environmental systems",
    "Biological Sciences": "Students fascinated by living systems, from molecules and cells to organisms and ecosystems",
    "Biomedical Engineering": "Students at the interface of engineering and medicine who want to design devices, imaging, and therapies",
    "Biomedical and Biological Sciences": "Students drawn to the mechanisms of human and animal physiology, disease, and pathobiology through research",
    "Chemical Engineering": "Students who want to turn chemical and biological processes into products at industrial scale",
    "Chemistry": "Students drawn to matter and its transformations, from synthesis to spectroscopy and reaction mechanisms",
    "City and Regional Planning": "Students focused on how communities and regions grow, drawn to land use, transportation, housing, and equitable development",
    "Civil Engineering": "Students focused on the infrastructure — structures, transportation, water, and the built environment — society relies on",
    "Classics": "Students drawn to the languages, literature, and civilizations of ancient Greece and Rome",
    "Communication and Media Studies": "Students interested in how messages, media, and audiences shape public life, organizations, and culture",
    "Community Organization and Advocacy": "Students drawn to grassroots mobilization, advocacy, and how communities organize for social change",
    "Computational Biology": "Students who combine biology with computation to analyze genomes and large biological datasets",
    "Computer Science": "Students drawn to algorithms, systems, and software who want rigorous training in how computation works",
    "Dance": "Students committed to dance as performers, choreographers, and scholars of movement",
    "Design and Applied Arts": "Students who want to design objects, environments, and experiences across applied-arts media",
    "Earth and Atmospheric Sciences": "Students who want to understand the Earth, its oceans and atmosphere, and the forces that shape the planet",
    "Ecology and Evolutionary Biology": "Students drawn to how organisms interact with their environment and change over evolutionary time",
    "Economics": "Students who want to understand how people, markets, and institutions allocate scarce resources",
    "Electrical and Computer Engineering": "Students drawn to circuits, signals, power, and the hardware and embedded systems behind modern devices",
    "Engineering Mechanics": "Students who want the mathematical and physical foundations of how materials and structures behave under load",
    "Engineering Physics": "Students who want to apply deep physics and mathematics to engineering problems at the frontier of technology",
    "English": "Students who love literature and writing and want to read closely, think critically, and argue in prose",
    "Environmental Design": "Students focused on designing sustainable, human-centered environments across architecture, landscape, and planning",
    "Environmental Engineering": "Students applying engineering to clean water, air quality, and sustainable infrastructure",
    "Fine and Studio Arts": "Students committed to making art and developing a studio practice across media",
    "Food Science and Technology": "Students drawn to the chemistry, microbiology, and engineering behind safe, nutritious, and appealing food",
    "Genetics": "Students focused on heredity, genomes, and how genes shape development, health, and variation",
    "German Studies": "Students drawn to German language, literature, and the intellectual traditions of the German-speaking world",
    "Historic Preservation and Conservation": "Students committed to conserving historic places, buildings, and cultural heritage",
    "History": "Students who want to understand the past and how it shapes the present through evidence and argument",
    "History of Architecture and Urban Development": "Students drawn to the history and theory of buildings, cities, and the forces that shaped the built environment",
    "Hospitality Management": "Students focused on leading hotels, restaurants, and the broader hospitality and service industry",
    "Hotel Administration": "Students preparing to lead the global hospitality industry, blending business fundamentals with service operations",
    "Housing and Human Environments": "Students drawn to how the design and policy of homes and built environments shape human well-being",
    "Human Development": "Students who want to understand how people develop across the lifespan, blending psychology, biology, and social context",
    "International Agriculture": "Students focused on food security, rural development, and agriculture in a global and comparative context",
    "Landscape Architecture": "Students who want to design landscapes, parks, and public spaces that balance ecology and human use",
    "Law": "Students pursuing advanced legal scholarship and research at the doctoral level",
    "Legal Studies (Online)": "Working professionals who need legal frameworks and reasoning without intending to practice law",
    "Linguistics": "Students drawn to the structure of language — its sounds, grammar, meaning, and how languages compare",
    "Management": "Students pursuing doctoral research on organizations, strategy, and how businesses are led and managed",
    "Materials Engineering": "Students who want to design and characterize materials, from nanostructures to alloys and biomaterials",
    "Mathematics": "Students who love mathematical reasoning, proof, and abstraction across pure and applied areas",
    "Mechanical Engineering": "Students drawn to mechanical systems, thermodynamics, and design across energy, robotics, and manufacturing",
    "Medieval and Renaissance Studies": "Students drawn to the literature, history, art, and thought of the medieval and early-modern world",
    "Microbiology": "Students drawn to microbes — their biology, genetics, and roles in health, disease, and the environment",
    "Music": "Students committed to music as performers, composers, and scholars",
    "Natural Resources and the Environment": "Students focused on conserving and managing forests, water, wildlife, and natural systems",
    "Neurobiology and Behavior": "Students fascinated by the nervous system and how brains generate behavior, from neurons to whole organisms",
    "Nuclear Engineering": "Students drawn to nuclear science and engineering — reactors, radiation, and energy systems",
    "Nutrition Sciences": "Students who want to understand how diet and nutrients affect human health across biology, public health, and policy",
    "Operations Research and Engineering": "Students who want to optimize complex systems and decisions using mathematics, modeling, and data",
    "Operations Research and Information Engineering": "Students who want to engineer better decisions and systems through optimization, stochastic models, and data",
    "Performing and Media Arts": "Students drawn to theater, film, and performance as makers, scholars, and critics",
    "Philosophy": "Students drawn to fundamental questions of knowledge, ethics, mind, and reality and to rigorous argument",
    "Physics": "Students drawn to the fundamental laws of nature, from particles and fields to matter and energy",
    "Plant Biology": "Students fascinated by how plants grow, function, and evolve, from molecules to ecosystems",
    "Plant Sciences": "Students drawn to the science of crops and plants — breeding, protection, and sustainable production",
    "Political Science and Government": "Students drawn to government, politics, and how power and institutions shape collective life",
    "Psychology": "Students fascinated by mind and behavior who want to study how people think, feel, and act",
    "Public Health": "Students committed to protecting and improving the health of populations through prevention and policy",
    "Public Policy Analysis": "Students who want to analyze, design, and evaluate policy to solve public problems",
    "Real Estate": "Students focused on real-estate development, investment, and the economics of the built environment",
    "Religious Studies": "Students drawn to the comparative study of religion, its texts, practices, and role in human cultures",
    "Romance Studies": "Students drawn to the languages, literatures, and cultures of the Romance-speaking world",
    "Science, Technology and Society": "Students who want to study how science and technology shape — and are shaped by — society, politics, and ethics",
    "Sociology": "Students who want to understand social structure, inequality, and how groups and institutions shape behavior",
    "Statistics": "Students drawn to inference and uncertainty who want to design studies and draw conclusions from data",
    "Sustainability Studies": "Students focused on balancing environmental, social, and economic needs for a sustainable future",
    "Systems Engineering": "Students who want to engineer complex systems end-to-end, balancing requirements, integration, and risk",
    "Veterinary Biomedical and Clinical Sciences": "Students drawn to research in animal health, comparative medicine, and the biology behind veterinary clinical practice",
    "Veterinary Medicine": "Students preparing for careers in animal health, clinical veterinary practice, and comparative biomedical research",
}


# ---------------------------------------------------------------------------
# LEVEL_TAIL — credential-appropriate readiness / typical next step. Follows the
# field lead so each credential level of a field reads differently.
# ---------------------------------------------------------------------------
LEVEL_TAIL: dict[str, str] = {
    "bachelors": "and want a broad undergraduate foundation before careers or graduate study.",
    "masters": "and want advanced, specialized graduate coursework aimed at senior professional roles.",
    "certificate": "looking for a focused, credit-bearing credential without committing to a full degree.",
    "phd": "and want to pursue original doctoral research toward academic or research careers.",
    "professional": "and want rigorous professional preparation for practice in the field.",
}


def compose_who(field: str | None, degree_type: str) -> str | None:
    """field-specific lead + credential-appropriate tail. Returns None if the
    field has no WHO_BY_FIELD entry (the build gate then fails loudly)."""
    if not field:
        return None
    lead = WHO_BY_FIELD.get(field)
    if lead is None:
        return None
    tail = LEVEL_TAIL.get(degree_type, LEVEL_TAIL["masters"])
    return f"{lead} {tail}"
