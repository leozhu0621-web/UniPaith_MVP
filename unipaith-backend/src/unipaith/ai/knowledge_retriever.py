"""Knowledge RAG retrieval layer.

Retrieves relevant knowledge documents for any query using:
- Semantic (vector) similarity search via pgvector
- Entity-based retrieval via KnowledgeLink
- Hybrid scoring combining both signals
- Recency and quality weighting

Feeds knowledge into all serving systems: advisor, recommendations,
institution intelligence.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.embedding_client import get_embedding_client
from unipaith.models.knowledge import KnowledgeDocument, KnowledgeLink

logger = logging.getLogger("unipaith.knowledge_retriever")


class RetrievedKnowledge:
    """A piece of retrieved knowledge with relevance scoring."""

    __slots__ = (
        "document_id",
        "title",
        "summary",
        "text",
        "source_url",
        "content_type",
        "score",
        "retrieval_method",
        "facts",
    )

    def __init__(
        self,
        document_id: UUID,
        title: str | None,
        summary: str | None,
        text: str,
        source_url: str | None,
        content_type: str | None,
        score: float,
        retrieval_method: str,
        facts: list[dict] | None = None,
    ):
        self.document_id = document_id
        self.title = title
        self.summary = summary
        self.text = text
        self.source_url = source_url
        self.content_type = content_type
        self.score = score
        self.retrieval_method = retrieval_method
        self.facts = facts


class KnowledgeRetriever:
    """Retrieves knowledge relevant to a query or entity."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_client = get_embedding_client()

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        entity_name: str | None = None,
        min_quality: float = 0.3,
        recency_days: int | None = None,
    ) -> list[RetrievedKnowledge]:
        """Hybrid retrieval: vector similarity + entity links + quality/recency."""
        results: dict[UUID, RetrievedKnowledge] = {}

        semantic_results = await self._semantic_search(
            query,
            limit=limit * 2,
            min_quality=min_quality,
            recency_days=recency_days,
        )
        for item in semantic_results:
            results[item.document_id] = item

        if entity_type or entity_name:
            entity_results = await self._entity_search(
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                limit=limit,
                min_quality=min_quality,
            )
            for item in entity_results:
                if item.document_id in results:
                    results[item.document_id].score = max(
                        results[item.document_id].score,
                        item.score * 1.2,
                    )
                    results[item.document_id].retrieval_method = "hybrid"
                else:
                    results[item.document_id] = item

        ranked = sorted(results.values(), key=lambda r: r.score, reverse=True)
        return ranked[:limit]

    async def retrieve_for_program(
        self,
        program_name: str,
        institution_name: str | None = None,
        limit: int = 8,
    ) -> list[RetrievedKnowledge]:
        """Retrieve knowledge specifically about a program/institution."""
        query_parts = [program_name]
        if institution_name:
            query_parts.append(institution_name)
        query = " ".join(query_parts) + " admissions graduate program"

        return await self.retrieve(
            query=query,
            limit=limit,
            entity_type="program" if not institution_name else None,
            entity_name=program_name,
        )

    async def retrieve_for_student_context(
        self,
        interests: list[str],
        goals: str | None = None,
        limit: int = 6,
    ) -> list[RetrievedKnowledge]:
        """Retrieve knowledge relevant to a student's interests and goals."""
        query_parts = interests[:5]
        if goals:
            query_parts.append(goals[:200])
        query = " ".join(query_parts) + " graduate programs admissions"

        return await self.retrieve(query=query, limit=limit)

    async def retrieve_for_conversation(
        self,
        message: str,
        user_context: str | None = None,
        limit: int = 5,
    ) -> list[RetrievedKnowledge]:
        """Retrieve knowledge to support a conversation response."""
        query = message[:500]
        if user_context:
            query = f"{user_context[:200]} {query}"

        return await self.retrieve(query=query, limit=limit, min_quality=0.4)

    async def _semantic_search(
        self,
        query: str,
        limit: int,
        min_quality: float,
        recency_days: int | None,
    ) -> list[RetrievedKnowledge]:
        try:
            query_embedding = await self.embedding_client.embed_text(query[:2000])
        except Exception:
            logger.warning("Embedding generation failed for RAG query")
            return []

        vec_str = "[" + ",".join(str(float(v)) for v in query_embedding) + "]"

        where_clauses = [
            "kd.processing_status = 'completed'",
            "kd.is_active = true",
            "kd.embedding IS NOT NULL",
        ]
        params: dict = {"query_vec": vec_str, "limit": limit}

        if min_quality > 0:
            where_clauses.append("(kd.quality_score IS NULL OR kd.quality_score >= :min_quality)")
            params["min_quality"] = min_quality

        if recency_days:
            where_clauses.append("kd.ingested_at >= :min_date")
            params["min_date"] = datetime.now(UTC) - timedelta(days=recency_days)

        where_sql = " AND ".join(where_clauses)

        sql = text(f"""
            SELECT kd.id, kd.title, kd.summary, kd.extracted_text, kd.source_url,
                   kd.content_type, kd.quality_score, kd.extracted_facts,
                   1 - (kd.embedding <=> cast(:query_vec as vector)) as similarity
            FROM knowledge_documents kd
            WHERE {where_sql}
            ORDER BY kd.embedding <=> cast(:query_vec as vector)
            LIMIT :limit
        """)

        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        return [
            RetrievedKnowledge(
                document_id=row[0],
                title=row[1],
                summary=row[2],
                text=(row[3] or "")[:2000],
                source_url=row[4],
                content_type=row[5],
                score=float(row[8]) * (float(row[6]) if row[6] else 0.5),
                retrieval_method="semantic",
                facts=row[7],
            )
            for row in rows
            if row[8] and float(row[8]) > 0.1
        ]

    async def _entity_search(
        self,
        entity_type: str | None,
        entity_id: UUID | None,
        entity_name: str | None,
        limit: int,
        min_quality: float,
    ) -> list[RetrievedKnowledge]:
        query = (
            select(
                KnowledgeDocument.id,
                KnowledgeDocument.title,
                KnowledgeDocument.summary,
                KnowledgeDocument.extracted_text,
                KnowledgeDocument.source_url,
                KnowledgeDocument.content_type,
                KnowledgeDocument.quality_score,
                KnowledgeDocument.extracted_facts,
                KnowledgeLink.confidence,
            )
            .join(KnowledgeLink, KnowledgeLink.document_id == KnowledgeDocument.id)
            .where(
                KnowledgeDocument.processing_status == "completed",
                KnowledgeDocument.is_active.is_(True),
            )
        )

        if entity_type:
            query = query.where(KnowledgeLink.entity_type == entity_type)
        if entity_id:
            query = query.where(KnowledgeLink.entity_id == entity_id)
        if entity_name:
            escaped = entity_name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.where(KnowledgeLink.entity_name.ilike(f"%{escaped}%"))
        if min_quality > 0:
            query = query.where(
                (KnowledgeDocument.quality_score.is_(None))
                | (KnowledgeDocument.quality_score >= min_quality)
            )

        query = query.order_by(KnowledgeLink.confidence.desc()).limit(limit)
        result = await self.db.execute(query)

        return [
            RetrievedKnowledge(
                document_id=row[0],
                title=row[1],
                summary=row[2],
                text=(row[3] or "")[:2000],
                source_url=row[4],
                content_type=row[5],
                score=float(row[8]) * (float(row[6]) if row[6] else 0.5),
                retrieval_method="entity",
                facts=row[7],
            )
            for row in result.fetchall()
        ]


def format_knowledge_for_prompt(
    knowledge: list[RetrievedKnowledge],
    max_chars: int = 4000,
) -> str:
    """Format retrieved knowledge into a prompt-friendly string."""
    if not knowledge:
        return ""

    parts = ["## Relevant Knowledge\n"]
    chars_used = len(parts[0])

    for i, item in enumerate(knowledge, 1):
        section = f"### Source {i}"
        if item.title:
            section += f": {item.title}"
        section += "\n"

        if item.summary:
            section += f"{item.summary}\n"

        if item.facts:
            for fact in item.facts[:3]:
                stmt = fact.get("statement", "")
                if stmt:
                    section += f"- {stmt}\n"

        if item.source_url:
            section += f"(Source: {item.source_url})\n"

        section += "\n"

        if chars_used + len(section) > max_chars:
            break
        parts.append(section)
        chars_used += len(section)

    return "".join(parts)
