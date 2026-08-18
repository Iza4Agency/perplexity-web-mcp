# Perplexity Model Roster Strict-Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every public model surface match Perplexity's July 14, 2026 search-model UI by replacing GPT-5.4/GPT-5.5 with GPT-5.6 Terra, GPT-5.6 Sol, and Grok 4.5.

**Architecture:** Keep the existing explicit, centralized model metadata design. Add backend `Model` constants, register public keys in `MODEL_METADATA`, derive council/tier behavior from that table, and update the thin MCP/API adapters and maintained documentation without introducing runtime discovery or compatibility aliases.

**Tech Stack:** Python 3.11+, FastMCP, FastAPI, pytest, Ruff, uv.

## Global Constraints

- Remove GPT-5.4 and GPT-5.5 from selectable model definitions, CLI, MCP, API listings, and maintained documentation.
- Add `gpt56_terra` (Pro), `gpt56_sol` (Max), and `grok45` (Pro), all with thinking toggles.
- Rename current user-facing Claude Sonnet labels from 5.0 to 5 without changing its backend identifiers.
- Keep Auto, Sonar 2, Deep Research, Create Files and Apps, and current Claude compatibility aliases.
- Do not add a runtime catalog fetch or compatibility layer for removed GPT models.

---

### Task 1: Test and implement the centralized roster

**Files:**
- Modify: `tests/test_shared.py`
- Modify: `tests/test_council.py`
- Modify: `tests/test_cli_main.py`
- Modify: `tests/test_rate_limits.py`
- Modify: `src/perplexity_web_mcp/models.py`
- Modify: `src/perplexity_web_mcp/shared.py`

**Interfaces:**
- Produces: `Models.GPT_56_TERRA`, `Models.GPT_56_TERRA_THINKING`, `Models.GPT_56_SOL`, `Models.GPT_56_SOL_THINKING`, `Models.GROK_45`, and `Models.GROK_45_THINKING`.
- Produces public keys: `gpt56_terra`, `gpt56_sol`, and `grok45` through `MODEL_METADATA`, `MODEL_MAP`, and `ModelName`.

- [ ] **Step 1: Update roster tests first**

Change expected model keys to include `gpt56_terra`, `gpt56_sol`, and `grok45`, exclude `gpt54` and `gpt55`, assert `MAX_ONLY_MODEL_NAMES == {"gpt56_sol", "claude_opus"}`, and assert the default council is `("gpt56_terra", "claude_sonnet", "gemini_pro")`. Update existing council/CLI fixtures from `Models.GPT_54*` to `Models.GPT_56_TERRA*` and assert the display names `GPT-5.6 Terra` and `Claude Sonnet 5`.

- [ ] **Step 2: Verify the focused tests fail for missing new definitions**

Run:

```bash
uv run --group tests pytest tests/test_shared.py tests/test_council.py tests/test_cli_main.py tests/test_rate_limits.py -q
```

Expected: collection or assertion failures because the new `Models` constants and public keys do not exist yet.

- [ ] **Step 3: Implement the model constants and metadata**

Add the six exact backend identifiers from the live catalog, replace the two old GPT metadata rows with three new rows, change Claude Sonnet's display label to `Claude Sonnet 5`, update `ModelName`, and change the default council to `gpt56_terra,claude_sonnet,gemini_pro`. Remove the four old GPT constants.

- [ ] **Step 4: Verify the centralized roster tests pass**

Run the same focused pytest command. Expected: PASS.

### Task 2: Test and implement MCP/API public surfaces

**Files:**
- Modify: `tests/test_api_server_models.py`
- Create: `tests/test_mcp_server.py`
- Modify: `src/perplexity_web_mcp/mcp/server.py`
- Modify: `src/perplexity_web_mcp/api/server.py`

**Interfaces:**
- Produces MCP tools: `pplx_gpt56_terra`, `pplx_gpt56_terra_thinking`, `pplx_gpt56_sol`, `pplx_gpt56_sol_thinking`, `pplx_grok45`, and `pplx_grok45_thinking`.
- Produces API aliases and `/v1/models` entries for GPT-5.6 Terra, GPT-5.6 Sol, and Grok 4.5.

- [ ] **Step 1: Write API and MCP assertions first**

Assert conventional aliases route to each new base/thinking model, `/v1/models` advertises the three new models and excludes `gpt-5.4`/`gpt-5.5`, new MCP wrappers call `ask()` with the correct `Models` constant, and old GPT wrappers are absent.

- [ ] **Step 2: Verify the focused tests fail**

Run:

```bash
uv run --group tests pytest tests/test_api_server_models.py tests/test_mcp_server.py -q
```

Expected: failures for missing aliases, advertised entries, or tools.

- [ ] **Step 3: Replace old GPT adapters with the new adapters**

Remove GPT-5.4/GPT-5.5 MCP functions and API mappings. Add the six MCP functions, aliases such as `gpt-5.6-terra`, `gpt56_terra`, `gpt-5.6-sol`, `gpt56_sol`, `grok-4.5`, and `grok45`, plus three canonical advertised model entries. Update current MCP/API docstrings from Claude Sonnet 5.0 to Claude Sonnet 5.

- [ ] **Step 4: Verify focused API/MCP tests pass**

Run the focused pytest command. Expected: PASS.

### Task 3: Synchronize maintained documentation and live snapshot

**Files:**
- Modify: `src/perplexity_web_mcp/cli/ai_doc.py`
- Modify: `src/perplexity_web_mcp/cli/main.py`
- Modify: `src/perplexity_web_mcp/cli/hack.py`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Modify: `desktop-extension/manifest.json`
- Modify: `src/perplexity_web_mcp/data/SKILL.md`
- Modify: `src/perplexity_web_mcp/data/references/models.md`
- Modify: `src/perplexity_web_mcp/data/references/mcp-tools.md`
- Modify: `src/perplexity_web_mcp/data/references/api-endpoints.md`
- Modify: mirrored files under `skills/perplexity-web-mcp/`
- Modify: `CHANGELOG.md`
- Modify: `scripts/reference_model_config.json`

**Interfaces:**
- Maintains exact documentation mirrors between `src/perplexity_web_mcp/data/` and `skills/perplexity-web-mcp/`.

- [ ] **Step 1: Replace current roster guidance and examples**

Document the three new keys, tiers, thinking behavior, MCP tools, API aliases, and Terra-based council default. Remove maintained recommendations for GPT-5.4/GPT-5.5 and rename Claude Sonnet 5.0 to Claude Sonnet 5. Do not rewrite historical changelog entries; add a new top entry describing this update.

- [ ] **Step 2: Refresh the live reference snapshot**

Run `python scripts/detect_model_changes.py --save`, using the documented browser fallback if Cloudflare blocks the direct fetch.

- [ ] **Step 3: Verify synchronization and formatting**

Run:

```bash
diff -ru src/perplexity_web_mcp/data skills/perplexity-web-mcp
uv run ruff check src tests
uv run ruff format --check src tests
git diff --check
```

Expected: no mirror differences, lint failures, formatting changes, or whitespace errors.

- [ ] **Step 4: Run the complete test suite**

Run:

```bash
uv run --group tests pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Confirm discovery reports exact active-search parity**

Run `python scripts/detect_model_changes.py` using the browser fallback if needed. Expected: no missing active search models and no stale selectable model identifiers in the codebase.
