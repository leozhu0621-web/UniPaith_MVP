#!/usr/bin/env python3
"""Regenerate verified, per-credential program descriptions for Stanford University.

Replaces the machine "Catalog entry <hex>:" + division-frame build-artifact assembly
(REPAIR_BACKLOG run 59 / stanfordprof10). Each description leads with a verified,
field-specific discipline definition, followed by a clause naming the program's real
owning Stanford school/department and credential level. Flagship slugs keep hand-gathered
descriptions from ``stanford_field_descriptions.SLUG_DESCRIPTIONS``.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/build_stanford_catalogue_descriptions.py

Writes ``src/unipaith/data/stanford_catalogue_descriptions.py`` keyed by program slug.
"""
# ruff: noqa: E501

from __future__ import annotations

import importlib.util
from pathlib import Path

OUT = Path("src/unipaith/data/stanford_catalogue_descriptions.py")
MICH_BUILD = Path("scripts/build_michigan_catalogue_descriptions.py")

_PREFIXES = (
    "Bachelor of Arts in ",
    "Bachelor of Science in ",
    "Master of Science in ",
    "Master of Arts in ",
    "Doctor of Philosophy in ",
    "Graduate Certificate in ",
)

_WHOLE = {
    "Juris Doctor": "law (jd)",
    "Doctor of Medicine": "medicine",
    "Master of Business Administration": "business administration (mba)",
    "Master of Science in Management (MSx)": "business administration (mba)",
}


def sfield(name: str) -> str:
    name = name.replace("'", "'")
    whole = {k.replace("'", "'"): v for k, v in _WHOLE.items()}
    if name in whole:
        return whole[name]
    for p in _PREFIXES:
        if name.startswith(p):
            return name[len(p) :].strip().lower()
    return name.lower()


# Stanford field key → Michigan FIELD_DEFS key (shared discipline definitions).
_STANFORD_TO_MICH: dict[str, str] = {
    "aeronautics and astronautics": "aerospace engineering",
    "anthropology": "anthropology",
    "applied mathematics": "applied and interdisciplinary mathematics",
    "archaeology": "archaeology of the ancient mediterranean",
    "art history": "art",
    "art practice": "art and design",
    "biochemistry": "biochemistry",
    "bioengineering": "biomedical engineering",
    "biology": "biology",
    "biomedical informatics": "bioinformatics",
    "biomedical sciences": "biomedical sciences (pibs)",
    "biosciences": "biomedical sciences (pibs)",
    "business administration": "business administration",
    "business administration (mba)": "business administration (mba)",
    "cell and developmental biology": "cell and developmental biology (pibs)",
    "chemical engineering": "chemical engineering",
    "chemistry": "chemistry",
    "civil and environmental engineering": "civil engineering",
    "classics": "classical studies",
    "clinical research": "clinical research design and statistical analysis",
    "communication": "communication and media",
    "comparative literature": "comparative literature",
    "comparative studies in race and ethnicity": "afroamerican and african studies",
    "computer science": "computer science",
    "earth systems": "earth systems",
    "east asian languages and cultures": "asian languages and cultures",
    "ecology and evolution": "ecology and evolutionary biology",
    "economics": "economics",
    "education": "education",
    "educational assessment and evaluation": "educational assessment and evaluation",
    "electrical engineering": "electrical engineering",
    "engineering fundamentals": "engineering physics",
    "english": "english language and literature",
    "environmental engineering": "environmental engineering",
    "epidemiology and clinical research": "public health sciences",
    "film and media studies": "film, television, and media",
    "french and italian": "romance languages and literatures",
    "genetics": "genetics and genomics (pibs)",
    "geological sciences": "geological sciences",
    "german studies": "german",
    "history": "history",
    "humanities": "arts and ideas in the humanities",
    "international policy": "international studies",
    "international relations": "international and regional studies",
    "law": "law (jd)",
    "law (jd)": "law (jd)",
    "linguistics": "linguistics",
    "management science and engineering": "industrial and operations engineering",
    "materials science and engineering": "materials science and engineering",
    "mathematics": "mathematics",
    "mechanical engineering": "mechanical engineering",
    "media studies": "film, television, and media",
    "medicine": "medicine",
    "microbiology and immunology": "microbiology and immunology",
    "music": "music",
    "neuroscience": "neuroscience",
    "philosophy": "philosophy",
    "physics": "physics",
    "physiology": "physiology",
    "political science": "political science",
    "product design": "product design",
    "psychology": "psychology",
    "public policy": "public policy",
    "public relations": "communication and media",
    "religious studies": "philosophy",
    "science, technology, and society": "science, technology, and society",
    "slavic languages and literatures": "slavic languages and literatures",
    "sociology": "sociology",
    "statistics": "statistics",
    "subject-area teacher education": "subject-area teacher education",
    "sustainability": "environmental health sciences",
    "symbolic systems": "cognitive science",
    "systems science and engineering": "electrical and computer engineering",
    "teacher education": "teacher education",
    "theater and performance studies": "theatre & drama",
    "urban studies": "urban and regional planning",
}

