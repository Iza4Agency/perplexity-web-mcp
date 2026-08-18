# Thread Library

Browse, search, and export your Perplexity conversation history — with no quota cost.

## What It Is

Every question you ask Perplexity is saved to your library. The thread library feature
exposes this history to the CLI and MCP server, enabling:

- **Browse past conversations** — list recent threads with titles, models, and previews
- **Search before querying** — check if a topic was already researched (saves quota)
- **Read full history** — load any past thread's complete Q&A, sources, and follow-ups
- **Resume past conversations** — continue any thread from where it left off
- **Export to JSON** — backup your entire library (no browser required)

**Cost: FREE.** All thread library operations are read-only REST calls that consume
zero Pro Search quota.

---

## CLI Usage

### List threads

```bash
pwm threads                          # most recent 20 threads
pwm threads --limit 50              # get 50 threads
pwm threads --search "quantum"      # filter by keyword (server-side)
pwm threads --offset 20             # page 2 (skip first 20)
pwm threads --json                  # JSON output (for piping / scripting)
```

### Export library to JSON

Exports each thread's full conversation history (all turns, sources, related queries)
to a timestamped JSON file. No browser, no Playwright — uses the REST API directly.

```bash
pwm export                              # → pplx-export-2026-06-29.json
pwm export --output ./backup.json      # custom path
pwm export --search "ai"               # only threads matching "ai"
pwm export --limit 50                  # cap at 50 threads
```

---

## MCP Tool Usage

### List threads

```
pplx_list_threads()                          # recent 20 threads
pplx_list_threads(limit=50)                  # get 50
pplx_list_threads(search_term="quantum")     # filter by keyword
pplx_list_threads(offset=20)                 # page 2
```

### Read a full thread

```
pplx_get_thread("f1f6562c-91be-47e9-9d1f-89ed902fdf8e")
```

Returns a Markdown-formatted document with every Q&A turn, cited sources, and related queries.

### Resume a past conversation

```
# Step 1: Search your history (no quota)
pplx_list_threads(search_term="quantum computing")
# → slug: "f1f6562c-91be-47e9-9d1f-89ed902fdf8e"

# Step 2: Load history for context (no quota)
pplx_get_thread("f1f6562c-91be-47e9-9d1f-89ed902fdf8e")

# Step 3: Continue the conversation (1 Pro query)
pplx_smart_query(
    "What are the latest advances in error correction?",
    conversation_id="f1f6562c-91be-47e9-9d1f-89ed902fdf8e"
)
```

---

## MCP Resources

```
perplexity://library                  # most recent 50 threads
perplexity://thread/<slug>            # full history for a specific thread
```

---

## Attribution

The REST endpoints powering this feature (`/rest/thread/list_ask_threads` and
`/rest/thread/{slug}`) were originally reverse-engineered by Kyle Brodeur in
[kylebrodeur/perplexity-exporter](https://github.com/kylebrodeur/perplexity-exporter).
