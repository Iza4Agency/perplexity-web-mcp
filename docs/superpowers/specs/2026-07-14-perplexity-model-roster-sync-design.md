# Perplexity Model Roster Strict-Sync Design

## Goal

Synchronize Perplexity Web MCP's public search-model roster with the live Perplexity selector discovered on July 14, 2026. Remove GPT-5.4 and GPT-5.5 completely, add GPT-5.6 Terra, GPT-5.6 Sol, and Grok 4.5, and update Claude Sonnet's display name from 5.0 to 5.

## Scope

The strict-sync policy applies to user-selectable premium search models. Perplexity-native product modes such as Auto, Sonar 2, Deep Research, and Create Files and Apps remain available because they are separate supported capabilities rather than stale premium-model entries.

Existing compatibility aliases for current Claude models remain unchanged. GPT-5.4 and GPT-5.5 receive no compatibility aliases because the requested policy is to remove search models that no longer appear in Perplexity's UI.

## Model Roster

Add these public models:

| Public key | Display name | Base identifier | Thinking identifier | Minimum tier |
|---|---|---|---|---|
| `gpt56_terra` | GPT-5.6 Terra | `gpt56_terra` | `gpt56_terra_thinking` | Pro |
| `gpt56_sol` | GPT-5.6 Sol | `gpt56_sol` | `gpt56_sol_thinking` | Max |
| `grok45` | Grok 4.5 | `grok45low` | `grok45medium` | Pro |

Remove the `gpt54` and `gpt55` public keys and their four backend identifiers from the codebase's selectable model definitions.

Keep the existing backend identifiers for Claude Sonnet, but change all current user-facing labels from `Claude Sonnet 5.0` to `Claude Sonnet 5`.

## Public Interfaces

The CLI model selector, shared smart-routing metadata, council model list, MCP server, API-compatible server, generated AI help, bundled Agent Skill, extension metadata, and documentation must expose the same current roster.

The MCP server adds these six explicit tools:

- `pplx_gpt56_terra`
- `pplx_gpt56_terra_thinking`
- `pplx_gpt56_sol`
- `pplx_gpt56_sol_thinking`
- `pplx_grok45`
- `pplx_grok45_thinking`

The four `pplx_gpt54*` and `pplx_gpt55*` tools are removed.

The API-compatible server adds conventional aliases for the three new models, including their canonical public keys, and removes GPT-5.4/GPT-5.5 aliases and advertised model entries.

## Routing and Council Behavior

GPT-5.6 Terra replaces GPT-5.4 in the Pro-compatible default Model Council. The default roster becomes:

```text
gpt56_terra,claude_sonnet,gemini_pro
```

GPT-5.6 Sol and Claude Opus 4.8 remain excluded from the default council because they require Max. All three new models are eligible for explicitly requested councils.

Smart routing remains unchanged because its detailed intent already uses Claude Sonnet rather than GPT-5.4. Existing quota protection continues to derive Max-only restrictions from centralized model metadata.

## Documentation and Snapshot

Update all maintained documentation and mirrored skill content, including README, project agent instructions, CLI AI help, MCP/API/model references, desktop extension metadata, and changelog. Historical changelog entries remain unchanged.

After implementation, fetch the live Perplexity catalog again and replace `scripts/reference_model_config.json` using the repository's discovery script with `--save`.

## Testing

Use test-driven development for behavioral changes:

1. Change model-roster, tier, council-default, resolver, MCP, API-alias, and advertised-model tests first.
2. Run the focused tests and confirm they fail because the new model definitions or tools do not yet exist.
3. Implement the minimum synchronized production changes.
4. Run focused tests until green.
5. Run formatting and lint checks configured by the repository.
6. Run the complete test suite with `uv run --group tests pytest tests/ -v`.
7. Run the discovery script once more and confirm the codebase-status section reports no missing or stale active search models.

## Success Criteria

- Every premium search model displayed in the July 14, 2026 Perplexity selector is represented with the correct identifier, thinking behavior, and subscription tier.
- GPT-5.4 and GPT-5.5 cannot be selected through the CLI, MCP, or API-compatible model listing.
- No maintained user-facing documentation recommends GPT-5.4, GPT-5.5, or Claude Sonnet 5.0.
- Default council routing uses GPT-5.6 Terra and remains Pro-compatible.
- The reference model snapshot matches the live catalog.
- The full automated test suite passes.
