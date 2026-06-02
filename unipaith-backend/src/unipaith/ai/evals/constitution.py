"""Spec 61 §3 — the behavior-constitution loader.

One source of truth, two readers. Each ``_shared/constitution_{agent}.md`` is
**both** the system-prompt include (so the conversational Claude agent is
steered by it) **and** the spec-62 judge rubric (so the agent is graded against
the exact same words). This module parses the versioned markdown into a
structured :class:`Constitution` so the prompt builder, the chatbot eval adapter
(`chatbot_adapter.py`), the runner, and the ``/goal/chatbot-eval`` transparency
surface all read the *same* dimensions + version — they cannot drift.

Dependency-free (``re`` + ``pathlib`` only) so the transparency layer can import
it without pulling in the AI client.

Format parsed (see the two constitution files):

- version  →  a ``> **Version:** X.Y.Z`` line
- each scored dimension  →  a heading
  ``## <key> — <Label> · <scored|hard-floor>`` followed by its prose body
  (the judge guidance for that dimension).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

# ``ai/evals/`` → ``ai/`` → ``ai/prompts/_shared``
_SHARED_DIR = Path(__file__).resolve().parent.parent / "prompts" / "_shared"

# The two conversational Claude surfaces spec 61 governs.
AGENTS: tuple[str, ...] = ("student", "faculty")

_VERSION_RE = re.compile(r"\*\*Version:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)")
# Heading: "## key — Label · scored"  (— = U+2014 em dash, · = U+00B7 middot)
_DIM_RE = re.compile(
    r"^##\s+(?P<key>\w+)\s+—\s+(?P<label>.+?)\s+·\s+(?P<floor>hard-floor|scored)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Dimension:
    """One scored rubric dimension parsed from a constitution file."""

    key: str
    label: str
    hard_floor: bool
    criterion: str  # the prose body under the heading — verbatim judge guidance


@dataclass(frozen=True)
class Constitution:
    """A parsed, versioned constitution = the verbatim spec-62 rubric."""

    agent: str  # "student" | "faculty"
    version: str
    path: str
    dimensions: tuple[Dimension, ...]
    full_text: str

    @property
    def dimension_keys(self) -> tuple[str, ...]:
        return tuple(d.key for d in self.dimensions)

    @property
    def hard_floor_keys(self) -> tuple[str, ...]:
        return tuple(d.key for d in self.dimensions if d.hard_floor)


def constitution_path(agent: str) -> Path:
    if agent not in AGENTS:
        raise ValueError(f"unknown constitution agent {agent!r}; expected one of {AGENTS}")
    return _SHARED_DIR / f"constitution_{agent}.md"


def constitution_exists(agent: str) -> bool:
    return constitution_path(agent).is_file()


@cache
def load_constitution(agent: str) -> Constitution:
    """Parse ``constitution_{agent}.md`` into a structured rubric.

    Cached — the files are static at runtime. Raises ``FileNotFoundError`` if the
    file is missing and ``ValueError`` if it carries no parseable version or
    dimensions (a malformed rubric must fail loudly, never silently grade on an
    empty rubric).
    """
    path = constitution_path(agent)
    text = path.read_text(encoding="utf-8")

    version_match = _VERSION_RE.search(text)
    if not version_match:
        raise ValueError(f"constitution {path.name} has no `**Version:** X.Y.Z` line")
    version = version_match.group(1)

    matches = list(_DIM_RE.finditer(text))
    if not matches:
        raise ValueError(
            f"constitution {path.name} declares no `## key — Label · floor` dimensions"
        )

    dimensions: list[Dimension] = []
    for i, m in enumerate(matches):
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        criterion = text[body_start:body_end].strip()
        dimensions.append(
            Dimension(
                key=m.group("key"),
                label=m.group("label").strip(),
                hard_floor=m.group("floor") == "hard-floor",
                criterion=criterion,
            )
        )

    return Constitution(
        agent=agent,
        version=version,
        path=str(path),
        dimensions=tuple(dimensions),
        full_text=text.rstrip(),
    )


def all_constitutions() -> list[Constitution]:
    """Every constitution that exists on disk, in declared agent order."""
    return [load_constitution(a) for a in AGENTS if constitution_exists(a)]
