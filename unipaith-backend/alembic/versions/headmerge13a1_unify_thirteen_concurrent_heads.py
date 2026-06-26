"""Merge thirteen concurrent alembic heads on origin/main (deploy pipeline unblock)

`origin/main` accumulated THIRTEEN divergent leaf-heads because parallel
single-head PRs (enrichment repairs + feature specs) each chained to the
then-current head and squash-merged (the squash-skew CLAUDE.md warns about;
SKILL.md §8 step 5 predicts exactly this). `alembic upgrade head` errors with
"Multiple head revisions are present", so NO new migration applies in prod and
merged repairs sit stranded NOT-LIVE — including the merged Georgetown full
catalog (`georgetownprof1`), whose 190 real-description programs never reach
students while the live API keeps serving its 5 empty-description seed rows
(REPAIR_BACKLOG #1).

This merge-only migration unifies all thirteen into one head. No schema or data
change.

Heads unified:
  c25a1b2c3d4e     — spec25 campaigns full
  d4e5f6a7b8c9     — confidence outcome pairs
  f24da7a0c1b3     — spec24 data upload
  georgetownprof1  — georgetown full catalog (the stranded enrichment)
  l2m3n4o5p6q7     — add institution claim fields
  nyuprof4         — nyu per-credential descriptions / debris
  pennnames1       — penn possessive-to-conferred names
  r40a1b2c3d4e     — spec40 recruitment CRM
  scoredweights1   — add weight research / campus_life
  uiucmrg1         — merge jhuuscmrg1 + uiucprof5
  uiucuwmrg1       — merge uiucheadmrg1 + uwmrg1
  uscprof3         — usc catalogue descriptions repair
  utaprof1         — ut-austin profile repair

Revision ID: headmerge13a1
Revises: c25a1b2c3d4e, d4e5f6a7b8c9, f24da7a0c1b3, georgetownprof1, l2m3n4o5p6q7, nyuprof4, pennnames1, r40a1b2c3d4e, scoredweights1, uiucmrg1, uiucuwmrg1, uscprof3, utaprof1
Create Date: 2026-06-26
"""

from __future__ import annotations

revision = "headmerge13a1"
down_revision = (
    "c25a1b2c3d4e",
    "d4e5f6a7b8c9",
    "f24da7a0c1b3",
    "georgetownprof1",
    "l2m3n4o5p6q7",
    "nyuprof4",
    "pennnames1",
    "r40a1b2c3d4e",
    "scoredweights1",
    "uiucmrg1",
    "uiucuwmrg1",
    "uscprof3",
    "utaprof1",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
