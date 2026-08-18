# Connector Source Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users route Perplexity CLI and MCP queries through account connector source IDs such as `pitchbook_mcp_cashmere`, while preserving existing source aliases.

**Architecture:** Add one shared source resolver that maps friendly aliases to Perplexity source IDs and validates connector IDs before query execution. Store source IDs as strings in conversation config so built-in enum values and arbitrary connector IDs can use the same payload path. Surface connector IDs through usage/listing output and update CLI/MCP documentation.

**Tech Stack:** Python 3, Pydantic, Click, Rich, FastMCP, pytest, uv.

## Global Constraints

- Do not add dependencies.
- Do not change authentication behavior.
- Do not add "Co-Authored with Codex" or similar text to commits.
- Run tests with `uv run --group tests pytest ...`.
- If reinstalling the tool after code changes, run `uv cache clean && uv tool install --force .`.
- Preserve existing source aliases: `none`, `web`, `academic`, `social`, `finance`, `all`.
- Do not silently fall back to web for an unknown source value.
- Treat connector routing as an undocumented Perplexity web API behavior. Verify with a real connector-enabled account before claiming full support.

---

## File Structure

- Modify `src/perplexity_web_mcp/shared.py`
  - Own source alias definitions, connector ID validation, and the public resolver used by CLI, MCP, smart routing, and council.
- Modify `src/perplexity_web_mcp/config.py`
  - Allow `ConversationConfig.source_focus` to carry string source IDs in addition to existing `SourceFocus` enum values.
- Modify `src/perplexity_web_mcp/core.py`
  - Serialize source focus values as strings, preserving enum support.
- Modify `src/perplexity_web_mcp/council.py`
  - Use the shared resolver instead of duplicating the fallback behavior.
- Modify `src/perplexity_web_mcp/cli/main.py`
  - Allow connector IDs in `-s/--source`, add a `pwm connectors list` command, and make error messages show connector discovery guidance.
- Modify `src/perplexity_web_mcp/mcp/server.py`
  - Change MCP annotations from restrictive `Literal` source types to plain strings and add a `pplx_connectors` tool.
- Modify `src/perplexity_web_mcp/cli/ai_doc.py`
  - Update generated/static AI help text to mention connector source IDs.
- Modify `src/perplexity_web_mcp/data/SKILL.md`
  - Update installed skill guidance for agents.
- Modify `src/perplexity_web_mcp/data/references/mcp-tools.md`
  - Update MCP parameter reference.
- Modify tests:
  - `tests/test_shared.py`
  - `tests/test_core.py`
  - `tests/test_cli_main.py`
  - `tests/test_council.py`
  - Add focused MCP tests if existing test style supports direct tool function calls.

---

### Task 1: Add Shared Source Resolution

**Files:**
- Modify: `src/perplexity_web_mcp/shared.py`
- Test: `tests/test_shared.py`

**Interfaces:**
- Produces: `SourceFocusName = str`
- Produces: `SOURCE_FOCUS_ALIASES: dict[str, list[str]]`
- Produces: `SourceResolutionError(ValueError)`
- Produces: `resolve_source_focus(source_focus: str) -> tuple[list[str], SearchFocus]`
- Consumes: `get_limit_cache()`, `SourceFocus`, `SearchFocus`

- [ ] **Step 1: Write failing tests for built-in aliases and connector IDs**

Add tests to `tests/test_shared.py`:

