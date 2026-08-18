# Account Connector Sources

Perplexity Pro and Enterprise accounts may expose account-level connector sources such as Pitchbook, Crunchbase, CB Insights, Statista, Google Drive, or Box. These connectors are controlled by Perplexity and by the authenticated account. This package can route queries through connector source IDs when Perplexity reports them, but it does not provide connector access by itself.

## Who Can Use This

You need all of the following:

- A Perplexity account authenticated with `pwm login`.
- A Perplexity plan or workspace with connectors enabled.
- At least one connector source ID reported by Perplexity's rate-limit API.

Free accounts usually will not have private-data connectors. If no connector IDs appear, use the built-in sources: `web`, `academic`, `social`, `finance`, `all`, or `none`.

## List Connector IDs

CLI:

```bash
pwm connectors list
pwm connectors list --refresh
```

MCP:

```python
pplx_connectors(refresh=False)
```

Example output:

```text
Connector source IDs:
- pitchbook_mcp_cashmere: 3/5
- cbinsights_mcp_cashmere: 5/5
```

## Query a Connector

CLI:

```bash
pwm ask "Summarize recent funding for Stripe" -m sonar -s pitchbook_mcp_cashmere
pwm research "Private company market map for payroll APIs" -s cbinsights_mcp_cashmere
pwm council "Compare private fintech competitors" -s pitchbook_mcp_cashmere
```

MCP:

```python
pplx_smart_query(
    query="Summarize recent funding for Stripe",
    intent="standard",
    source_focus="pitchbook_mcp_cashmere",
)
```

## Important Behavior

- Do not guess connector IDs. Run `pwm connectors list` or `pplx_connectors()` first.
- Unknown source values fail intentionally. They do not fall back to web search.
- Connector availability, quota, and answer quality are controlled by Perplexity.
- Live verification requires an account with that connector enabled.
- Connector IDs may be account-specific and may change if Perplexity changes its web API.

## Troubleshooting

If `pwm connectors list` says no connector source IDs were reported, the authenticated account probably does not have connectors enabled or Perplexity did not expose them through the rate-limit API.

If a connector query fails even though the ID is listed, re-run `pwm connectors list --refresh` and check whether the connector quota is exhausted. If quota remains, the connector may require a different backend payload from Perplexity's web app; open an issue with the connector ID, the command used, and the error message.
