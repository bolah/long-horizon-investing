---
description: Run only the debate stages (bull/bear, risk debate, synthesis) from existing analyst files. Skips Stage 1 data collection.
argument-hint: "[TICKER]"
---

# /debate-only [TICKER]

Run the debate and synthesis stages from existing analyst files. Useful for re-running the verdict without re-fetching data (faster, lower cost).

**Requires:** All 5 analyst files already present in `research/{TICKER}/`.

## Steps

1. Verify all 5 analyst files exist in `research/{TICKER}/`: `fundamentals.json`, `moat.json`, `valuation.json`, `macro.json`, `insider.json`. If any are missing, tell the user to run `/analyze {TICKER}` first.

2. **Stage 1.5 (optional):** if `factcheck.json` is absent or stale, run the `fact-checker` agent to (re)verify the analyst citations before debating. Skip only if a recent `factcheck.json` already exists.

3. Run Stage 2 (bull + bear) in parallel.

4. Run Stage 3 (risk debate: aggressive, conservative, neutral) in parallel.

5. Run Stage 4 (first-pass `synthesizer`).

6. Run Stage 5 (`verdict-challenger` → `challenge.json`).

7. Run Stage 6 (`synthesizer` revision pass — addresses `challenge.json`, overwrites verdict).

8. Display the verdict.

**Note:** This re-uses cached analyst data. If analysts are stale (> 30 days), consider `/analyze {TICKER}` with fresh data.
