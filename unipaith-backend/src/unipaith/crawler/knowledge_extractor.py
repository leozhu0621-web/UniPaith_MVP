"""Format-aware knowledge extraction pipeline.

Takes raw content from any source/format, classifies it, extracts structured
knowledge using LLM, links to entities, and generates embeddings for the
knowledge_documents table.
"""
from __future__ import annotations

import hashlib
import logging
import re
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.embedding_client import get_embedding_client
from unipaith.ai.llm_client import get_llm_client
from unipaith.models.knowledge import (
    KnowledgeDocument,
    KnowledgeLink,
)

logger = logging.getLogger("unipaith.knowledge_extractor")

CONTENT_FORMATS = {
    "webpage", "video_transcript", "social_post", "academic_paper",
    "government_dataset", "podcast_transcript", "document",
    "api_response", "rss_entry",
}

CLASSIFY_PROMPT = """Analyze this content and return a JSON object with:
{
  "content_type": "<admissions|program_info|student_experience|
    ranking|financial_aid|research|career_outcomes|other>",
  "quality_estimate": <0.0-1.0>,
  "credibility_estimate": <0.0-1.0>,
  "language": "<en|zh|es|...>",
  "title": "<extracted or inferred title>",
  "summary": "<2-3 sentence summary of key information>"
}
Return ONLY valid JSON."""

EXTRACT_PROMPT = """You are a knowledge extraction engine for a university admissions platform.
Extract structured knowledge from this content. Return a JSON object with:
{
  "entities": [
    {"name": "<name>", "type": "<institution|program|field|country|person>",
     "confidence": <0.0-1.0>}
  ],
  "facts": [
    {"statement": "<claim>", "confidence": <0.0-1.0>,
     "category": "<admissions|ranking|financial|outcome|requirement|other>"}
  ],
  "key_topics": ["<topic1>", "<topic2>"],
  "relevance_to_admissions": <0.0-1.0>
}
Return ONLY valid JSON."""

LINK_PROMPT = """Given these extracted entities from a knowledge document, identify which
existing database entities they likely refer to. For each entity, provide:
{
  "entity_name": "<name>",
  "entity_type": "<institution|program|field|country>",
  "relationship": "<describes|mentions|ranks|reviews|compares|recommends>",
  "confidence": <0.0-1.0>
}
Return a JSON array. Return ONLY valid JSON."""


class KnowledgeExtractor:
    """Processes raw content into structured knowledge documents."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.embedding_client = get_embedding_client()

    async def process_raw_content(
        self,
        raw_text: str,
        source_url: str | None = None,
        content_format: str = "webpage",
        frontier_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> KnowledgeDocument | None:
        if not raw_text or len(raw_text.strip()) < 50:
            logger.debug("Skipping content too short: %d chars", len(raw_text or ""))
            return None

        if content_format not in CONTENT_FORMATS:
            content_format = "webpage"

        domain = urlparse(source_url).netloc if source_url else None
        hashlib.sha256(raw_text[:2000].encode()).hexdigest()

        existing = await self.db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.source_url == source_url,
            ).limit(1)
        ) if source_url else None
        if existing and existing.scalar_one_or_none():
            logger.debug("Duplicate source_url, skipping: %s", source_url)
            return None

        doc = KnowledgeDocument(
            source_url=source_url,
            source_domain=domain,
            content_format=content_format,
            raw_text=raw_text[:500_000],
            crawl_frontier_id=frontier_id,
            metadata_json=metadata or {},
            processing_status="processing",
        )
        self.db.add(doc)
        await self.db.flush()

        try:
            await self._classify(doc, raw_text)
            await self._extract(doc, raw_text)
            await self._link_entities(doc)
            await self._generate_embedding(doc)
            doc.processing_status = "completed"
            doc.word_count = len(raw_text.split())
        except Exception:
            logger.exception("Knowledge extraction failed for %s", source_url or doc.id)
            doc.processing_status = "failed"
            doc.processing_error = "extraction_failed"

        await self.db.flush()
        return doc

    async def _classify(self, doc: KnowledgeDocument, raw_text: str) -> None:
        truncated = raw_text[:4000]
        prompt = f"{CLASSIFY_PROMPT}\n\n---\nContent ({doc.content_format}):\n{truncated}"
        response = await self.llm.extract_features(
            "You are a content classification engine.", prompt,
        )
        parsed = _safe_parse_json(response)
        if not parsed:
            return

        doc.content_type = parsed.get("content_type", "other")
        doc.quality_score = _clamp(parsed.get("quality_estimate", 0.5))
        doc.credibility_score = _clamp(parsed.get("credibility_estimate", 0.5))
        doc.language = parsed.get("language", "en")
        doc.title = parsed.get("title")
        doc.summary = parsed.get("summary")

    async def _extract(self, doc: KnowledgeDocument, raw_text: str) -> None:
        truncated = raw_text[:6000]
        prompt = f"{EXTRACT_PROMPT}\n\n---\nContent:\n{truncated}"
        response = await self.llm.extract_features(
            "You are a knowledge extraction engine.", prompt,
        )
        parsed = _safe_parse_json(response)
        if not parsed:
            return

        doc.extracted_entities = parsed.get("entities", [])
        doc.extracted_facts = parsed.get("facts", [])
        doc.extracted_text = truncated
        doc.relevance_score = _clamp(parsed.get("relevance_to_admissions", 0.5))

    async def _link_entities(self, doc: KnowledgeDocument) -> None:
        entities = doc.extracted_entities or []
        if not entities:
            return

        for entity_data in entities[:20]:
            name = entity_data.get("name", "")
            etype = entity_data.get("type", "unknown")
            confidence = _clamp(entity_data.get("confidence", 0.5))

            if not name or len(name) < 2:
                continue

            link = KnowledgeLink(
                document_id=doc.id,
                entity_type=etype,
                entity_name=name,
                relationship_type="mentions",
                confidence=confidence,
            )
            self.db.add(link)

        await self.db.flush()

    async def _generate_embedding(self, doc: KnowledgeDocument) -> None:
        text_for_embedding = _build_embedding_text(doc)
        if not text_for_embedding or len(text_for_embedding) < 20:
            return

        try:
            embedding = await self.embedding_client.embed_text(text_for_embedding[:8000])
            doc.embedding = embedding
        except Exception:
            logger.warning("Embedding generation failed for doc %s", doc.id)

    async def reprocess_document(self, doc_id: UUID) -> KnowledgeDocument | None:
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        if not doc or not doc.raw_text:
            return None

        doc.processing_status = "processing"
        await self.db.flush()

        try:
            await self._classify(doc, doc.raw_text)
            await self._extract(doc, doc.raw_text)
            await self._link_entities(doc)
            await self._generate_embedding(doc)
            doc.processing_status = "completed"
        except Exception:
            logger.exception("Reprocess failed for doc %s", doc_id)
            doc.processing_status = "failed"

        await self.db.flush()
        return doc


def _build_embedding_text(doc: KnowledgeDocument) -> str:
    parts = []
    if doc.title:
        parts.append(f"Title: {doc.title}")
    if doc.summary:
        parts.append(f"Summary: {doc.summary}")
    if doc.content_type:
        parts.append(f"Type: {doc.content_type}")
    if doc.extracted_text:
        parts.append(doc.extracted_text[:3000])
    elif doc.raw_text:
        parts.append(doc.raw_text[:3000])
    return "\n".join(parts)


def _safe_parse_json(text: str) -> dict | None:
    import json
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def _clamp(value: float | None, lo: float = 0.0, hi: float = 1.0) -> float:
    if value is None:
        return 0.5
    return max(lo, min(hi, float(value)))
