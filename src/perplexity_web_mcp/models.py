"""AI model definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Model:
    """AI model configuration."""

    identifier: str
    mode: str = "copilot"


class Models:
    """Available AI models (all use copilot mode with web search)."""

    AUTO = Model(identifier="auto", mode="concise")
    """Standard Free Search — Unlimited concise search mode for free accounts."""

    DEEP_RESEARCH = Model(identifier="pplx_alpha")
    """Deep Research - Create in-depth reports with more sources, charts, and advanced reasoning."""

    CREATE_FILES_AND_APPS = Model(identifier="pplx_beta")
    """Create files and apps (previously known as Labs) - Turn your ideas into docs, slides, dashboards, and more."""

    BEST = Model(identifier="pplx_pro")
    """Best - Automatically selects the best model based on the query."""

    SONAR = Model(identifier="experimental", mode="concise")
    """Sonar 2 — Perplexity's latest in-house model (backend id: experimental)."""

    GEMINI_31_PRO_THINKING = Model(identifier="gemini31pro_high")
    """Gemini 3.1 Pro Thinking - Google's most advanced model (thinking)."""

    GPT_56_TERRA = Model(identifier="gpt56_terra")
    """GPT-5.6 Terra - OpenAI's versatile model."""

    GPT_56_TERRA_THINKING = Model(identifier="gpt56_terra_thinking")
    """GPT-5.6 Terra Thinking - OpenAI's versatile model with thinking."""

    GPT_56_SOL = Model(identifier="gpt56_sol")
    """GPT-5.6 Sol - OpenAI's most powerful model (Max only)."""

    GPT_56_SOL_THINKING = Model(identifier="gpt56_sol_thinking")
    """GPT-5.6 Sol Thinking - OpenAI's most powerful model with thinking (Max only)."""

    GROK_45 = Model(identifier="grok45low")
    """Grok 4.5 - xAI's most advanced model."""

    GROK_45_THINKING = Model(identifier="grok45medium")
    """Grok 4.5 Thinking - xAI's most advanced model with thinking."""

    CLAUDE_50_SONNET = Model(identifier="claude50sonnet")
    """Claude Sonnet 5 - Anthropic's fast model."""

    CLAUDE_50_SONNET_THINKING = Model(identifier="claude50sonnetthinking")
    """Claude Sonnet 5 Thinking - Anthropic's newest reasoning model."""

    CLAUDE_48_OPUS = Model(identifier="claude48opus")
    """Claude Opus 4.8 - Anthropic's most advanced reasoning model."""

    CLAUDE_48_OPUS_THINKING = Model(identifier="claude48opusthinking")
    """Claude Opus 4.8 Thinking - Anthropic's most advanced reasoning model (thinking)."""

    NEMOTRON_3_ULTRA = Model(identifier="nv_nemotron_3_ultra")
    """Nemotron 3 Ultra - NVIDIA's Nemotron 3 Ultra 550B model (thinking)."""

    GLM_5_2 = Model(identifier="glm_5_2")
    """GLM-5.2 - Z.ai's advanced model (thinking)."""

    KIMI_K2_6 = Model(identifier="kimik26instant")
    """Kimi K2.6 - Moonshot AI's latest model."""

    KIMI_K2_6_THINKING = Model(identifier="kimik26thinking")
    """Kimi K2.6 Thinking - Moonshot AI's latest model (thinking)."""
