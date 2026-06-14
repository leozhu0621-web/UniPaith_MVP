"""UniPaith MCP data API — a single-key endpoint the Claude platform agent can
call to read/write student data directly (standalone, without the in-app host).

Transport: MCP Streamable HTTP (stateless JSON-RPC 2.0 over POST /mcp). Auth: a
single bearer key (`settings.unipaith_mcp_api_key`). **By explicit product
direction this key grants ALL-DATA access** — a valid bearer may operate on any
student by id. Guard it like a master credential.

The tools wrap the same service layer the in-app host uses (`dispatch_tool`),
resolving the caller-supplied `student_id` (a StudentProfile id or User id) to a
user and reusing every existing rule (consent, handoff gating, persistence).
No SDK dependency — the protocol is implemented directly to avoid pulling the
`mcp` package's pydantic constraints into the backend.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.database import get_db
from unipaith.models.student import StudentProfile
from unipaith.services.uni_tools import dispatch_tool, tool_search_programs

router = APIRouter(tags=["mcp"])

_SENTINEL_USER = UUID(int=0)  # search_programs ignores user_id (catalog-wide)
_PROTOCOL_VERSION = "2025-06-18"

# ── Tool catalog advertised via tools/list ────────────────────────────────
_STUDENT_ID = {
    "student_id": {
        "type": "string",
        "description": "The student's UniPaith id (StudentProfile id or User id).",
    }
}
_TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "get_profile",
        "description": (
            "Load everything UniPaith knows about a student: profile, goals, "
            "needs, identity, active strategy, and journey completion."
        ),
        "inputSchema": {"type": "object", "properties": _STUDENT_ID, "required": ["student_id"]},
    },
    {
        "name": "create_profile",
        "description": "Idempotently ensure a student's profile exists; returns its id.",
        "inputSchema": {
            "type": "object",
            "properties": {**_STUDENT_ID, "initial_data": {"type": "object"}},
            "required": ["student_id"],
        },
    },
    {
        "name": "save_signals",
        "description": (
            "Persist signals learned about a student. `signals` is a list of "
            "{type: goal|need|value|belief|fact, content, evidence, completeness?}."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                **_STUDENT_ID,
                "signals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["goal", "need", "value", "belief", "fact"],
                            },
                            "content": {"type": "string"},
                            "evidence": {"type": "string"},
                            "completeness": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["type", "content", "evidence"],
                    },
                },
            },
            "required": ["student_id", "signals"],
        },
    },
    {
        "name": "get_matches",
        "description": "Return a student's program matches (gated on discovery readiness).",
        "inputSchema": {"type": "object", "properties": _STUDENT_ID, "required": ["student_id"]},
    },
    {
        "name": "search_programs",
        "description": (
            "Search UniPaith's published program catalog. Catalog-wide; needs no student."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Natural-language query."}},
            "required": ["query"],
        },
    },
    {
        "name": "generate_strategy",
        "description": "Generate a student's broad strategy (career → degree → paths + narrative).",
        "inputSchema": {"type": "object", "properties": _STUDENT_ID, "required": ["student_id"]},
    },
]
_TOOL_NAMES = {t["name"] for t in _TOOL_DEFS}


async def _user_id_for_student(db: AsyncSession, sid: str | None) -> UUID | None:
    """Resolve a caller-supplied student id (StudentProfile id OR User id) to the
    user id the service layer keys on. All-data: any valid id resolves."""
    if not sid:
        return None
    try:
        candidate = UUID(str(sid))
    except (ValueError, AttributeError, TypeError):
        return None
    by_profile = (
        await db.execute(select(StudentProfile.user_id).where(StudentProfile.id == candidate))
    ).scalar_one_or_none()
    if by_profile is not None:
        return by_profile
    return (
        await db.execute(select(StudentProfile.user_id).where(StudentProfile.user_id == candidate))
    ).scalar_one_or_none()


async def _call_tool(params: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments") or {}
    if name not in _TOOL_NAMES:
        return _content({"error": f"unknown_tool:{name}"}, is_error=True)
    if name == "search_programs":
        out = await tool_search_programs(db, _SENTINEL_USER, args)
    else:
        user_id = await _user_id_for_student(db, args.get("student_id"))
        if user_id is None:
            out = {"error": f"student_not_found:{args.get('student_id')}"}
        else:
            out = await dispatch_tool(db, user_id, name, args, session_id=None)
    return _content(out)


def _content(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "content": [{"type": "text", "text": json.dumps(payload, default=str)}]
    }
    if is_error:
        result["isError"] = True
    return result


async def _handle_rpc(msg: dict[str, Any], db: AsyncSession) -> dict[str, Any] | None:
    """Handle one JSON-RPC message; returns the response, or None for a
    notification (no id) which the transport answers with HTTP 202."""
    mid = msg.get("id")
    method = msg.get("method")
    if mid is None:
        return None  # notification (e.g. notifications/initialized)
    try:
        if method == "initialize":
            requested = (msg.get("params") or {}).get("protocolVersion") or _PROTOCOL_VERSION
            result: dict[str, Any] = {
                "protocolVersion": requested,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "unipaith", "version": "1.0.0"},
            }
        elif method == "tools/list":
            result = {"tools": _TOOL_DEFS}
        elif method == "tools/call":
            result = await _call_tool(msg.get("params") or {}, db)
        elif method == "ping":
            result = {}
        else:
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32601, "message": f"method not found: {method}"},
            }
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    except Exception as exc:  # never 5xx the connector
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(exc)[:300]}}


def _authorized(request: Request) -> bool:
    expected = settings.unipaith_mcp_api_key
    if not expected:
        return False
    auth = request.headers.get("authorization", "")
    return auth == f"Bearer {expected}"


async def _serve(request: Request, db: AsyncSession) -> Response:
    if not _authorized(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}},
            status_code=400,
        )
    if isinstance(body, list):  # JSON-RPC batch
        responses = [r for r in [await _handle_rpc(m, db) for m in body] if r is not None]
        return JSONResponse(responses) if responses else Response(status_code=202)
    resp = await _handle_rpc(body, db)
    if resp is None:
        return Response(status_code=202)
    return JSONResponse(resp)


@router.post("/mcp")
async def mcp_endpoint(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    return await _serve(request, db)


@router.post("/mcp/")
async def mcp_endpoint_slash(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    return await _serve(request, db)


@router.get("/mcp")
async def mcp_get() -> Response:
    # Stateless server — no server→client SSE channel on GET.
    return Response(status_code=405)