```python
class TestResolveSourceFocus:
    def test_builtin_aliases_resolve_to_payload_source_ids(self) -> None:
        assert shared.resolve_source_focus("none") == ([], shared.SearchFocus.WRITING)
        assert shared.resolve_source_focus("web") == (["web"], shared.SearchFocus.WEB)
        assert shared.resolve_source_focus("academic") == (["scholar"], shared.SearchFocus.WEB)
        assert shared.resolve_source_focus("social") == (["social"], shared.SearchFocus.WEB)
        assert shared.resolve_source_focus("finance") == (["edgar"], shared.SearchFocus.WEB)
        assert shared.resolve_source_focus("all") == (["web", "scholar", "social"], shared.SearchFocus.WEB)

    def test_connector_id_from_rate_limits_is_accepted(self) -> None:
        cache = MagicMock()
        cache.get_rate_limits.return_value = RateLimits(
            source_limits=[
                shared.SourceLimit(source_id="pitchbook_mcp_cashmere", monthly_limit=5, remaining=3),
            ]
        )
        with patch("perplexity_web_mcp.shared.get_limit_cache", return_value=cache):
            sources, search_focus = shared.resolve_source_focus("pitchbook_mcp_cashmere")

        assert sources == ["pitchbook_mcp_cashmere"]
        assert search_focus is shared.SearchFocus.WEB

    def test_connector_like_id_is_accepted_when_limits_unavailable(self) -> None:
        with patch("perplexity_web_mcp.shared.get_limit_cache", return_value=None):
            sources, search_focus = shared.resolve_source_focus("crunchbase_mcp_cashmere")

        assert sources == ["crunchbase_mcp_cashmere"]
        assert search_focus is shared.SearchFocus.WEB

    def test_unknown_source_raises_instead_of_falling_back_to_web(self) -> None:
        with patch("perplexity_web_mcp.shared.get_limit_cache", return_value=None):
            with pytest.raises(shared.SourceResolutionError, match="Unknown source"):
                shared.resolve_source_focus("badvalue")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --group tests pytest tests/test_shared.py::TestResolveSourceFocus -v
```

Expected: fail because `resolve_source_focus`, `SourceResolutionError`, and `SOURCE_FOCUS_ALIASES` do not exist.

- [ ] **Step 3: Implement resolver in `shared.py`**

Replace the source section in `src/perplexity_web_mcp/shared.py` with this shape:

```python
import re

SOURCE_FOCUS_ALIASES: dict[str, list[str]] = {
    "none": [],
    "web": [SourceFocus.WEB.value],
    "academic": [SourceFocus.ACADEMIC.value],
    "social": [SourceFocus.SOCIAL.value],
    "finance": [SourceFocus.FINANCE.value],
    "all": [SourceFocus.WEB.value, SourceFocus.ACADEMIC.value, SourceFocus.SOCIAL.value],
}

SOURCE_FOCUS_MAP = SOURCE_FOCUS_ALIASES
SourceFocusName = str
SOURCE_FOCUS_NAMES: list[str] = list(SOURCE_FOCUS_ALIASES.keys())
_CONNECTOR_ID_RE = re.compile(r"^[a-z][a-z0-9_]*_mcp_[a-z0-9_]+$")
_BUILTIN_SOURCE_IDS = {
    SourceFocus.WEB.value,
    SourceFocus.ACADEMIC.value,
    SourceFocus.SOCIAL.value,
    SourceFocus.FINANCE.value,
    "google_drive",
    "box",
}


class SourceResolutionError(ValueError):
    """Raised when a source alias or connector source ID cannot be resolved."""


def _source_ids_from_limits() -> set[str]:
    cache = get_limit_cache()
    if cache is None:
        return set()
    limits = cache.get_rate_limits()
    if limits is None:
        return set()
    return {source.source_id for source in limits.source_limits}


def resolve_source_focus(source_focus: str) -> tuple[list[str], SearchFocus]:
    source = (source_focus or "web").strip()
    if source in SOURCE_FOCUS_ALIASES:
        search_focus = SearchFocus.WRITING if source == "none" else SearchFocus.WEB
        return SOURCE_FOCUS_ALIASES[source], search_focus

    known_source_ids = _source_ids_from_limits()
    if source in known_source_ids or source in _BUILTIN_SOURCE_IDS or _CONNECTOR_ID_RE.fullmatch(source):
        return [source], SearchFocus.WEB

    available = ", ".join(SOURCE_FOCUS_NAMES)
    raise SourceResolutionError(
        f"Unknown source '{source}'. Available aliases: {available}. "
        "Run `pwm connectors list` or `pwm usage` to find account connector source IDs."
    )
```

Keep `SOURCE_FOCUS_MAP` as a compatibility alias so existing imports keep working.

- [ ] **Step 4: Replace shared query fallback with resolver**

Change `_execute_with_retry` in `src/perplexity_web_mcp/shared.py`:

```python
def _execute_with_retry(
    query: str,
    model: Model,
    source_focus: SourceFocusName,
    conversation_id: str | None,
) -> tuple[str, list[SearchResultItem], str | None]:
    """Execute a query with automatic token retry on authentication failure."""
    from .exceptions import AuthenticationError, RateLimitError

    sources, search_mode = resolve_source_focus(source_focus)

    try:
        return _execute_query(query, model, sources, search_mode, conversation_id)
    except AuthenticationError:
        old_token = _client_token
        reset_client()
        new_token = load_token()
        if new_token and new_token != old_token:
            try:
                return _execute_query(query, model, sources, search_mode, conversation_id)
            except (AuthenticationError, RateLimitError) as retry_err:
                raise type(retry_err)(_format_error(retry_err)) from retry_err
        else:
            raise
```

