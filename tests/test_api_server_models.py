"""Tests for API-compatible server model aliases."""

from __future__ import annotations

from perplexity_web_mcp.api.server import AVAILABLE_MODELS, get_model
from perplexity_web_mcp.models import Models


def test_claude_sonnet_aliases_route_to_sonnet_5() -> None:
    assert get_model("claude-sonnet-5-0") is Models.CLAUDE_50_SONNET
    assert get_model("claude-sonnet-5-0", thinking=True) is Models.CLAUDE_50_SONNET_THINKING


def test_legacy_claude_sonnet_alias_routes_to_current_sonnet() -> None:
    assert get_model("claude-sonnet-4-6") is Models.CLAUDE_50_SONNET
    assert get_model("claude-3-5-sonnet", thinking=True) is Models.CLAUDE_50_SONNET_THINKING


def test_glm_aliases_route_to_glm_5_2() -> None:
    assert get_model("glm-5.2") is Models.GLM_5_2
    assert get_model("glm52", thinking=True) is Models.GLM_5_2


def test_available_models_include_current_sonnet_and_glm() -> None:
    ids = {model["id"] for model in AVAILABLE_MODELS}
    assert "claude-sonnet-5" in ids
    assert "glm-5.2" in ids


def test_new_openai_and_xai_aliases_route_to_current_models() -> None:
    assert get_model("gpt-5.6-terra") is Models.GPT_56_TERRA
    assert get_model("gpt56_terra", thinking=True) is Models.GPT_56_TERRA_THINKING
    assert get_model("gpt-5.6-sol") is Models.GPT_56_SOL
    assert get_model("gpt56_sol", thinking=True) is Models.GPT_56_SOL_THINKING
    assert get_model("grok-4.5") is Models.GROK_45
    assert get_model("grok45", thinking=True) is Models.GROK_45_THINKING


def test_available_models_match_current_gpt_and_grok_roster() -> None:
    ids = {model["id"] for model in AVAILABLE_MODELS}
    assert {"gpt-5.6-terra", "gpt-5.6-sol", "grok-4.5"} <= ids
    assert {"gpt-5.4", "gpt-5.5"}.isdisjoint(ids)
