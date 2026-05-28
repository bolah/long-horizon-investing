# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **Claude Code plugin** (not a Python app — there is no build, no test runner, no package). It is authored entirely as markdown prompt files plus JSON manifests. "Developing" here means editing agent/command/skill prompts and the manifests that wire them together.

**It is a research opinion tool.** Every agent prompt must preserve the invariant that the system never executes trades, connects to a broker, or manages a portfolio. Do not add tools or instructions that would.

The loose `*.py` files at the root (`analyze_nvda.py`, `temp_nvda_*.py`, etc.) are untracked one-off scratch scripts — not part of the plugin. `research/` is gitignored (live run output / audit trail stays local).

## Running it

This plugin is invoked, not built. Install + use:

```bash
claude plugin install path/to/long-horizon-investing/
export FRED_API_KEY=your_key            # free key, required for the fred MCP

/analyze COST                           # full 10y US run
/analyze COST --horizon 5               # 3 | 5 | 10
/analyze ASML --accept-eu-degraded      # EU ticker (no EDGAR; degraded)
/revisit COST                           # re-check kill-criteria vs current data
/debate-only COST                       # re-run debate from cached analyst JSON
```

The three MCP servers (`edgar-mcp`, `yfinance-mcp`, `fred-mcp`) are declared in `.mcp.json` and auto-installed via `uvx`.

## Architecture: a 6-stage subagent pipeline

`/analyze` (`commands/analyze.md`) is the orchestrator. It dispatches subagents via the Agent tool in staged fan-out/fan-in — **each stage must fully complete before the next starts**:

```
Stage 1   (6 parallel)  fundamentals, moat, valuation, macro-secular, insider-ownership, earnings-transcript
Stage 1.5 (1 seq)       fact-checker → factcheck.json
Stage 2   (2 parallel)  bull-researcher, bear-researcher
Stage 3   (3 parallel)  aggressive-, conservative-, neutral-debator
Stage 4   (1 sequential) synthesizer → verdict.json + report.md (first pass)
Stage 5   (1 sequential) verdict-challenger → challenge.json
Stage 6   (1 sequential) synthesizer revision pass → verdict.json + report.md (final)
```

Agents **do not call each other**. They communicate only through JSON files in `research/{TICKER}/`. Each Stage-N agent reads the files written by Stage-(N-1) and appends its own. This file-passing contract is the backbone — when adding or reordering an agent, update both `commands/analyze.md` (dispatch + wait points) and the downstream agent's "Read all these files" list. The `synthesizer` reads all 11 prior files (including `transcripts.json`); `commands/debate-only.md` and `revisit.md` depend on the Stage-1 JSON already existing.

The plugin manifest **`.claude-plugin/plugin.json` in the InvestAgents copy lists every command/agent/skill explicitly — but in THIS repo it is minimal** (name/version/author only); commands, agents, and skills are discovered by directory convention (`commands/`, `agents/`, `skills/`). Keep that in mind: adding a file here is enough to register it.

## Authoring conventions (read existing files before writing new ones)

- **Agents** (`agents/*.md`): YAML frontmatter with `name`, `description`, `model` (Sonnet for analysts/debaters, Opus for `synthesizer`), and a restrictive `tools:` list. Give each agent only the MCP/file tools it needs. The prompt body uses `$TICKER` as the substitution token and writes to `research/$TICKER/<role>.json`.
- **Common envelope schema**: every analyst writes `{ role, ticker, as_of_date, horizon_years, content: {...}, citations, gaps, confidence }`. Match the existing field shape — downstream agents and the synthesizer parse these by key.
- **Skills** (`skills/*/SKILL.md`): loaded by name from inside agent prompts ("Load `citation-discipline` and `...` skills"). `citation-discipline` is loaded by every envelope-writing agent; `kill-criteria-design` by the synthesizer. `long-horizon-dcf` and `long-horizon-comps` are adapted from Anthropic's financial-services (Apache-2.0) — preserve the `# Modified from ...` provenance header and the NOTICE entry if you edit them.
- **Numerical claims** follow citation-or-flag discipline: cite the source or list it in `gaps[]`. Don't invent figures.

## US-first / EU degraded mode (a hard, cross-cutting rule)

EDGAR (insider, 13F, Form 4, full filings) is **US-only**. For EU tickers, agents set `eu_mode_degraded: true`, fall back to yfinance, and **cap `confidence` at 5**. The gate is enforced in two places that must stay consistent:
- `commands/analyze.md`: halts after Stage 1 and prompts for `--accept-eu-degraded` unless the flag was passed.
- `agents/synthesizer.md`: if `insider.json` is `eu_mode_degraded` and the flag was not passed, the verdict **must** be downgraded to `Avoid` (or `Hold` if a position exists) with a `dissent_summary` explaining the downgrade.

## Synthesizer confidence gates (the verdict contract)

The `synthesizer` issues one of **Initiate / Add / Hold / Trim / Avoid** with a `conviction` 1–10. Hard rules in `agents/synthesizer.md`:
- `Initiate`/`Add` require `conviction ≥ 7`, ≥ 1 cited moat source, and insider data present (or `--accept-eu-degraded`).
- `management_credibility_score ≤ 4` in `transcripts.json` soft-caps conviction at 7.
- Valuation basis is **always vs. normalized 10-year earnings power, never TTM**.
- 3–6 kill-criteria, each testable + lagging (observable fact, not stock price) + scheduled.
- A `dissent_summary` recording what the bear/conservative argued that was overridden.

If you change the verdict vocabulary, gates, or `verdict.json` schema, propagate to `synthesizer.md`, `commands/revisit.md` (which re-tests kill-criteria), and `README.md`.