- [ ] **Step 5: Run focused shared tests**

Run:

```bash
uv run --group tests pytest tests/test_shared.py -v
```

Expected: pass, except tests that still expect the old `SOURCE_FOCUS_MAP` value type may need the expected values changed from `SourceFocus` enum objects to payload strings.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add src/perplexity_web_mcp/shared.py tests/test_shared.py
git commit -m "feat: resolve connector source ids"
```

---

### Task 2: Allow String Source IDs in Query Payloads

**Files:**
- Modify: `src/perplexity_web_mcp/config.py`
- Modify: `src/perplexity_web_mcp/core.py`
- Test: `tests/test_core.py`

**Interfaces:**
- Consumes: `ConversationConfig.source_focus`
- Produces: payload `params["sources"]` as `list[str]`

- [ ] **Step 1: Write failing payload test for connector strings**

Add to `tests/test_core.py`:

```python
def test_source_focus_accepts_connector_string(self) -> None:
    config = ConversationConfig(source_focus=["pitchbook_mcp_cashmere"])
    conv = self._conv(config)
    payload = conv._build_payload("q", Models.BEST, [])

    assert payload["params"]["sources"] == ["pitchbook_mcp_cashmere"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run --group tests pytest tests/test_core.py::TestPayloadBuilding::test_source_focus_accepts_connector_string -v
```

Expected: fail because `core.py` assumes every source item has `.value`.

- [ ] **Step 3: Update config type**

Change `ConversationConfig.source_focus` in `src/perplexity_web_mcp/config.py`:

```python
source_focus: SourceFocus | str | list[SourceFocus | str] = SourceFocus.WEB
```

- [ ] **Step 4: Serialize enums and strings safely**

Add helper logic inside `Conversation._build_payload` in `src/perplexity_web_mcp/core.py`:

```python
        raw_source_focus = cfg.source_focus if isinstance(cfg.source_focus, list) else [cfg.source_focus]
        sources = [source.value if isinstance(source, SourceFocus) else source for source in raw_source_focus]
```

Import `SourceFocus` in `core.py` if it is not already imported at runtime:

```python
from .enums import CitationMode, SourceFocus
```

- [ ] **Step 5: Run focused core tests**

Run:

```bash
uv run --group tests pytest tests/test_core.py::TestPayloadBuilding -v
```

Expected: pass.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add src/perplexity_web_mcp/config.py src/perplexity_web_mcp/core.py tests/test_core.py
git commit -m "feat: pass connector source ids in query payload"
```

---

### Task 3: Update Council Routing to Use the Resolver

**Files:**
- Modify: `src/perplexity_web_mcp/council.py`
- Test: `tests/test_council.py`

**Interfaces:**
- Consumes: `resolve_source_focus(source_focus: str) -> tuple[list[str], SearchFocus]`
- Produces: council queries that pass connector IDs to each model.

- [ ] **Step 1: Write failing council test**

Add to `tests/test_council.py`:

```python
@patch("perplexity_web_mcp.council._query_single_model")
@patch("perplexity_web_mcp.shared.get_limit_cache", return_value=None)
def test_council_accepts_connector_source_id(mock_cache: MagicMock, mock_query: MagicMock) -> None:
    mock_query.return_value = CouncilMemberResult(
        name="Sonar 2",
        answer="answer",
        citations=[],
        error=None,
    )

    council_ask(
        query="company funding",
        models=[("Sonar 2", Models.SONAR)],
        source_focus="pitchbook_mcp_cashmere",
        synthesize=False,
    )

    assert mock_query.call_args.args[3] == ["pitchbook_mcp_cashmere"]
    assert mock_query.call_args.args[4] is SearchFocus.WEB
```

Use the exact local `CouncilMemberResult` constructor signature from `tests/test_council.py` if it differs.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run --group tests pytest tests/test_council.py::test_council_accepts_connector_source_id -v
```

Expected: fail because council still uses `SOURCE_FOCUS_MAP.get(..., [SourceFocus.WEB])`.

- [ ] **Step 3: Replace council fallback**

In `src/perplexity_web_mcp/council.py`, replace:

```python
from .shared import SOURCE_FOCUS_MAP
...
sources = SOURCE_FOCUS_MAP.get(source_focus, [SourceFocus.WEB])
search_mode = SearchFocus.WRITING if source_focus == "none" else SearchFocus.WEB
```

with:

```python
from .shared import resolve_source_focus
...
sources, search_mode = resolve_source_focus(source_focus)
```

- [ ] **Step 4: Run council tests**

Run:

```bash
uv run --group tests pytest tests/test_council.py -v
```

Expected: pass.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add src/perplexity_web_mcp/council.py tests/test_council.py
git commit -m "feat: route council through connector sources"
```

---

### Task 4: Add CLI Connector Discovery and Validation

**Files:**
- Modify: `src/perplexity_web_mcp/cli/main.py`
- Test: `tests/test_cli_main.py`

**Interfaces:**
- Consumes: `resolve_source_focus(source: str)`
- Produces: `pwm connectors list`

- [ ] **Step 1: Write failing CLI tests**

Add to `tests/test_cli_main.py`:

```python
@patch("perplexity_web_mcp.cli.main.ask", return_value="answer")
@patch("perplexity_web_mcp.shared.get_limit_cache", return_value=None)
def test_ask_accepts_connector_source(mock_cache: MagicMock, mock_ask: MagicMock, capsys: pytest.CaptureFixture) -> None:
    code = _cmd_ask(["company funding", "-m", "sonar", "-s", "pitchbook_mcp_cashmere"])

    assert code == 0
    assert "answer" in capsys.readouterr().out
    assert mock_ask.call_args.args[2] == "pitchbook_mcp_cashmere"


def test_bad_source_still_returns_clear_error(capsys: pytest.CaptureFixture) -> None:
    code = _cmd_ask(["query", "--source", "badvalue"])

    assert code == 1
    assert "Unknown source 'badvalue'" in capsys.readouterr().err
    assert "pwm connectors list" in capsys.readouterr().err
```

If `capsys.readouterr()` is already consumed in the second assertion, store it once:

```python
captured = capsys.readouterr()
assert "Unknown source 'badvalue'" in captured.err
assert "pwm connectors list" in captured.err
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --group tests pytest tests/test_cli_main.py::TestCmdAsk -v
```

Expected: connector test fails because `_cmd_ask_impl` still rejects values outside `SOURCE_FOCUS_NAMES`.

- [ ] **Step 3: Replace static CLI validation with resolver validation**

In `src/perplexity_web_mcp/cli/main.py`, import:

```python
from perplexity_web_mcp.shared import SourceResolutionError, resolve_source_focus
```

In `_cmd_ask_impl`, replace static source validation with:

```python
    try:
        resolve_source_focus(source)
    except SourceResolutionError as error:
        print(str(error), file=sys.stderr)
        return 1
```

Apply the same pattern to `_cmd_research_impl` and `_cmd_council_impl`.

- [ ] **Step 4: Add `pwm connectors list` command**

Add this command near the usage command group in `src/perplexity_web_mcp/cli/main.py`:

```python
@cli.group()
def connectors():
    """List account connector source IDs."""


@connectors.command(name="list")
@click.option("--refresh", is_flag=True, help="Refresh limits before listing connectors.")
def connectors_list(refresh):
    """List source IDs visible in the account rate-limit API."""
    code = _cmd_connectors_list(refresh=refresh)
    raise SystemExit(code)


def _cmd_connectors_list(refresh: bool = False) -> int:
    token = load_token()
    if not token:
        print("Not authenticated. Run `pwm login` first.", file=sys.stderr)
        return 1

    cache = RateLimitCache(token)
    limits = cache.get_rate_limits(force_refresh=refresh)
    if limits is None:
        print("Could not fetch connector source IDs.", file=sys.stderr)
        return 1

    connector_sources = [
        source for source in limits.source_limits
        if "_mcp_" in source.source_id or source.monthly_limit is not None
    ]

    table = Table(title="Connector Sources", show_header=True, header_style="bold cyan")
    table.add_column("Source ID", style="bold")
    table.add_column("Remaining", justify="right")
    table.add_column("Monthly Limit", justify="right")

    for source in connector_sources:
        remaining = "unlimited" if source.remaining is None else str(source.remaining)
        monthly_limit = "unlimited" if source.monthly_limit is None else str(source.monthly_limit)
        table.add_row(source.source_id, remaining, monthly_limit)

    if not connector_sources:
        console.print("[yellow]No connector source IDs were reported by this account.[/]")
        return 0

    console.print(table)
    return 0
```

Use existing imports and naming in `cli/main.py`; add `RateLimitCache` and `load_token` imports only if they are not already present.

- [ ] **Step 5: Add connector rows to `pwm usage` source section**

If `pwm usage` does not currently display `limits.source_limits`, add a table after the main rate limit table:

```python
        source_rows = [source for source in limits.source_limits if source.monthly_limit is not None]
        if source_rows:
            source_table = Table(title="Source Limits", show_header=True, header_style="bold cyan")
            source_table.add_column("Source ID", style="bold")
            source_table.add_column("Remaining", justify="right")
            source_table.add_column("Monthly Limit", justify="right")
            for source in source_rows:
                source_table.add_row(
                    source.source_id,
                    "unlimited" if source.remaining is None else str(source.remaining),
                    "unlimited" if source.monthly_limit is None else str(source.monthly_limit),
                )
            console.print(source_table)
```

- [ ] **Step 6: Run CLI tests**

Run:

```bash
uv run --group tests pytest tests/test_cli_main.py -v
```

Expected: pass.

- [ ] **Step 7: Commit Task 4**

Run:

```bash
git add src/perplexity_web_mcp/cli/main.py tests/test_cli_main.py
git commit -m "feat: list and validate connector sources"
```

---

### Task 5: Update MCP Tools for Arbitrary Connector IDs

**Files:**
- Modify: `src/perplexity_web_mcp/mcp/server.py`
- Test: existing MCP/server tests if present, otherwise direct function tests in `tests/test_rate_limits.py` or a new `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `SourceFocusName = str`
- Produces: `pplx_connectors(refresh: bool = False) -> str`

- [ ] **Step 1: Write failing MCP connector listing test**

Create `tests/test_mcp_server.py` if no MCP test file exists:

```python
from __future__ import annotations

from unittest.mock import MagicMock, patch

from perplexity_web_mcp.mcp import server
from perplexity_web_mcp.rate_limits import RateLimits, SourceLimit


@patch("perplexity_web_mcp.mcp.server.get_limit_cache")
def test_pplx_connectors_lists_source_ids(mock_get_limit_cache: MagicMock) -> None:
    cache = MagicMock()
    cache.get_rate_limits.return_value = RateLimits(
        source_limits=[
            SourceLimit(source_id="web", monthly_limit=None, remaining=None),
            SourceLimit(source_id="pitchbook_mcp_cashmere", monthly_limit=5, remaining=3),
        ]
    )
    mock_get_limit_cache.return_value = cache

    result = server.pplx_connectors.fn(refresh=False)

    assert "pitchbook_mcp_cashmere" in result
    assert "3/5" in result
```

If FastMCP exposes direct functions differently in this version, follow the existing pattern used for `pplx_usage` tests in `tests/test_rate_limits.py`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run --group tests pytest tests/test_mcp_server.py -v
```

Expected: fail because `pplx_connectors` does not exist.

- [ ] **Step 3: Update MCP descriptions and add connector tool**

In `src/perplexity_web_mcp/mcp/server.py`, update the server instructions:

```python
"All query tools support source_focus: none, web, academic, social, finance, all, "
"or an account connector source ID from pplx_connectors().\n"
```

Add:

```python
@mcp.tool
def pplx_connectors(refresh: bool = False) -> str:
    """List account connector source IDs that can be passed as source_focus.

    Returns source IDs from the Perplexity rate-limit API. Use these IDs as
    source_focus values, for example source_focus="pitchbook_mcp_cashmere".
    """
    cache = get_limit_cache()
    if cache is None:
        return "NOT AUTHENTICATED\n\nNo session token found. Authenticate first with pplx_auth_request_code."

    limits = cache.get_rate_limits(force_refresh=refresh)
    if limits is None:
        return "Could not fetch source limits."

    connector_sources = [
        source for source in limits.source_limits
        if "_mcp_" in source.source_id or source.monthly_limit is not None
    ]
    if not connector_sources:
        return "No connector source IDs were reported by this account."

    lines = ["Connector source IDs:"]
    for source in connector_sources:
        if source.monthly_limit is None:
            quota = "unlimited"
        else:
            quota = f"{source.remaining}/{source.monthly_limit}"
        lines.append(f"- {source.source_id}: {quota}")
    return "\n".join(lines)
```

- [ ] **Step 4: Verify MCP source annotations are no longer restrictive**

Confirm every MCP query function has:

```python
source_focus: SourceFocusName = "web"
```

and that `SourceFocusName` resolves to `str` from `shared.py`, not a `Literal[...]`.

- [ ] **Step 5: Run MCP tests**

Run:

```bash
uv run --group tests pytest tests/test_mcp_server.py tests/test_rate_limits.py -v
```

Expected: pass.

- [ ] **Step 6: Commit Task 5**

Run:

```bash
git add src/perplexity_web_mcp/mcp/server.py tests/test_mcp_server.py
git commit -m "feat: expose connector source ids to mcp clients"
```

---

### Task 6: Update Docs, Skill Reference, and AI Help

**Files:**
- Modify: `README.md`
- Create: `docs/connectors.md`
- Modify: `src/perplexity_web_mcp/cli/ai_doc.py`
- Modify: `src/perplexity_web_mcp/data/SKILL.md`
- Modify: `src/perplexity_web_mcp/data/references/mcp-tools.md`

**Interfaces:**
- Consumes: `pwm connectors list`
- Consumes: `pplx_connectors(refresh=False)`
- Produces: user-facing documentation for connector source IDs.

- [ ] **Step 0: Create dedicated connector guide**

Create `docs/connectors.md` explaining that connector access depends on the authenticated Perplexity account, free accounts may show no connector IDs, users must discover IDs with `pwm connectors list` or `pplx_connectors()`, and unknown source values fail instead of falling back to web.

- [ ] **Step 1: Update README source section**

In the source focus section, add:

```markdown
### Account connector sources

Perplexity accounts with enabled connectors may expose additional source IDs
through the rate-limit API, such as `pitchbook_mcp_cashmere` or
`cbinsights_mcp_cashmere`.

List available connector IDs:

```bash
pwm connectors list
```

Route a query through one connector:

```bash
pwm ask "Summarize recent funding for Acme Corp" -s pitchbook_mcp_cashmere
```

For MCP clients, call `pplx_connectors()` first, then pass the returned source
ID as `source_focus` to any `pplx_*` query tool.
```

- [ ] **Step 2: Update CLI AI doc**

In `src/perplexity_web_mcp/cli/ai_doc.py`, change source-focused examples to include:

```text
  pwm connectors list                              # List account connector source IDs
  pwm ask "private company funding" -s pitchbook_mcp_cashmere
```

Also update MCP text:

```text
  pplx_connectors(refresh=False)                   List connector source IDs
  source_focus may be a built-in alias or connector source ID.
```

- [ ] **Step 3: Update bundled skill**

In `src/perplexity_web_mcp/data/SKILL.md`, add connector guidance:

```markdown
Connector source IDs:
- CLI: run `pwm connectors list`, then pass the source ID with `-s`.
- MCP: call `pplx_connectors()`, then pass the source ID as `source_focus`.
- Do not guess connector IDs. If no connector is listed, use normal source focus values.
```

- [ ] **Step 4: Update MCP tool reference**

In `src/perplexity_web_mcp/data/references/mcp-tools.md`, add:

```markdown
### pplx_connectors

```python
pplx_connectors(refresh: bool = False) -> str
```

Lists account connector source IDs that can be passed to `source_focus`.
```

Update each `source_focus` comment from:

```python
# none, web, academic, social, finance, all
```

to:

```python
# none, web, academic, social, finance, all, or connector source ID from pplx_connectors()
```

- [ ] **Step 5: Run docs grep checks**

Run:

```bash
rg -n "connector|connectors|pitchbook_mcp_cashmere|pplx_connectors" README.md docs/connectors.md src/perplexity_web_mcp/cli/ai_doc.py src/perplexity_web_mcp/data
```

Expected: output shows connector guidance in all four doc locations.

- [ ] **Step 6: Commit Task 6**

Run:

```bash
git add README.md docs/connectors.md src/perplexity_web_mcp/cli/ai_doc.py src/perplexity_web_mcp/data/SKILL.md src/perplexity_web_mcp/data/references/mcp-tools.md
git commit -m "docs: document connector source routing"
```

---

### Task 7: Manual API Verification Against a Connector Account

**Files:**
- No code files required.
- Optional: Add a short note to `docs/superpowers/plans/2026-07-02-connector-source-routing.md` after execution with the verification result.

**Interfaces:**
- Consumes: installed local CLI
- Produces: confidence that Perplexity accepts connector IDs in `params.sources`

- [ ] **Step 1: Reinstall local tool without stale uv cache**

Run:

```bash
uv cache clean && uv tool install --force .
```

Expected: reinstall succeeds.

- [ ] **Step 2: Confirm authentication**

Run:

```bash
pwm login --check
```

Expected: authenticated account details are shown.

- [ ] **Step 3: List connector source IDs**

Run:

```bash
pwm connectors list --refresh
```

Expected: output includes connector IDs such as `pitchbook_mcp_cashmere`, `cbinsights_mcp_cashmere`, or another account-specific connector.

- [ ] **Step 4: Run a low-risk connector query**

Use a connector source ID from Step 3:

```bash
pwm ask "In one sentence, what kind of company is Stripe?" -m sonar -s pitchbook_mcp_cashmere --no-citations
```

Expected: query succeeds and does not error with an invalid source message.

- [ ] **Step 5: Confirm source quota changes if the connector has a monthly limit**

Run:

```bash
pwm connectors list --refresh
```

Expected: for limited connector sources, the remaining count may decrease by one. If it does not decrease but the query succeeds, record that Perplexity did not report connector quota consumption for this query.

- [ ] **Step 6: Verify typo protection**

Run:

```bash
pwm ask "test" -m sonar -s pitchbook_typo --no-citations
```

Expected: command exits non-zero with `Unknown source 'pitchbook_typo'` and does not run a web query.

- [ ] **Step 7: Commit verification note only if a note was added**

Run only if the plan or docs were updated with verification results:

```bash
git add docs/superpowers/plans/2026-07-02-connector-source-routing.md
git commit -m "docs: record connector routing verification"
```

---

### Task 8: Full Regression Suite and Final Review

**Files:**
- No new files.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: merge-ready branch.

- [ ] **Step 1: Run full unit test suite**

Run:

```bash
uv run --group tests pytest tests/ -v
```

Expected: pass.

- [ ] **Step 2: Run import smoke checks**

Run:

```bash
uv run python - <<'PY'
from perplexity_web_mcp.shared import resolve_source_focus
print(resolve_source_focus("web"))
print(resolve_source_focus("pitchbook_mcp_cashmere"))
PY
```

Expected: prints `(['web'], <SearchFocus.WEB: 'internet'>)` and `(['pitchbook_mcp_cashmere'], <SearchFocus.WEB: 'internet'>)`.

- [ ] **Step 3: Inspect changed files**

Run:

```bash
git diff --stat
git diff -- src/perplexity_web_mcp/shared.py src/perplexity_web_mcp/core.py src/perplexity_web_mcp/cli/main.py src/perplexity_web_mcp/mcp/server.py
```

Expected: changes are scoped to source resolution, connector listing, docs, and tests.

- [ ] **Step 4: Check for stale source docs**

Run:

```bash
rg -n "none, web, academic, social, finance, all" README.md src/perplexity_web_mcp
```

Expected: every remaining occurrence either also mentions connector source IDs or is intentionally describing only built-in aliases.

- [ ] **Step 5: Final commit if uncommitted changes remain**

Run:

```bash
git status --short
```

If files remain unstaged from final fixes:

```bash
git add <changed-files>
git commit -m "test: verify connector source routing"
```

---

## Rollback Plan

If manual verification proves `params.sources = ["pitchbook_mcp_cashmere"]` does not work, do not ship the query routing behavior. Keep or separately ship only harmless discovery improvements:

- `pwm connectors list`
- `pplx_connectors`
- `pwm usage` source-limit display

Then open a follow-up investigation task to capture the Perplexity web app request for connector-backed queries and compare payload fields against this client.

## Self-Review

- Spec coverage: Issue #13 asks for connector query routing plus connector listing. Tasks 1-5 implement routing and listing; Task 6 documents it; Task 7 validates the undocumented API behavior.
- Placeholder scan: No placeholder markers or unspecified implementation steps remain. The only conditional language is around existing test helper signatures and documented manual verification outcomes.
- Type consistency: `SourceFocusName` becomes `str`; `resolve_source_focus()` returns `tuple[list[str], SearchFocus]`; `ConversationConfig.source_focus` accepts `SourceFocus | str | list[SourceFocus | str]`; payload serialization always emits `list[str]`.
