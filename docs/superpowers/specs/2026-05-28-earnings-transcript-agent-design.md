# Earnings Transcript Analyst Agent — Design Spec

**Date:** 2026-05-28  
**Status:** Approved

---

## Overview

Add an `earnings-transcript` analyst agent to Stage 1 of the `/analyze` pipeline. It fetches the last 4 quarterly earnings call transcripts from stockanalysis.com, caches them locally as markdown files, analyzes four qualitative signal dimensions, and writes `transcripts.json` following the common envelope schema.

---

## Architecture & Data Flow

### Pipeline slot

Stage 1 — parallel with `fundamentals`, `moat`, `valuation`, `macro-secular`, `insider-ownership`. Stage 1 grows from 5 to 6 parallel agents.

### Tools

`WebFetch`, `Read`, `Write`. No MCP tools needed. Works for both US and EU tickers (stockanalysis.com covers global) — no `eu_mode_degraded` flag.

### Fetch flow

1. Check `research/{TICKER}/transcripts/` for already-cached `{year}-Q{n}.md` files.
2. Fetch `https://stockanalysis.com/stocks/{ticker}/transcripts/` to discover transcript URLs. Parse only quarterly earnings calls — skip investor days, AGMs, and other event types. Take the 4 most recent quarters.
3. For each uncached transcript, fetch the individual page and write raw text to `research/{TICKER}/transcripts/{year}-Q{n}.md`.
4. Analyze all 4 cached files across the four signal dimensions.
5. Write `research/{TICKER}/transcripts.json`.

**Cache semantics:** Files are immutable once published — no staleness check needed. If a file exists on disk, use it without re-fetching.

**Miss handling:** If stockanalysis.com has no listing for the ticker (very small cap or unlisted), write the envelope with all `content` fields null, a gap entry, and `confidence: 1`.

---

## Output Schema

File: `research/{TICKER}/transcripts.json`

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
        "event": "New manufacturing facility opening in Poland",
        "expected_timing": "H2 2026",
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

### `management_credibility_score` (1–10)

Composite of transcript-internal signals only (Stage 1 runs in parallel — `fundamentals.json` does not yet exist):
- Guidance accuracy (did stated targets match outcomes in subsequent calls?)
- Tone consistency (stable and specific vs. evasive or shifting)
- Capital allocation language alignment (stated priorities consistent across calls)

The synthesizer cross-checks this score against `fundamentals.json` after Stage 1 completes.

---

## Pipeline Wiring Changes

### `commands/analyze.md`

Stage 1 dispatch list: add `earnings-transcript` agent alongside the existing 5.

### `agents/synthesizer.md`

Add `research/$TICKER/transcripts.json` to the "Read all these files" list.

Synthesizer behavior:
- `management_credibility_score ≤ 4` → soft cap: conviction cannot exceed 7 even if all other signals are strong. Document the cap in `dissent_summary`.
- Surface any `red_flags` entries and material `forward_looking_events` (magnitude = "material") explicitly in `report.md`.

### Bull/bear researchers

No changes needed — they read all files in `research/{TICKER}/` by convention.

---

## Skills

The agent loads `citation-discipline` before proceeding (consistent with all other Stage 1 analysts).

---

## Files Created / Modified

| Path | Action |
|------|--------|
| `agents/earnings-transcript.md` | **New** — agent prompt |
| `commands/analyze.md` | **Edit** — add agent to Stage 1 dispatch |
| `agents/synthesizer.md` | **Edit** — add transcripts.json to read list + credibility score gate |
| `CLAUDE.md` | **Edit** — document new agent in pipeline description |
