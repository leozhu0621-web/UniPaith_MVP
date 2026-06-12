"""Uni managed-agent settings — flag defaults off, ids empty until configured."""

from unipaith.config import settings


def test_uni_managed_agent_settings_exist():
    assert settings.ai_uni_managed_agent_v1 is False  # default off
    assert settings.uni_agent_id == ""
    assert settings.uni_environment_id == ""
