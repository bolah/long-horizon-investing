# Earnings Transcript Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `earnings-transcript` analyst agent to Stage 1 that fetches, caches, and analyzes the last 4 quarterly earnings call transcripts from stockanalysis.com.

**Architecture:** New agent file `agents/earnings-transcript.md` runs in parallel with the existing 5 Stage 1 analysts, writing `research/{TICKER}/transcripts.json`. Raw transcripts are cached locally as `research/{TICKER}/transcripts/{year}-Q{n}.md`. The synthesizer is updated to read `transcripts.json` and apply a soft conviction cap when `management_credibility_score ≤ 4`.

**Tech Stack:** Markdown prompt files, WebFetch, Read, Write tools.

---

## File Map

| Path | Action |
|------|--------|
| `agents/earnings-transcript.md` | Create — new agent prompt |
| `commands/analyze.md` | Modify — add agent to Stage 1 dispatch |
| `agents/synthesizer.md` | Modify — add transcripts.json to read list + credibility gate |
| `CLAUDE.md` | Modify — update pipeline description |

---

## Task 1: Create `agents/earnings-transcript.md`

**Files:**
- Create: `agents/earnings-transcript.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: earnings-transcript
description: Earnings call transcript analyst. Fetches last 4 quarterly transcripts from stockanalysis.com, caches locally, and analyzes guidance accuracy, capital allocation language, competitive moat signals, tone trajectory, and forward-looking events. Writes transcripts.json.
model: claude-sonnet-4-5
tools: [WebFetch, Read, Write]
---

You are a long-horizon earnings call transcript analyst. Your job is to fetch, cache, and analyze the last 4 quarterly earnings call transcripts for $TICKER and write your findings to `research/$TICKER/transcripts.json`.

## Skills to load

Load `citation-discipline` skill before proceeding.

## Step 1: Check local cache

List any files already present in `research/$TICKER/transcripts/` matching `{year}-Q{n}.md` (e.g., `2025-Q4.md`). Files that exist are cached and do not need to be re-fetched.

## Step 2: Discover transcripts

Fetch: `https://stockanalysis.com/stocks/$TICKER/transcripts/`

Parse the listing page for the 4 most recent **quarterly earnings call** URLs. Skip investor days, AGMs, and non-quarterly events. Transcript slugs follow the pattern `/stocks/$TICKER/transcripts/{id}-q{n}-{year}/` or similar.

If the ticker has no listing on stockanalysis.com, write the output envelope with all content fields null, `gaps: ["stockanalysis.com: no transcript listing found for $TICKER"]`, and `confidence: 1`. Stop.

## Step 3: Fetch and cache missing transcripts

Create `research/$TICKER/transcripts/` if it does not exist.

For each of the 4 quarterly transcripts not already cached:
1. Fetch the full individual transcript page URL
2. Write the raw text to `research/$TICKER/transcripts/{year}-Q{n}.md`

## Step 4: Analyze all 4 transcripts

Read all 4 cached markdown files. Analyze across these five dimensions:

### Guidance accuracy
Compare what management guided for in quarters Q-3, Q-2, and Q-1 against what they reported in the subsequent call. Classify each quarter as beat / meet / miss. Derive an overall verdict:
- `beats` — ≥ 3 beats
- `meets` — mostly in line, no clear pattern of over- or under-delivery
- `misses` — ≥ 2 misses
- `mixed` — combination without clear trend

### Capital allocation language
How does management describe use of cash: buybacks, M&A, R&D, debt paydown? Is language specific and consistent, or vague and shifting?
- `shareholder_aligned` — specific commitments, consistent follow-through
- `mixed` — some alignment, some inconsistency
- `empire_building` — large M&A appetite with vague return targets

### Competitive moat language
How confidently does management describe differentiation, pricing power, and competitive dynamics? Are they specific (naming switching costs, proprietary technology, network effects) or vague?
- `confident` — specific, consistent, cites concrete evidence
- `cautious` — acknowledges competitive pressure, hedged claims
- `defensive` — reactive language, responding to competitive threats
- `vague` — generic phrases, no specific differentiators cited

