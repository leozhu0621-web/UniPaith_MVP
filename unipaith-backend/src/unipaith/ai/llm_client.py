"""
Unified LLM client for all AI operations.
Uses OpenAI-compatible API (works with vLLM, OpenAI, Anthropic via proxy, etc.)
"""
from __future__ import annotations

from openai import AsyncOpenAI

from unipaith.config import settings


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
        response = await self.feature_client.chat.completions.create(
            model=settings.llm_feature_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.llm_feature_max_tokens,
            temperature=settings.llm_feature_temperature,
        )
        return response.choices[0].message.content

    async def generate_reasoning(self, system_prompt: str, user_content: str) -> str:
        """Call reasoning model for natural-language explanations."""
        response = await self.reasoning_client.chat.completions.create(
            model=settings.llm_reasoning_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.llm_reasoning_max_tokens,
            temperature=settings.llm_reasoning_temperature,
        )
        return response.choices[0].message.content


class MockLLMClient:
    """Mock client for development/testing without GPU access."""

    async def extract_features(self, system_prompt: str, user_content: str) -> str:
        return '''{
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
        }'''

    async def generate_reasoning(self, system_prompt: str, user_content: str) -> str:
        return (
            "This program is a strong match based on your academic background in computer science "
            "and your research experience in NLP. The program's emphasis on applied machine learning "
            "aligns well with your goal of working at the intersection of AI and healthcare. "
            "Your GPA and test scores are competitive for this program. "
            "The program offers co-op opportunities that match your interest "
            "in gaining industry experience. Financial fit is moderate — tuition is within your "
            "stated budget, and partial scholarships are available for qualified international students."
        )


def get_llm_client() -> LLMClient | MockLLMClient:
    """Factory: returns mock client if ai_mock_mode is enabled."""
    if settings.ai_mock_mode:
        return MockLLMClient()
    return LLMClient()
