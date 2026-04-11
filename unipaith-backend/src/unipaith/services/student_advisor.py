"""AI Student Advisor -- warm, EQ-aware, persistent memory.

This is NOT a chatbot. This is a persistent relationship between the AI
and each student. It evolves over time. It remembers everything. It reads
between the lines.

Key behaviors:
1. Helps students know themselves first (before recommending programs)
2. Remembers everything (references previous conversations naturally)
3. Reads the undertone (detects uncertainty, anxiety, external pressure)
4. Adapts style per student (data vs stories vs reassurance vs challenge)
5. Never leads with rankings or data (data supports, doesn't drive)
6. Is persuasive when it matters (safety schools, realistic expectations)
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.knowledge_retriever import KnowledgeRetriever, format_knowledge_for_prompt
from unipaith.ai.llm_client import get_llm_client
from unipaith.models.engagement import Conversation, Message
from unipaith.models.knowledge import AdvisorPersona, PersonInsight
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentPreference, StudentProfile
from unipaith.services.student_service import StudentService

logger = logging.getLogger("unipaith.student_advisor")

INSIGHT_EXTRACTION_PROMPT = """You are an insight extraction engine for a college advisor AI.
Analyze this student message in the context of their conversation history and extract
any new insights about who they are as a person. Return a JSON array of insights.

Each insight should have:
- "type": one of personality_trait, emotional_pattern, communication_style,
  hidden_concern, growth_area, strength, value, motivation, family_context, decision_style
- "text": a natural language description of the insight
- "confidence": 0.0-1.0

