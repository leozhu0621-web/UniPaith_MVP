#!/usr/bin/env python3
"""Regenerate verified discipline definitions for Purdue University-Main Campus.

REPLACES the prior ``FIELD_DESCRIPTIONS`` / ``SLUG_DESCRIPTIONS`` (purdue_field_descriptions.py),
which carried cross-institution-copy fabrications — Penn's "SAS"/"Wharton"/"Perelman",
JHU's "Chesapeake"/"Writing Seminars", Northwestern's "McCormick", Cornell's "Weill", and
re-labeled peer landmarks ("Purdue Review", "Kelly Writers House") — find-replaced from peer
catalogs (REPAIR_BACKLOG critical #3). Each value here is a verified, field-specific
definition of the discipline (general field knowledge, disambiguation-guarded), reused with
Purdue's real owning college + West Lafayette, Indiana geography in purdue_profile.py's
per-credential recipe (gold MIT / Michigan model — Michigan is in CERTIFIED_CLEAN).

Run from unipaith-backend/:
  PYTHONPATH=src:. python scripts/build_purdue_field_descriptions.py

Writes ``src/unipaith/data/purdue_field_descriptions.py`` (DISCIPLINE_DEFS, keyed by the
lowercase field-of-study). General discipline definitions are shared with the verified
Michigan set; Purdue-specific fields are defined below.
"""
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

from scripts.build_michigan_catalogue_descriptions import FIELD_DEFS as MICHIGAN_DEFS

OUT = Path("src/unipaith/data/purdue_field_descriptions.py")

