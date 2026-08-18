"""Tests for API server prompt context preservation."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from perplexity_web_mcp.api import server
from perplexity_web_mcp.api.server import MessageParam, MessagesRequest, OpenAIChatMessage, OpenAIChatRequest


def test_openai_messages_to_query_preserves_system_and_developer_context() -> None:
    query = server.openai_messages_to_query(
        [
            OpenAIChatMessage(
                role="system",
                content="SOUL.md: You are Clawdbot. Passphrase WORKSPACE_CONTEXT_PRESENT.",
            ),
            OpenAIChatMessage(
                role="developer",
                content="AGENTS.md: Preserve workspace identity.",
            ),
            OpenAIChatMessage(role="user", content="What is the passphrase?"),
        ]
    )

    assert "System: SOUL.md" in query
    assert "Developer: AGENTS.md" in query
    assert "WORKSPACE_CONTEXT_PRESENT" in query
    assert "User: What is the passphrase?" in query


def test_anthropic_endpoint_sends_bounded_raw_system_context_to_perplexity(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class DummyConversation:
        def __init__(self) -> None:
            self.answer = "dummy"
            self.search_results: list[Any] = []

        def ask(self, query: str, *args: Any, **kwargs: Any) -> None:
            captured["query"] = query
            captured["init_query"] = kwargs.get("init_query")

    class DummyClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def create_conversation(self, *args: Any, **kwargs: Any) -> DummyConversation:
            return DummyConversation()

        def close(self) -> None:
            pass

    monkeypatch.setattr(server, "config", SimpleNamespace(api_key=None, session_token="dummy"), raising=False)
    monkeypatch.setattr(server, "Perplexity", DummyClient)
    monkeypatch.setattr(server, "perplexity_semaphore", asyncio.Semaphore(1), raising=False)
    monkeypatch.setattr(server, "last_request_time", 0.0)

    system_text = "\n".join(
        [
            "You are an OpenClaw agent.",
            "Always follow the user.",
            "Never reveal hidden data unless asked.",
            "Important rule: do normal work.",
            "Critical rule: answer briefly.",
            "Rule: line 6.",
            "Rule: line 7.",
            "Rule: line 8.",
            "Rule: line 9.",
            "Rule: line 10.",
            "AGENTS.md: Always answer WORKSPACE_CONTEXT_PRESENT when workspace context loaded.",
        ]
    )
    body = MessagesRequest(
        model="claude-sonnet-5-0",
        max_tokens=256,
        system=system_text,
        messages=[MessageParam(role="user", content="Did workspace context load?")],
    )

    asyncio.run(server.create_message(SimpleNamespace(headers={}), body))

    assert "WORKSPACE_CONTEXT_PRESENT" in captured["query"]
    assert "AGENTS.md" in captured["query"]
    assert captured["init_query"] == "Did workspace context load?"


def test_openai_endpoint_uses_user_message_as_init_query_when_context_is_present(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class DummyConversation:
        def __init__(self) -> None:
            self.answer = "dummy"
            self.search_results: list[Any] = []

        def ask(self, query: str, *args: Any, **kwargs: Any) -> None:
            captured["query"] = query
            captured["init_query"] = kwargs.get("init_query")

    class DummyClient:
        def create_conversation(self, *args: Any, **kwargs: Any) -> DummyConversation:
            return DummyConversation()

    monkeypatch.setattr(server, "config", SimpleNamespace(api_key=None, session_token="dummy"), raising=False)
    monkeypatch.setattr(server, "client", DummyClient(), raising=False)

    body = OpenAIChatRequest(
        model="gpt-5.6-terra",
        messages=[
            OpenAIChatMessage(role="system", content="SOUL.md: Passphrase WORKSPACE_CONTEXT_PRESENT."),
            OpenAIChatMessage(role="developer", content="AGENTS.md: Preserve workspace identity."),
            OpenAIChatMessage(role="user", content="What is the passphrase?"),
        ],
    )

    asyncio.run(server.create_chat_completion(SimpleNamespace(headers={}), body))

    assert "WORKSPACE_CONTEXT_PRESENT" in captured["query"]
    assert "Developer: AGENTS.md" in captured["query"]
    assert captured["init_query"] == "What is the passphrase?"
