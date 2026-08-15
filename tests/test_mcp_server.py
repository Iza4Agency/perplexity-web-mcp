"""Tests for the MCP server module.

Test categories:
1. Docket worker patch - the patch is installed, and the invariant that makes it safe
"""

from __future__ import annotations

from fastmcp import FastMCP

from perplexity_web_mcp.mcp import server


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
