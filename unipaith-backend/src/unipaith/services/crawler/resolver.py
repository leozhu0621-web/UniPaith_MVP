"""Spec 60 §6 step (5) — entity resolution.

Links extracted facts to a canonical ``knowledge_entities`` node (get-or-create
by ``entity_type`` + ``canonical_key``) and records a ``knowledge_links`` edge
from the source document to that node, so the raw graph and the clean projection
stay connected (§2).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.crawler import KnowledgeEntity
from unipaith.models.knowledge import KnowledgeLink
from unipaith.services.crawler.util import to_jsonable


class EntityResolver:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve(
        self,
        *,
        entity_type: str,
        canonical_key: str | None,
        canonical_name: str,
        domain: str | None = None,
        source: str = "crawled",
        confidence: float = 0.6,
        source_url: str | None = None,
        source_domain: str | None = None,
        source_document_id: UUID | None = None,
        attributes: dict | None = None,
    ) -> KnowledgeEntity:
        attributes = to_jsonable(attributes or {})
        entity: KnowledgeEntity | None = None
        if canonical_key:
            result = await self.db.execute(
                select(KnowledgeEntity).where(
                    KnowledgeEntity.entity_type == entity_type,
                    KnowledgeEntity.canonical_key == canonical_key,
                )
            )
            entity = result.scalar_one_or_none()

        if entity is None:
            entity = KnowledgeEntity(
                entity_type=entity_type,
                canonical_key=canonical_key,
                canonical_name=canonical_name,
                domain=domain,
                attributes=attributes,
                source=source,
                confidence=confidence,
                source_url=source_url,
                source_domain=source_domain,
                source_document_id=source_document_id,
                status="live"
                if source in ("seed", "corroborated", "first_party")
                else "provisional",
            )
            self.db.add(entity)
            await self.db.flush()
        else:
            # Merge attributes; keep the strongest confidence seen.
            if attributes:
                merged = dict(entity.attributes or {})
                merged.update(attributes)
                entity.attributes = merged
            if confidence > (entity.confidence or 0):
                entity.confidence = confidence
            entity.canonical_name = canonical_name or entity.canonical_name

        return entity

    async def link_document(
        self,
        *,
        document_id: UUID,
        entity: KnowledgeEntity,
        relationship_type: str = "describes",
        confidence: float = 0.6,
    ) -> KnowledgeLink:
        link = KnowledgeLink(
            document_id=document_id,
            entity_type=entity.entity_type,
            entity_id=entity.id,
            entity_name=entity.canonical_name,
            relationship_type=relationship_type,
            confidence=confidence,
        )
        self.db.add(link)
        await self.db.flush()
        return link