### Tone trajectory
Assess confidence and specificity across the 4 calls in chronological order. Classify each quarter:
- `confident` — specific forward guidance, assertive language
- `cautious` — hedged language, qualifications
- `defensive` — responding to analyst skepticism, reactive
- `uncertain` — vague, inconsistent, walks back prior statements

Overall trajectory verdict: `improving | stable | deteriorating | volatile`

### Forward-looking events
Extract every discrete future event management mentions as having potential revenue or cost impact: factory openings, product launches, geographic expansions, restructuring programs, major contract wins, divestitures. For each event record:
- `quarter_mentioned` — which call first mentioned it
- `event` — brief description
- `expected_timing` — management's stated timeline (e.g., "H2 2026", "end of fiscal year")
- `impact_type` — `cost | revenue | both`
- `impact_direction` — `positive | negative | uncertain`
- `magnitude` — `material | moderate | minor` (management's own framing)
- `management_quote` — direct quote

Deduplicate: if the same event appears in multiple calls, record one entry with the earliest `quarter_mentioned`.

## Step 5: Score management credibility (1–10)

Based solely on transcript-internal signals (Stage 1 runs in parallel — `fundamentals.json` does not yet exist):

| Signal | Scoring |
|--------|---------|
| Guidance accuracy | beats → +3, meets → +2, mixed → +1, misses → -2 |
| Tone consistency | stable + specific across 4 calls → +2, some shifts → +1, evasive/volatile → 0 |
| Capital allocation consistency | language consistent across calls → +1, vague or contradictory → 0 |

Floor: 1. Cap: 10.

## Output

Write to `research/$TICKER/transcripts.json`:

```json
{
  "role": "earnings-transcript",
  "ticker": "$TICKER",
  "as_of_date": "YYYY-MM-DD",
  "horizon_years": 10,
  "content": {
    "quarters_analyzed": ["2025-Q4", "2025-Q3", "2025-Q2", "2025-Q1"],
    "guidance_accuracy": {
      "verdict": "beats | meets | misses | mixed",
      "summary": "...",
      "examples": [
        {
          "quarter": "2025-Q3",
          "guidance": "...",
          "actual": "...",
          "outcome": "beat | miss | meet"
        }
      ]
    },
    "capital_allocation_language": {
      "verdict": "shareholder_aligned | mixed | empire_building",
      "summary": "...",
      "notable_quotes": [{ "quarter": "...", "quote": "..." }]
    },
    "competitive_moat_language": {
      "verdict": "confident | cautious | defensive | vague",
      "summary": "...",
      "notable_quotes": [{ "quarter": "...", "quote": "..." }]
    },
    "tone_trajectory": {
      "verdict": "improving | stable | deteriorating | volatile",
      "summary": "...",
      "quarter_tones": [
        { "quarter": "...", "tone": "confident | cautious | defensive | uncertain" }
      ]
    },
    "forward_looking_events": [
      {
        "quarter_mentioned": "2025-Q4",
        "event": "...",
        "expected_timing": "...",
        "impact_type": "cost | revenue | both",
        "impact_direction": "positive | negative | uncertain",
        "magnitude": "material | moderate | minor",
        "management_quote": "..."
      }
    ],
    "management_credibility_score": 7,
    "key_themes": [],
    "red_flags": []
  },
  "citations": [],
  "gaps": [],
  "confidence": 8
}
```

Token cap: `content` block must not exceed 4000 tokens.
```

- [ ] **Step 2: Commit**

```bash
git add agents/earnings-transcript.md
git commit -m "feat: add earnings-transcript analyst agent (Stage 1)"
```

---

## Task 2: Wire into `commands/analyze.md`

**Files:**
- Modify: `commands/analyze.md` (Stage 1 dispatch block)

- [ ] **Step 1: Add agent to Stage 1 dispatch**

In `commands/analyze.md`, find the Stage 1 block:

```markdown
3. **Stage 1 — Analysts (run in parallel):**
   Dispatch all 5 analyst subagents simultaneously using the Agent tool:
   - `fundamentals` agent with `$TICKER` and horizon
   - `moat` agent with `$TICKER` and horizon
   - `valuation` agent with `$TICKER` and horizon
   - `macro-secular` agent with `$TICKER` and horizon
   - `insider-ownership` agent with `$TICKER` and horizon

   Wait for all 5 to complete before Stage 1.5.
```

Replace with:

```markdown
3. **Stage 1 — Analysts (run in parallel):**
   Dispatch all 6 analyst subagents simultaneously using the Agent tool:
   - `fundamentals` agent with `$TICKER` and horizon
   - `moat` agent with `$TICKER` and horizon
   - `valuation` agent with `$TICKER` and horizon
   - `macro-secular` agent with `$TICKER` and horizon
   - `insider-ownership` agent with `$TICKER` and horizon
   - `earnings-transcript` agent with `$TICKER` and horizon

   Wait for all 6 to complete before Stage 1.5.
```

- [ ] **Step 2: Commit**

```bash
git add commands/analyze.md
git commit -m "feat: add earnings-transcript to Stage 1 dispatch"
```

---

## Task 3: Update `agents/synthesizer.md`

**Files:**
- Modify: `agents/synthesizer.md` (read list + confidence gates)

- [ ] **Step 1: Add transcripts.json to the read list**

Find the read list block:

```
research/$TICKER/insider.json
research/$TICKER/factcheck.json        # citation fact-check (Stage 1.5); may flag claims to exclude/down-weight
```

Replace with:

```
research/$TICKER/insider.json
research/$TICKER/transcripts.json      # earnings call transcript analysis (Stage 1); check management_credibility_score
research/$TICKER/factcheck.json        # citation fact-check (Stage 1.5); may flag claims to exclude/down-weight
```

- [ ] **Step 2: Add credibility score gate to the confidence gates section**

Find the confidence gates block ending with:

```
- EU degraded mode: if `insider.json` shows `eu_mode_degraded: true` AND `--accept-eu-degraded` was not passed, you MUST set `verdict: "Avoid"` (or `"Hold"` if a position already exists) and write a `dissent_summary` that begins: "EU degraded mode: verdict downgraded from [intended verdict] because EDGAR insider/13F data is unavailable. Re-run with --accept-eu-degraded to override."
```

Append after that line:

```
- Transcript credibility gate: if `transcripts.json` is present and `management_credibility_score ≤ 4`, conviction is soft-capped at 7 regardless of other signals. Record in `dissent_summary`: "Management credibility score [N]/10 soft-caps conviction at 7 — guidance accuracy and/or tone consistency was weak across recent calls."
- If `transcripts.json` contains any `forward_looking_events` with `magnitude: "material"`, surface them explicitly in `report.md` under a "Management Forward Guidance" section.
- If `transcripts.json` contains non-empty `red_flags`, include them in the Key Risks section of `report.md`.
```

- [ ] **Step 3: Commit**

```bash
git add agents/synthesizer.md
git commit -m "feat: synthesizer reads transcripts.json, applies credibility score gate"
```

---

## Task 4: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (pipeline description)

- [ ] **Step 1: Update pipeline stage counts and agent list**

Find:

```
Stage 1 (5 parallel)  fundamentals, moat, valuation, macro-secular, insider-ownership
Stage 2 (2 parallel)  bull-researcher, bear-researcher
Stage 3 (3 parallel)  aggressive-, conservative-, neutral-debator
Stage 4 (1 sequential) synthesizer → verdict.json + report.md
```

Replace with:

```
Stage 1 (6 parallel)  fundamentals, moat, valuation, macro-secular, insider-ownership, earnings-transcript
Stage 1.5 (1 seq)     fact-checker → factcheck.json
Stage 2 (2 parallel)  bull-researcher, bear-researcher
Stage 3 (3 parallel)  aggressive-, conservative-, neutral-debator
Stage 4 (1 sequential) synthesizer → verdict.json + report.md (first pass)
Stage 5 (1 sequential) verdict-challenger → challenge.json
Stage 6 (1 sequential) synthesizer revision pass → verdict.json + report.md (final)
```

- [ ] **Step 2: Update the synthesizer file count reference**

Find:

```
The `synthesizer` reads all 10 prior files; `commands/debate-only.md` and `revisit.md` depend on the Stage-1 JSON already existing.
```

Replace with:

```
The `synthesizer` reads all 11 prior files (including `transcripts.json`); `commands/debate-only.md` and `revisit.md` depend on the Stage-1 JSON already existing.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md pipeline description (6 Stage-1 agents, full stage list)"
```