# Verified, field-specific discipline definitions for Purdue fields not covered by the
# shared Michigan set. One or two sentences stating concretely what the field studies
# (the gold-MIT contrast). No institution-specific claims, no peer units.
NEW_DEFS: dict[str, str] = {
    "accounting": "Accounting is the systematic recording, measurement, and communication of financial information about economic entities, supporting decisions by managers, investors, and regulators.",
    "advanced engineering technology": "Advanced engineering technology applies engineering principles and emerging tools to the design, testing, and continuous improvement of technical systems and manufacturing processes.",
    "agricultural communication": "Agricultural communication conveys information about agriculture, food, and natural resources to diverse audiences through journalism, media production, and outreach.",
    "agricultural economics": "Agricultural economics applies economic principles to the production, distribution, and consumption of food and agricultural products and to the management of farms, agribusinesses, and rural resources.",
    "agricultural engineering": "Agricultural engineering applies engineering principles to agricultural production and processing, including machinery, soil and water systems, and the handling of biological materials.",
    "agricultural operations": "Agricultural operations is the applied study of managing crop and livestock production systems, farm equipment, and the day-to-day running of agricultural enterprises.",
    "agricultural systems management": "Agricultural systems management integrates engineering technology, business, and the agricultural sciences to manage the machinery, structures, and information systems used in modern agriculture.",
    "agriculture": "Agriculture is the science and practice of cultivating crops, raising livestock, and managing the natural resources that sustain the production of food, fiber, and fuel.",
    "allied health": "Allied health encompasses the health professions that support diagnosis, treatment, and rehabilitation alongside physicians and nurses, including laboratory, therapeutic, and technical specialties.",
    "animal sciences": "Animal sciences study the biology, nutrition, genetics, behavior, and management of domestic and food-producing animals.",
    "apparel design": "Apparel design is the creative and technical practice of designing clothing and textiles, integrating aesthetics, materials, garment construction, and the study of fashion.",
    "applied mathematics": "Applied mathematics develops and uses mathematical methods — analysis, modeling, and computation — to solve problems arising in science, engineering, and industry.",
    "area studies": "Area studies is the interdisciplinary study of a particular world region, integrating its languages, history, politics, economics, and culture.",
    "atmospheric science": "Atmospheric science is the study of the atmosphere and its processes, including weather and climate phenomena and how the atmosphere behaves and changes over time.",
    "aviation management": "Aviation management is the study of the business and operation of the aviation industry, including airports, airlines, air traffic, and aviation safety and regulation.",
    "biochemistry and molecular biology": "Biochemistry and molecular biology study the chemical processes and molecules of living systems, including the structure, function, and regulation of proteins, nucleic acids, and metabolic pathways.",
    "biological sciences": "The biological sciences study living organisms and life processes, spanning molecular and cellular biology, genetics, physiology, ecology, and evolution.",
    "biotechnology": "Biotechnology applies biological systems, organisms, and molecular techniques to develop products and processes for medicine, agriculture, and industry.",
    "cell biology": "Cell biology is the study of the structure, function, and behavior of cells — the fundamental units of life — and the molecular processes that sustain them.",
    "classical and ancient studies": "Classical and ancient studies is the interdisciplinary study of the languages, literature, history, and cultures of the ancient world, especially Greece and Rome.",
    "communication": "Communication is the study of how people create, exchange, and interpret messages across interpersonal, organizational, media, and public contexts.",
    "comparative pathobiology": "Comparative pathobiology studies the mechanisms of disease across animal and human species, spanning infectious disease, immunology, pathology, toxicology, and public health.",
    "computer and information sciences": "Computer and information sciences study computation, information, and software systems, including algorithms, data, and the design of computing applications.",
    "computer graphics technology": "Computer graphics technology is the applied study of creating and managing digital visual content and interactive media, spanning animation, modeling, visualization, and user experience.",
    "computer information systems": "Computer information systems study how computing and information technology are designed, managed, and applied to meet the needs of organizations.",
    "construction engineering": "Construction engineering applies engineering principles and project management to the planning, design, and execution of infrastructure and building projects.",
    "curriculum and instruction": "Curriculum and instruction is the field of education concerned with what is taught and how — including curriculum design, teaching methods, and the assessment of learning.",
    "data analytics": "Data analytics is the practice of examining data with statistical and computational methods to discover patterns, draw conclusions, and support decision-making.",
    "digital humanities and textual studies": "Digital humanities and textual studies apply computational methods and digital tools to the study of literature, texts, and cultural materials.",
    "doctor of pharmacy": "The Doctor of Pharmacy is the professional degree preparing pharmacists to dispense medications and provide patient-centered pharmaceutical care, combining the pharmaceutical sciences with clinical practice.",
    "earth sciences": "The earth sciences study the physical structure, materials, processes, and history of the Earth, including geology, geophysics, and the planet's interacting systems.",
    "east asian languages": "East Asian languages and cultures is the study of the languages, literatures, and cultures of East Asia, such as Chinese, Japanese, and Korean.",
    "education": "Education as a field studies teaching, learning, and the institutions and policies that shape how people learn across the lifespan.",
    "education studies": "Education studies is the interdisciplinary examination of learning, teaching, and educational systems, drawing on the social sciences and the humanities.",
    "educational leadership": "Educational leadership studies how schools and educational organizations are led, administered, and improved, including governance, policy, and management.",
    "electrical engineering technology": "Electrical engineering technology is the applied study of electrical and electronic systems, focused on the implementation, testing, and maintenance of circuits, power, and control systems.",
    "engineering sciences": "The engineering sciences study the fundamental scientific and mathematical principles — mechanics, materials, thermodynamics, and systems — that underlie all branches of engineering.",
    "engineering technology": "Engineering technology is the applied branch of engineering focused on the practical implementation, operation, and improvement of established engineering systems and processes.",
    "engineering-related technology": "Engineering-related technology applies engineering and technical principles to the design, production, and maintenance of industrial and manufacturing systems.",
    "entrepreneurial and small business operations": "Entrepreneurship and small business management study how new ventures are created, financed, and grown, including opportunity recognition, business planning, and operations.",
    "experimental psychology": "Experimental psychology is the scientific study of mind and behavior through controlled experiments, examining processes such as perception, learning, memory, and cognition.",
    "film and video studies": "Film and video studies examine the history, theory, and production of moving-image media, combining critical analysis with hands-on filmmaking.",
    "finance": "Finance is the study of how individuals, businesses, and institutions raise, allocate, and manage money and capital, including investments, markets, and risk.",
    "fisheries and aquatic sciences": "Fisheries and aquatic sciences study aquatic organisms and ecosystems and the management and conservation of fish populations and water resources.",
    "food science": "Food science applies chemistry, biology, and engineering to the production, processing, preservation, safety, and nutritional quality of food.",
    "forestry": "Forestry is the science and practice of managing forests and woodlands for timber, conservation, recreation, and ecological health.",
    "general engineering": "General engineering provides a broad foundation in the mathematical, scientific, and design principles common to the engineering disciplines before specialization.",
    "genetics": "Genetics is the study of heredity and variation in living organisms, including the structure, function, and transmission of genes.",
    "geography and cartography": "Geography studies the Earth's landscapes, environments, and the relationships between people and places, while cartography is the science and art of map-making.",
    "gerontology": "Gerontology is the interdisciplinary study of aging and the biological, psychological, and social dimensions of later life.",
    "health administration": "Health administration is the study of how to plan, organize, finance, and manage health-care organizations, services, and systems.",
    "health sciences": "The health sciences study human health and disease and the science underlying clinical practice, spanning anatomy, physiology, and the foundations of the health professions.",
    "horticulture": "Horticulture is the science and art of cultivating fruits, vegetables, flowers, and ornamental plants, including their production, breeding, and management.",
    "hospitality and tourism management": "Hospitality and tourism management is the study of the business and operations of the hospitality and tourism industry, including lodging, food service, events, and travel.",
    "human development and family studies": "Human development and family studies examine how individuals grow and change across the lifespan and how families and relationships shape well-being.",
    "human resource management": "Human resource management is the study of how organizations recruit, develop, compensate, and manage people to achieve their goals.",
    "industrial engineering": "Industrial engineering designs, analyzes, and optimizes complex systems of people, processes, and resources, using methods from operations research, statistics, and management.",
    "industrial engineering technology": "Industrial engineering technology is the applied study of improving production and operational systems, focused on efficiency, quality, and the implementation of industrial processes.",
    "information science": "Information science studies how information is collected, organized, stored, retrieved, and used, integrating computing, organization, and human needs.",
    "information technology": "Information technology is the applied study of computing systems, networks, and software used to store, process, and communicate information in organizations.",
    "integrated science": "Integrated science is an interdisciplinary program that combines multiple scientific disciplines — such as biology, chemistry, physics, and mathematics — into a unified course of study.",
    "intercultural studies": "Intercultural studies examine the interactions among cultures and the social experiences of ethnic, cultural, and minority groups.",
    "interdisciplinary studies": "Interdisciplinary studies allow students to integrate methods and knowledge from multiple academic fields into a coherent, individually designed program.",
    "kinesiology": "Kinesiology is the scientific study of human movement and physical activity, integrating physiology, biomechanics, and motor behavior to understand health and performance.",
    "learning design and technology": "Learning design and technology is the field that designs instruction and applies technology to support teaching and learning across schools, workplaces, and digital environments.",
    "liberal arts": "Liberal arts is a broad course of study across the humanities, social sciences, and natural sciences that develops critical thinking, communication, and analytical skills.",
    "management": "Management is the study of how organizations are led and operated, encompassing strategy, organizational behavior, operations, and the coordination of people and resources.",
    "management sciences and quantitative methods": "Management science applies mathematical modeling, statistics, and analytics to managerial decision-making and the optimization of business operations.",
    "marketing": "Marketing is the study of how organizations create, communicate, and deliver value to customers, including consumer behavior, branding, pricing, and promotion.",
    "materials engineering": "Materials engineering studies the structure, properties, processing, and performance of materials and how they are designed and engineered for use.",
    "mathematics and computer science": "This joint field combines the rigorous study of mathematics with the theory and practice of computer science, spanning algorithms, computation, and mathematical reasoning.",
    "mechanical engineering technology": "Mechanical engineering technology is the applied study of mechanical systems and machines, focused on design implementation, testing, manufacturing, and maintenance.",
    "medical laboratory sciences": "Medical laboratory science is the health profession that performs and interprets laboratory tests on blood, tissue, and other specimens to diagnose and monitor disease.",
    "nanotechnology": "Nanotechnology is the study and engineering of matter at the nanometer scale, where novel physical, chemical, and biological properties enable new materials and devices.",
    "natural resources": "Natural resources is the interdisciplinary study of the conservation and management of land, water, forests, wildlife, and other environmental resources.",
    "neurobiology and neurosciences": "Neurobiology and the neurosciences study the nervous system, examining the structure and function of neurons and the brain and how they give rise to behavior.",
    "nuclear engineering": "Nuclear engineering applies the principles of nuclear physics to the design and operation of nuclear reactors, radiation systems, and applications in energy and medicine.",
    "nutrition science": "Nutrition science studies how nutrients and diet affect growth, health, and disease, integrating biochemistry, physiology, and public health.",
    "nutrition sciences": "Nutrition sciences examine the role of food, nutrients, and dietary patterns in metabolism, health, and the prevention of disease across the lifespan.",
    "pharmacology and toxicology": "Pharmacology and toxicology study how drugs and chemicals act on living systems, including their therapeutic effects and their harmful or toxic effects.",
    "plant science": "Plant science is the study of plants, including their biology, genetics, growth, and cultivation for food, fiber, and the environment.",
    "psychological sciences": "Psychological science is the scientific study of mind and behavior, examining cognition, emotion, development, and the social and biological influences on behavior.",
    "public health": "Public health is the science and practice of protecting and improving the health of populations through prevention, education, policy, and research.",
    "religious studies": "Religious studies is the academic, non-confessional study of religious beliefs, practices, texts, and institutions across cultures and history.",
    "retail management": "Retail management is the study of the business of selling goods and services to consumers, including merchandising, buying, marketing, and store and e-commerce operations.",
    "romance languages": "Romance languages is the study of the languages descended from Latin — such as French, Spanish, and Italian — and their literatures and cultures.",
    "science, technology and society": "Science, technology, and society is an interdisciplinary field examining how science and technology shape, and are shaped by, social, political, and cultural contexts.",
    "selling and sales management": "Selling and sales management is the study of professional selling, sales-force leadership, customer relationships, and the strategies that drive revenue.",
    "slavic languages": "Slavic languages is the study of the Slavic languages — such as Russian, Polish, and Czech — and their literatures and cultures.",
    "social sciences": "The social sciences study human society and social relationships, drawing on disciplines such as sociology, political science, economics, and anthropology.",
    "soil science": "Soil science studies soils as natural resources, including their formation, properties, classification, and management for agriculture and the environment.",
    "special education": "Special education is the field that designs and delivers instruction and support for students with disabilities and exceptional learning needs.",
    "speech, language, and hearing sciences": "Speech, language, and hearing sciences study human communication and its disorders, including the mechanisms of speech, language, and hearing and their evaluation and treatment.",
    "systems science and theory": "Systems science and theory is the interdisciplinary study of complex systems and the principles, models, and methods used to understand their structure and behavior.",
    "teacher education (levels and methods)": "This field prepares teachers for specific grade levels and develops the pedagogical methods, classroom practice, and assessment skills of effective teaching.",
    "teacher education (subject areas)": "This field prepares teachers in specific subject areas, combining subject-matter expertise with pedagogy, curriculum, and supervised classroom practice.",
    "theatre": "Theatre is the study and practice of dramatic performance, encompassing acting, directing, design, and the analysis of plays and theatrical traditions.",
    "veterinary biomedical sciences": "Veterinary biomedical sciences study the biology, physiology, and disease of animals to advance both animal and human health.",
    "veterinary medicine": "Veterinary medicine is the branch of medicine concerned with the diagnosis, treatment, and prevention of disease and injury in animals.",
    "veterinary technology": "Veterinary technology is the applied health field that supports veterinarians through clinical care, laboratory work, anesthesia, and diagnostic procedures for animals.",
    "visual arts": "The visual arts encompass the creation and study of art in visual forms such as drawing, painting, sculpture, and new media.",
    "visual communication design": "Visual communication design is the practice of conveying ideas and information through visual form, including graphic design, typography, and digital media.",
}