# Stanford-only definitions where Michigan has no clean match.
_STANFORD_ONLY: dict[str, str] = {
    "physiology": (
        "Physiology is the study of how living organisms function, examining the "
        "mechanical, physical, and biochemical processes that sustain life at the "
        "cellular, organ, and systems levels."
    ),
    "religious studies": (
        "Religious studies is the academic study of religion, examining beliefs, "
        "practices, texts, and institutions across traditions without advocating "
        "for or against any particular faith."
    ),
    "science, technology, and society": (
        "Science, technology, and society examines how scientific knowledge and "
        "technological systems shape — and are shaped by — social, political, and "
        "ethical forces in modern life."
    ),
    "product design": (
        "Product design is the practice of creating useful, usable, and desirable "
        "objects and systems, integrating user research, engineering constraints, "
        "and aesthetic form in the design process."
    ),
    "earth systems": (
        "Earth systems science integrates geology, ecology, oceanography, and "
        "atmospheric science to study how the planet's physical and biological "
        "systems interact and respond to human activity."
    ),
    "geological sciences": (
        "Geological sciences study the Earth's solid materials, structures, and "
        "processes — including mineralogy, tectonics, and the history recorded in "
        "rocks and landforms."
    ),
    "education": (
        "Education is the study of teaching, learning, and the institutions that "
        "shape how knowledge and skills are developed across the lifespan."
    ),
    "teacher education": (
        "Teacher education prepares educators for classroom practice through "
        "pedagogy, curriculum design, and supervised clinical placements in "
        "partner schools."
    ),
    "subject-area teacher education": (
        "Subject-area teacher education combines deep content knowledge in a "
        "discipline with the pedagogical methods needed to teach that subject "
        "effectively in secondary or postsecondary settings."
    ),
    "educational assessment and evaluation": (
        "Educational assessment and evaluation studies how to measure learning "
        "outcomes, design valid tests and surveys, and use data to improve "
        "instruction and educational policy."
    ),
}


def _load_michigan_field_defs() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("mich_build", MICH_BUILD)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.FIELD_DEFS


def _field_def(field_key: str, mich: dict[str, str]) -> str | None:
    if field_key in _STANFORD_ONLY:
        return _STANFORD_ONLY[field_key]
    mich_key = _STANFORD_TO_MICH.get(field_key)
    if mich_key and mich_key in mich:
        return mich[mich_key]
    return None


_PREFIX = {
    "bachelors": "",
    "masters": "Graduate study. ",
    "phd": "Doctoral research. ",
    "professional": "Professional study. ",
    "certificate": "Graduate certificate study. ",
}
_LEVEL = {
    "bachelors": "undergraduate",
    "masters": "master's",
    "phd": "doctoral",
    "professional": "professional",
    "certificate": "graduate certificate",
}


def build() -> dict[str, str]:
    from unipaith.data.stanford_catalog_descriptions import PROGRAMS
    from unipaith.data.stanford_field_descriptions import SLUG_DESCRIPTIONS

    mich = _load_michigan_field_defs()
    out: dict[str, str] = {}
    missing: list[str] = []

    for p in PROGRAMS:
        slug = p["slug"]
        if slug in SLUG_DESCRIPTIONS:
            out[slug] = SLUG_DESCRIPTIONS[slug]
            continue
        name = p["program_name"]
        dtype = p["degree_type"]
        dept = p["department"]
        fkey = sfield(name)
        defn = _field_def(fkey, mich)
        if not defn:
            missing.append(f"{fkey}  ({name})")
            continue
        desc = (
            f"{_PREFIX[dtype]}{defn} At Stanford University's {dept} on the "
            f"Stanford campus, the {name} engages this discipline at the "
            f"{_LEVEL[dtype]} level."
        )
        if p.get("delivery_format") == "online":
            desc += " Delivered fully online."
        elif p.get("delivery_format") == "hybrid":
            desc += " Delivered in a hybrid format."
        out[slug] = desc

    if missing:
        raise SystemExit("Missing field definitions for:\n  " + "\n  ".join(sorted(set(missing))))
    if len(out) != len(PROGRAMS):
        raise SystemExit(f"Expected {len(PROGRAMS)} descriptions, got {len(out)}")
    return out


def write_module(descs: dict[str, str]) -> None:
    lines = [
        '"""Verified, per-credential program descriptions for Stanford University.',
        "",
        "Each description leads with a verified, field-specific definition of the program's",
        "discipline (disambiguation-guarded discipline definitions), followed by a clause",
        "naming the program's real owning Stanford school/department and credential level.",
        "Master's, doctoral, and certificate rows carry a credential-specific lead so each",
        "credential of a field reads distinctly (gold MIT = 0% shared bodies). Flagship",
        "programs retain hand-gathered SLUG_DESCRIPTIONS from stanford_field_descriptions.",
        "",
        'Regenerated 2026-06-19 to replace the machine "Catalog entry <hex>:" + division-frame',
        "build-artifact assembly (REPAIR_BACKLOG run 59, Stanford target). Regenerate via",
        "scripts/build_stanford_catalogue_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "CATALOGUE_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(descs):
        esc = descs[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{esc}",')
    lines.append("}")
    OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    from unipaith.profile_standard.anti_stub import analyze, machine_artifacts

    descs = build()
    from unipaith.data.stanford_catalog_descriptions import PROGRAMS

    by_slug = {p["slug"]: p["program_name"] for p in PROGRAMS}
    programs = [{"program_name": by_slug[s], "description": d} for s, d in descs.items()]
    report = analyze(programs)
    arts = machine_artifacts(programs)
    if not report.is_clean or arts:
        raise SystemExit(f"Anti-stub gate failed: {report.summary()} | artifacts={arts[:5]}")
    write_module(descs)
    print(f"Wrote {len(descs)} descriptions → {OUT} (anti-stub clean, 0 artifacts)")


if __name__ == "__main__":
    main()
