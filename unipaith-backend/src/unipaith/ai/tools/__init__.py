"""Tool schemas for Anthropic tool-use calls.

Each agent that uses tool-use registers its schemas here. Schemas are kept
in pure-Python dicts (not pydantic) because they're shipped to Anthropic
verbatim — adding a layer of indirection just risks drift between schema
and model contract.
"""

from unipaith.ai.tools.extractor_schema import EXTRACT_SIGNALS_TOOL
from unipaith.ai.tools.orchestrator_tools import (
    RECORD_ARTIFACT_TOOL,
    REQUEST_LAYER_ADVANCE_TOOL,
    SUGGEST_REPLIES_TOOL,
)

__all__ = [
    "EXTRACT_SIGNALS_TOOL",
    "RECORD_ARTIFACT_TOOL",
    "REQUEST_LAYER_ADVANCE_TOOL",
    "SUGGEST_REPLIES_TOOL",
]
