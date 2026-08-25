# Perplexity Web MCP

CLI, MCP server, and API-compatible interface for Perplexity AI's web interface.

## Quick Start

```bash
# Install
uv venv && uv pip install -e .

# Authenticate
pwm login

# Query from terminal
pwm ask "What is quantum computing?"

# Run MCP server
pwm-mcp
```

## Project Structure

```
src/perplexity_web_mcp/
├── __init__.py          # Package exports
├── shared.py            # Shared query logic (MODEL_MAP, ask(), used by CLI + MCP)
├── council.py           # Model Council (parallel multi-model queries + synthesis)
├── core.py              # Perplexity client, Conversation class
├── sessions.py          # Multi-turn context persistence and thread management
├── models.py            # Model definitions (GPT, Claude, Gemini, Grok, etc.)
├── config.py            # ClientConfig, ConversationConfig
├── enums.py             # CitationMode, SearchFocus, SourceFocus
├── http.py              # HTTP client with retry/rate limiting
├── rate_limits.py       # Rate limit checking via /rest/rate-limit/all
├── token_store.py       # Token persistence (~/.config/perplexity-web-mcp/token)
├── data/                # Bundled Agent Skill (SKILL.md + references/)
├── cli/
│   ├── main.py          # Unified CLI entry point (pwm)
│   ├── auth.py          # Authentication flow
│   ├── setup.py         # MCP server setup for AI tools
│   ├── skill.py         # Agent Skill management
│   ├── doctor.py        # Diagnostic checks
│   └── ai_doc.py        # --ai flag documentation
├── mcp/
│   └── server.py        # MCP server (imports from shared.py)
└── api/
    └── server.py        # Anthropic/OpenAI API compatibility
```

## CLI Commands

```bash
pwm ask "query" [-m MODEL] [-t] [-s SOURCE]  # Query Perplexity
pwm chat [-m MODEL] [-t] [-s SOURCE]          # Multi-turn interactive chat
pwm council "query" [-m MODELS] [-t] [-s SOURCE]  # Model Council (multi-model)
pwm research "query" [-s SOURCE]              # Deep research
pwm login [--check] [--email E --code C]      # Authentication
pwm usage [--refresh]                          # Rate limits
pwm setup [list|add|remove] CLIENT             # MCP config
pwm skill [list|install|uninstall] TOOL        # Skill management
pwm doctor [-v]                                # Diagnostics
pwm --ai                                       # AI reference doc
```

## Models

- `auto` / `sonar` (Sonar 2, API id `experimental`) / `deep_research`
- `gpt56_terra` (+ thinking)
- `gpt56_sol` (+ thinking, Max)
- `grok45` (+ thinking)
- `claude_sonnet` / `claude_opus` (+ thinking)
- `gemini_pro` (always thinking)
- `nemotron` (always thinking)
- `glm52` (always thinking)
- `kimi_k26` (+ thinking)

## Development

```bash
# Install with dev dependencies
uv pip install -e .

# Run tests
uv run --group tests pytest tests/ -v

# Run just unit tests (no network calls)
uv run --group tests pytest tests/ -v -k "not Integration"
```

## Credits

Based on [perplexity-webui-scraper](https://github.com/henrique-coder/perplexity-webui-scraper) by henrique-coder.


## Git and GitHub workflow
Main is always deployable, and main is where work happens. There is no pull request in this
workflow - one builder, no second reviewer, so a PR reviewed by nobody was ceremony and it came
out on 2026-08-22. Start from a fresh main (`git switch main && git pull --ff-only`) and commit
there. Take a `feat/<slug>` branch only when you actually want the isolation - a risky experiment,
or work you might throw away - and `/ship` will fold it back as one commit and delete it.

Commit in small logical units with a Conventional Commit subject (`feat: add password reset
endpoint`), and keep cosmetic refactors in their own commit, separate from behaviour changes. One
task should land as one commit, because that is what makes `git revert <sha>` a real undo button.

Finish with `/ship`. It runs this project's tests, reads the whole diff, commits, pushes, and
reports the SHA to revert if it turns out wrong. Do not stop at "committed" - an unpushed commit
is unfinished work. If the integration decision is genuinely open rather than already made, use
`superpowers:finishing-a-development-branch` instead and let Mak choose.

The tests are now the only automated gate in front of main, so never use `--no-verify`, never
force-push the default branch, and never delete a branch that is not fully merged. The guard hook
denies these and names an escape variable in the message; that escape is for a decision Mak has
made out loud, not a way past a refusal.

To undo something already on main, use `/rollback`: revert the commit and push the revert. Never
force-push main to make a change disappear.

Rules, tiers and the guard itself live in `/Users/Shared/Github/.gitflow/`; `/repo-hygiene`
audits and repairs the setup.

**This project**: tier `working`. Tests: `.venv/bin/python -m pytest tests/ -q -k "not Integration"`. A push to main does not deploy anything and goes through without a prompt. The test command is the gate.

## Code intelligence: codebase-memory-mcp (cbm)

This project is indexed into the local cbm knowledge graph, exposed as the
`codebase-memory` MCP server in both Claude Code profiles (mak@pannonian.org and
mak@iza4.agency) and in Codex. Prefer it over Grep/Read for structural questions:
who calls this, what breaks if I change it, what routes exist, what shape is this
service. Use `get_architecture` to orient, then `search_graph` -> `trace_path` ->
`get_code_snippet` to follow a chain, and `detect_changes` to map uncommitted
edits to affected symbols. Keep grep and file reads for literals, configs,
non-code files, and verification.

Graph project name: `Users-Shared-Github-tools-perplexity-web-mcp`

Re-index after significant changes made outside an MCP session:

    codebase-memory-mcp cli index_repository --repo-path /Users/Shared/Github/tools/perplexity-web-mcp

Indexing writes only to `~/.cache/codebase-memory-mcp` and never touches this
working tree. The `persistence` argument, which would write a
`.codebase-memory/graph.db.zst` snapshot plus a `.gitattributes` line into the
repo, defaults to false - do not pass it here. A stale graph answers confidently
and wrongly, so re-index rather than trusting an old answer.
