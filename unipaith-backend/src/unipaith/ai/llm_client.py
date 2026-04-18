"""
Unified LLM client for all AI operations.
Uses OpenAI-compatible API (works with vLLM, OpenAI, Anthropic via proxy, etc.)

Three modes controlled by settings.gpu_mode:
- "mock": returns synthetic responses (dev/testing, $0)
- "local": calls localhost vLLM endpoints (local GPU)
- "aws": calls AWS GPU instances with auto-start/stop for 70B
"""

from __future__ import annotations

import asyncio
import logging

from openai import AsyncOpenAI

from unipaith.config import settings
from unipaith.core.ai_runtime_metrics import record_llm, start_timer

logger = logging.getLogger("unipaith.llm_client")


class LLMClient:
    """Handles all LLM interactions. Model-agnostic via OpenAI-compatible API."""

    def __init__(self):
        self.feature_client = AsyncOpenAI(
            base_url=settings.llm_feature_base_url,
            api_key=settings.llm_feature_api_key,
        )
        self.reasoning_client = AsyncOpenAI(
            base_url=settings.llm_reasoning_base_url,
            api_key=settings.llm_reasoning_api_key,
        )

    async def extract_features(self, system_prompt: str, user_content: str) -> str:
        """Call feature extraction model. Returns raw text response."""
        response = await self._call_with_resilience(
            self.feature_client,
            model=settings.llm_feature_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.llm_feature_max_tokens,
            temperature=settings.llm_feature_temperature,
        )
        return response.choices[0].message.content or ""

    async def generate_reasoning(self, system_prompt: str, user_content: str) -> str:
        """Call reasoning model for natural-language explanations."""
        response = await self._call_with_resilience(
            self.reasoning_client,
            model=settings.llm_reasoning_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.llm_reasoning_max_tokens,
            temperature=settings.llm_reasoning_temperature,
        )
        return response.choices[0].message.content or ""

    async def _call_with_resilience(self, client: AsyncOpenAI, **kwargs):
        last_error: Exception | None = None
        for attempt in range(1, settings.ai_request_max_retries + 1):
            started = start_timer()
            try:
                response = await asyncio.wait_for(
                    client.chat.completions.create(**kwargs),
                    timeout=settings.ai_request_timeout_seconds,
                )
                record_llm(started, ok=True)
                return response
            except TimeoutError as exc:
                record_llm(started, ok=False, timed_out=True)
                last_error = exc
                logger.warning(
                    "LLM timeout attempt %d/%d", attempt, settings.ai_request_max_retries
                )
            except Exception as exc:  # pragma: no cover - network/runtime safety
                record_llm(started, ok=False)
                last_error = exc
                logger.warning(
                    "LLM request failed attempt %d/%d: %s",
                    attempt,
                    settings.ai_request_max_retries,
                    exc,
                )

            if attempt < settings.ai_request_max_retries:
                await asyncio.sleep(settings.ai_request_backoff_seconds * attempt)

        raise last_error or RuntimeError("LLM request failed with no retries configured")