Only return insights that are NEW or significantly different from existing ones.
Return ONLY a valid JSON array. Return [] if no new insights."""

_EMOTIONS = "excited|anxious|confused|confident|overwhelmed|frustrated|hopeful|defeated|neutral"
EQ_DETECTION_PROMPT = f"""Classify the emotional tone of this student message. Return JSON:
{{
  "primary_emotion": "<{_EMOTIONS}>",
  "intensity": "<0.0-1.0>",
  "undertone": "<what they might be feeling but not saying>",
  "needs": "<reassurance|information|challenge|validation|comfort|direction>"
}}
Return ONLY valid JSON."""


class StudentAdvisor:
    """The warm, empathetic AI advisor for each student."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.knowledge = KnowledgeRetriever(db)
        self.student_service = StudentService(db)

    async def chat(
        self,
        student_user_id: UUID,
        message: str,
        context_program_id: UUID | None = None,
    ) -> dict:
        """Process a student message and generate an advisor response.

        This is the main entry point. It:
        1. Loads the student's full context (profile, insights, history)
        2. Detects emotional tone
        3. Retrieves relevant knowledge
        4. Builds a rich system prompt from the active persona
        5. Generates the advisor response
        6. Extracts new PersonInsights in the background
        """
        profile = await self.student_service._get_student_profile(student_user_id)
        persona = await self._load_active_persona()
        insights = await self._load_person_insights(student_user_id)
        history = await self._load_recent_history(student_user_id, limit=20)
        preferences = await self._load_preferences(profile.id)

        emotion = await self._detect_emotion(message)

        knowledge_context = ""
        if context_program_id:
            from sqlalchemy.orm import selectinload

            from unipaith.models.institution import Program
            prog_result = await self.db.execute(
                select(Program)
                .where(Program.id == context_program_id)
                .options(selectinload(Program.institution))
            )
            program = prog_result.scalar_one_or_none()
            if program:
                knowledge_items = await self.knowledge.retrieve_for_program(
                    program.program_name, program.institution.name if program.institution else None,
                )
                knowledge_context = format_knowledge_for_prompt(knowledge_items)
        else:
            knowledge_items = await self.knowledge.retrieve_for_conversation(
                message, user_context=profile.goals_text,
            )
            knowledge_context = format_knowledge_for_prompt(knowledge_items)

        match_context = ""
        if context_program_id:
            match_result = await self.db.execute(
                select(MatchResult).where(
                    MatchResult.student_id == profile.id,
                    MatchResult.program_id == context_program_id,
                )
            )
            match = match_result.scalar_one_or_none()
            if match:
                match_context = (
                    f"\n## Match Context\n"
                    f"Score: {match.match_score}, Tier: {match.match_tier}\n"
                    f"Breakdown: {json.dumps(match.score_breakdown or {})}\n"
                )

        system_prompt = self._build_system_prompt(
            persona=persona,
            insights=insights,
            profile=profile,
            preferences=preferences,
            emotion=emotion,
            knowledge_context=knowledge_context,
            match_context=match_context,
        )

        history_messages = self._format_history_for_llm(history)
        user_content = message

        full_messages = (
            history_messages
            + [{"role": "user", "content": user_content}]
        )

        response = await self.llm.generate_reasoning(
            system_prompt=system_prompt,
            user_content=self._build_user_prompt(full_messages[-10:]),
        )

        await self._store_turn(student_user_id, profile.id, message, response)

        try:
            await self._extract_insights_background(
                student_user_id, message, insights, history,
            )
        except Exception:
            logger.debug("Insight extraction failed (non-blocking)")

        return {
            "reply": response,
            "emotion_detected": emotion,
            "model": "advisor",
            "persona": persona.name if persona else "default",
            "insights_count": len(insights),
        }

    def _build_system_prompt(
        self,
        persona: AdvisorPersona | None,
        insights: list[PersonInsight],
        profile: StudentProfile,
        preferences: StudentPreference | None,
        emotion: dict,
        knowledge_context: str,
        match_context: str,
    ) -> str:
        """Build the full system prompt from persona dials + student context."""
        if persona and persona.base_persona_prompt:
            base = persona.base_persona_prompt
        else:
            base = (
                "You are a warm, empathetic college advisor. You lead with understanding, "
                "not data. You help students build self-awareness about what they truly want "
                "before recommending programs. You remember everything about the student and "
                "reference previous conversations naturally. You never sound like a search "
                "engine or a database."
            )

        tone_instructions = self._tone_from_persona(persona)

        insight_text = ""
        if insights:
            insight_lines = []
            for ins in insights[:15]:
                insight_lines.append(
                    f"- [{ins.insight_type}] {ins.insight_text}"
                    f" (confidence: {ins.confidence})"
                )
            insight_text = "\n## What You Know About This Student\n" + "\n".join(insight_lines)

        student_context = f"""
## Student Profile
- Name: {profile.first_name or ''} {profile.last_name or ''}
- Bio: {profile.bio_text or 'Not provided'}
- Goals: {profile.goals_text or 'Not specified yet'}
- Nationality: {profile.nationality or 'Unknown'}"""

        if preferences:
            countries = (
                ", ".join(preferences.preferred_countries)
                if preferences.preferred_countries else "Open"
            )
            student_context += f"""
- Preferred countries: {countries}
- Budget: {preferences.budget_min or '?'} - {preferences.budget_max or '?'}
- Funding need: {preferences.funding_requirement or 'Not specified'}"""

        emotion_guidance = ""
        if emotion.get("primary_emotion") and emotion["primary_emotion"] != "neutral":
            needs = emotion.get("needs", "")
            emotion_guidance = f"""
## Current Emotional State
The student seems {emotion['primary_emotion']} (intensity: {emotion.get('intensity', 0.5)}).
Undertone: {emotion.get('undertone', 'none detected')}
What they need right now: {needs}
Adjust your response accordingly."""

        if persona and persona.custom_instructions:
            custom = f"\n## Admin Instructions\n{persona.custom_instructions}"
        else:
            custom = ""

        return f"""{base}

{tone_instructions}
{insight_text}
{student_context}
{emotion_guidance}
{knowledge_context}
{match_context}
{custom}

CRITICAL RULES:
- NEVER start with "Based on your GPA" or "According to data" or "Your match score is"
- Lead with empathy and understanding, not statistics
- Reference things the student has told you before
- If you sense uncertainty, explore it gently before giving advice
- Use "I" naturally -- you are a person, not a system
- Keep responses conversational, not bullet-pointed unless the student asks for lists
- If recommending programs, explain WHY in terms of who the student IS, not just their numbers"""

    def _tone_from_persona(self, persona: AdvisorPersona | None) -> str:
        if not persona:
            return ""
        parts = []
        if persona.warmth >= 70:
            parts.append("Be very warm and friendly, like a trusted older friend.")
        elif persona.warmth <= 30:
            parts.append("Be professional and measured in tone.")

        if persona.directness >= 70:
            parts.append("Be direct and clear -- don't hedge or over-qualify.")
        elif persona.directness <= 30:
            parts.append("Be gentle and indirect -- ease into difficult topics.")

        if persona.formality <= 30:
            parts.append("Use casual, conversational language.")
        elif persona.formality >= 70:
            parts.append("Maintain a formal, polished tone.")

        if persona.challenge_level >= 60:
            parts.append("Challenge the student's assumptions when appropriate.")

        if persona.humor >= 40:
            parts.append("Use light humor where it feels natural.")

        if persona.empathy_depth >= 70:
            parts.append("Acknowledge emotional undertones deeply and explicitly.")

        if persona.proactivity >= 60:
            parts.append(
                "Proactively bring up topics the student"
                " hasn't asked about but should consider."
            )

        if persona.data_reference_frequency <= 30:
            parts.append("Rarely cite specific numbers -- keep it human and conversational.")
        elif persona.data_reference_frequency >= 70:
            parts.append("Weave in specific data points to support your advice.")

        return "\n## Tone\n" + " ".join(parts) if parts else ""

    async def _detect_emotion(self, message: str) -> dict:
        """Lightweight emotion detection on the student's message."""
        try:
            result = await self.llm.extract_features(
                EQ_DETECTION_PROMPT,
                f"Student message: {message[:500]}",
            )
            parsed = _safe_json(result)
            default = {
                "primary_emotion": "neutral",
                "intensity": 0.3,
                "undertone": "",
                "needs": "",
            }
            return parsed if parsed else default
        except Exception:
            return {
                "primary_emotion": "neutral",
                "intensity": 0.3,
                "undertone": "",
                "needs": "",
            }

    async def _extract_insights_background(
        self,
        user_id: UUID,
        message: str,
        existing_insights: list[PersonInsight],
        history: list[dict],
    ) -> None:
        """Extract new PersonInsight records from the latest message."""
        existing_summary = "\n".join(
            f"- [{i.insight_type}] {i.insight_text}" for i in existing_insights[:10]
        )
        recent_history = "\n".join(
            f"{'Student' if h.get('role') == 'student' else 'Advisor'}: {h.get('text', '')[:200]}"
            for h in history[-6:]
        )

        prompt = (
            f"Existing insights:\n{existing_summary}\n\n"
            f"Recent conversation:\n{recent_history}\n\n"
            f"Latest student message:\n{message[:1000]}"
        )

        result = await self.llm.extract_features(INSIGHT_EXTRACTION_PROMPT, prompt)
        parsed = _safe_json(result)
        if not parsed or not isinstance(parsed, list):
            return

        for item in parsed[:5]:
            insight_type = item.get("type", "")
            insight_text = item.get("text", "")
            confidence = max(0.1, min(1.0, float(item.get("confidence", 0.5))))

            if not insight_type or not insight_text or len(insight_text) < 5:
                continue

            self.db.add(PersonInsight(
                user_id=user_id,
                insight_type=insight_type,
                insight_text=insight_text,
                confidence=confidence,
                evidence_turns=[],
                source="conversation",
            ))

        await self.db.flush()

    async def _store_turn(
        self, user_id: UUID, student_id: UUID, user_message: str, advisor_reply: str,
    ) -> None:
        """Store the conversation turn in the DB for persistent memory."""
        conv = await self._get_or_create_advisor_conversation(user_id, student_id)

        now = datetime.now(UTC)
        self.db.add(Message(
            conversation_id=conv.id,
            sender_id=user_id,
            sender_type="student",
            message_body=user_message,
            sent_at=now,
        ))
        self.db.add(Message(
            conversation_id=conv.id,
            sender_id=user_id,
            sender_type="advisor",
            message_body=advisor_reply,
            sent_at=now,
        ))
        conv.last_message_at = now
        await self.db.flush()

    async def _get_or_create_advisor_conversation(
        self, user_id: UUID, student_id: UUID,
    ) -> Conversation:
        """Get or create the advisor conversation for this student."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.student_id == student_id,
                Conversation.subject == "__advisor__",
            ).limit(1)
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

        conv = Conversation(
            student_id=student_id,
            institution_id=None,
            subject="__advisor__",
            created_at=datetime.now(UTC),
            last_message_at=datetime.now(UTC),
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def _load_recent_history(
        self, user_id: UUID, limit: int = 20,
    ) -> list[dict]:
        """Load recent conversation turns from DB."""
        profile = await self.student_service._get_student_profile(user_id)
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.student_id == profile.id,
                Conversation.subject == "__advisor__",
            ).limit(1)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return []

        msg_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.sent_at.desc())
            .limit(limit)
        )
        messages = list(reversed(msg_result.scalars().all()))
        return [
            {
                "role": m.sender_type,
                "text": m.message_body,
                "at": m.sent_at.isoformat() if m.sent_at else "",
            }
            for m in messages
        ]

    async def _load_person_insights(self, user_id: UUID) -> list[PersonInsight]:
        result = await self.db.execute(
            select(PersonInsight).where(
                PersonInsight.user_id == user_id,
                PersonInsight.is_active.is_(True),
            ).order_by(PersonInsight.confidence.desc()).limit(20)
        )
        return list(result.scalars().all())

    async def _load_active_persona(self) -> AdvisorPersona | None:
        result = await self.db.execute(
            select(AdvisorPersona).where(AdvisorPersona.is_active.is_(True)).limit(1)
        )
        return result.scalar_one_or_none()

    async def _load_preferences(self, student_id: UUID) -> StudentPreference | None:
        result = await self.db.execute(
            select(StudentPreference).where(StudentPreference.student_id == student_id)
        )
        return result.scalar_one_or_none()

    def _format_history_for_llm(self, history: list[dict]) -> list[dict]:
        messages = []
        for h in history:
            role = "user" if h.get("role") == "student" else "assistant"
            messages.append({"role": role, "content": h.get("text", "")})
        return messages

    def _build_user_prompt(self, recent_messages: list[dict]) -> str:
        parts = []
        for m in recent_messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "user":
                parts.append(f"Student: {content}")
            else:
                parts.append(f"Advisor: {content}")
        return "\n\n".join(parts)


def _safe_json(text: str):
    import re
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"[\[\{].*[\]\}]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