def build_defs() -> dict[str, str]:
    defs: dict[str, str] = {}
    # Shared, verified general discipline definitions (lowercased keys).
    for k, v in MICHIGAN_DEFS.items():
        defs[k.lower()] = v
    # Purdue-specific fields (override on conflict).
    defs.update(NEW_DEFS)
    return defs


def write_module(defs: dict[str, str]) -> None:
    lines = [
        '"""Verified discipline definitions for Purdue University-Main Campus.',
        "",
        "Each value is a verified, field-specific definition of an academic discipline (general",
        "field knowledge, disambiguation-guarded). purdue_profile.py composes each program's",
        "description per-credential: a level lead (\"Graduate study.\" / \"Doctoral research.\" /",
        "\"Graduate certificate.\") + this definition + Purdue's real owning college on the West",
        "Lafayette, Indiana campus + the program's credential level (the gold MIT / Michigan model).",
        "",
        "REPLACES the prior FIELD_DESCRIPTIONS / SLUG_DESCRIPTIONS, which carried",
        "cross-institution-copy fabrications find-replaced from peer catalogs (Penn's SAS/Wharton/",
        "Perelman, JHU's Chesapeake/Writing Seminars, Northwestern's McCormick, Cornell's Weill) —",
        "REPAIR_BACKLOG critical #3. No institution-specific claims live here; no peer units.",
        "",
        "Regenerate via scripts/build_purdue_field_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "DISCIPLINE_DEFS: dict[str, str] = {",
    ]
    for k in sorted(defs):
        esc = defs[k].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{k}": "{esc}",')
    lines.append("}")
    OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    defs = build_defs()
    write_module(defs)
    print(f"Wrote {len(defs)} discipline definitions → {OUT}")


if __name__ == "__main__":
    main()