class AWSLLMClient:
    """AWS GPU-backed LLM client with on-demand 70B management.

    - extract_features(): uses always-on g5.xlarge (8B model)
    - generate_reasoning(): auto-starts g5.12xlarge (70B), falls back to template if unavailable
    """

    def __init__(self):
        from unipaith.ai.gpu_manager import get_8b_manager, get_70b_manager

        self._8b_manager = get_8b_manager()
        self._70b_manager = get_70b_manager()

        # 8B client (always-on instance)
        self.feature_client = AsyncOpenAI(
            base_url=f"{settings.gpu_8b_endpoint}/v1",
            api_key="not-needed",
        )
        # 70B client (on-demand instance)
        self.reasoning_client = AsyncOpenAI(
            base_url=f"{settings.gpu_70b_endpoint}/v1",
            api_key="not-needed",
        )

    async def extract_features(self, system_prompt: str, user_content: str) -> str:
        """Call 8B model on always-on g5.xlarge."""
        response = await self._call_with_resilience(
            self.feature_client,
            model=settings.llm_feature_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.llm_feature_max_tokens,
            temperature=settings.llm_feature_temperature,
        )
        return response.choices[0].message.content or ""

    async def generate_reasoning(self, system_prompt: str, user_content: str) -> str:
        """Call 70B model on on-demand g5.12xlarge, with auto-start and fallback."""
        # Check budget before starting expensive instance
        if await self._is_budget_exceeded():
            logger.warning("70B budget exceeded, falling back to template reasoning")
            return self._template_reasoning(user_content)

        # Auto-start 70B if not running
        if not await self._70b_manager.is_running():
            logger.info("Starting 70B instance for reasoning generation")
            ready = await self._70b_manager.ensure_running()
            if not ready:
                logger.warning("70B instance failed to start, falling back to template")
                return self._template_reasoning(user_content)

        self._70b_manager.record_request()

        try:
            response = await self._call_with_resilience(
                self.reasoning_client,
                model=settings.llm_reasoning_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=settings.llm_reasoning_max_tokens,
                temperature=settings.llm_reasoning_temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("70B reasoning call failed: %s, falling back to template", e)
            return self._template_reasoning(user_content)

    async def _call_with_resilience(self, client: AsyncOpenAI, **kwargs):
        last_error: Exception | None = None
        for attempt in range(1, settings.ai_request_max_retries + 1):
            started = start_timer()
            try:
                response = await asyncio.wait_for(
                    client.chat.completions.create(**kwargs),
                    timeout=settings.ai_request_timeout_seconds,
                )
                record_llm(started, ok=True)
                return response
            except TimeoutError as exc:
                record_llm(started, ok=False, timed_out=True)
                last_error = exc
            except Exception as exc:
                record_llm(started, ok=False)
                last_error = exc
            if attempt < settings.ai_request_max_retries:
                await asyncio.sleep(settings.ai_request_backoff_seconds * attempt)
        raise last_error or RuntimeError("LLM request failed with no retries configured")

    async def _is_budget_exceeded(self) -> bool:
        """Check if monthly GPU budget is exceeded."""
        try:
            from unipaith.ai.cost_tracker import get_cost_tracker

            tracker = get_cost_tracker()
            return tracker.is_budget_exceeded()
        except Exception:
            return False  # Don't block on cost tracker errors

    @staticmethod
    def _template_reasoning(user_content: str) -> str:
        """Generate basic reasoning from a template when 70B is unavailable.

        Lower quality than the 70B model but costs $0.
        """
        return (
            "Based on the analysis of your profile and this program's requirements, "
            "this match was determined by evaluating your academic background, "
            "research experience, and stated preferences against the program's "
            "admission criteria, faculty research areas, and student outcomes. "
            "The match score reflects the overall alignment across these dimensions. "
            "For a more detailed personalized explanation, please try again later."
        )


class MockLLMClient:
    """Mock client for development/testing without GPU access."""

    async def extract_features(self, system_prompt: str, user_content: str) -> str:
        return """{
            "academic_strength": 0.82,
            "research_experience": 0.75,
            "leadership_signal": 0.60,
            "international_perspective": 0.90,
            "career_clarity": 0.70,
            "technical_depth": 0.78,
            "communication_quality": 0.65,
            "key_themes": ["data science", "machine learning", "healthcare applications"],
            "notable_strengths": ["strong quantitative background", "research publication"],
            "potential_gaps": ["limited industry experience"],
            "extracted_interests": ["NLP", "computer vision", "AI ethics"],
            "motivation_type": "mixed",
            "readiness_level": "strong"
        }"""

    async def generate_reasoning(self, system_prompt: str, user_content: str) -> str:
        return (
            "This program is a strong match based on your academic background in computer science "
            "and your research experience in NLP. The program's "
            "emphasis on applied machine learning "
            "aligns well with your goal of working at the intersection of AI and healthcare. "
            "Your GPA and test scores are competitive for this program. "
            "The program offers co-op opportunities that match your interest "
            "in gaining industry experience. Financial fit is moderate — tuition is within your "
            "stated budget, and partial scholarships are available "
            "for qualified international students."
        )


def get_llm_client() -> LLMClient | AWSLLMClient | MockLLMClient:
    """Factory: returns the appropriate LLM client based on gpu_mode.

    - "mock": synthetic responses (tests only)
    - "local" / "openai": uses configured base_url + api_key (OpenAI API or local vLLM)
    - "aws": AWS GPU instances with auto-start/stop
    """
    if settings.gpu_mode == "mock" or settings.ai_mock_mode:
        return MockLLMClient()
    if settings.gpu_mode == "aws":
        return AWSLLMClient()
    # "local", "openai", or any other value — uses config base_url + api_key
    return LLMClient()
