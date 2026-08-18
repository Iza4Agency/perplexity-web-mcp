"""Tests for the MCP server module.

Test categories:
1. Model-specific tool routing (upstream).
2. MCP auth TOTP challenge persistence (upstream).
3. Docket worker patch - the patch is installed, and the invariant that makes it
   safe. This fork carries that patch, so its tests live alongside upstream's
   rather than replacing them; the two files collided as an add/add on the
   0.14.9 merge purely because they share a name.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastmcp import FastMCP

from perplexity_web_mcp.mcp import server
from perplexity_web_mcp.models import Models


def test_current_model_tools_route_to_live_identifiers() -> None:
    cases = (
        (server.pplx_gpt56_terra, Models.GPT_56_TERRA),
        (server.pplx_gpt56_terra_thinking, Models.GPT_56_TERRA_THINKING),
        (server.pplx_gpt56_sol, Models.GPT_56_SOL),
        (server.pplx_gpt56_sol_thinking, Models.GPT_56_SOL_THINKING),
        (server.pplx_grok45, Models.GROK_45),
        (server.pplx_grok45_thinking, Models.GROK_45_THINKING),
    )

    with patch.object(server, "ask", return_value="ok") as mock_ask:
        for tool, model in cases:
            assert tool.fn("question", "none", "conversation") == "ok"
            mock_ask.assert_called_with("question", model, "none", "conversation")


def test_removed_gpt_tools_are_not_exposed() -> None:
    assert not hasattr(server, "pplx_gpt54")
    assert not hasattr(server, "pplx_gpt54_thinking")
    assert not hasattr(server, "pplx_gpt55")
    assert not hasattr(server, "pplx_gpt55_thinking")


def test_mcp_auth_preserves_totp_challenge_between_calls() -> None:
    """MCP clients can submit TOTP after the email OTP callback requests it."""
    session = MagicMock()
    server._set_auth_session({"session": session, "email": "user@example.com"})

    try:
        with (
            patch.object(server, "resolve_redirect_url", return_value="https://callback"),
            patch.object(server, "follow_auth_callback", return_value="challenge-123"),
            patch.object(server, "verify_totp") as verify,
            patch.object(server, "extract_session_token", return_value="session-token"),
            patch.object(server, "save_token", return_value=True),
            patch("perplexity_web_mcp.cli.auth.get_user_info", return_value=None),
        ):
            first = server.pplx_auth_complete.fn("user@example.com", "654321")
            second = server.pplx_auth_complete.fn("user@example.com", totp_code="123456")

        assert first.startswith("TOTP_REQUIRED")
        assert second.startswith("SUCCESS")
        verify.assert_called_once_with(session, "challenge-123", "123456")
    finally:
        server._clear_auth_session()


class TestDocketWorkerDisabled:
    """FastMCP 2.14's background-task worker must not run.

    It polls an in-process fakeredis on two 250 ms timers for the life of the
    process, measured at ~1.4% of a core per instance, and Claude Code starts one
    instance per session. See the comment above _docket_lifespan_disabled.
    """

    def test_patch_is_installed(self):
        assert FastMCP._docket_lifespan is server._docket_lifespan_disabled

    def test_every_tool_forbids_background_tasks(self):
        """The invariant the patch depends on.

        Disabling the worker is only safe while no tool can be dispatched to it.
        FastMCP assigns mode 'forbidden' to sync tools; an async tool registered
        with task=True would be silently dropped instead of executed, so this must
        fail loudly rather than the patch being quietly wrong.
        """
        offenders = {
            name: mode
            for name, tool in server.mcp._tool_manager._tools.items()
            if (mode := getattr(getattr(tool, "task_config", None), "mode", None))
            != "forbidden"
        }
        assert not offenders, (
            f"tools not marked 'forbidden': {offenders}. Either make them sync, or "
            f"remove the _docket_lifespan patch so the worker can serve them."
        )

    def test_lifespan_publishes_current_server(self):
        """The real lifespan sets _current_server; CurrentFastMCP() reads it."""
        import anyio

        from fastmcp.server.dependencies import _current_server

        async def exercise():
            async with server._docket_lifespan_disabled(server.mcp):
                ref = _current_server.get()
                assert ref is not None and ref() is server.mcp

        anyio.run(exercise)
        assert _current_server.get(None) is None
