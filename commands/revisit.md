---
description: Re-evaluate kill-criteria for a previously analyzed ticker using current data.
argument-hint: "[TICKER] [--refresh-analysts]"
---

# /revisit [TICKER]

Check whether kill-criteria from a prior verdict have been triggered.

**Usage:**
- `/revisit COST` — check current data against kill-criteria in verdict.json
- `/revisit COST --refresh-analysts` — re-run all 5 analyst agents before checking

## Steps

1. Read `research/{TICKER}/verdict.json`. If not found, tell the user to run `/analyze {TICKER}` first.

2. If `--refresh-analysts` is passed: re-run Stage 1 (all 5 analyst agents) before proceeding.

3. For each kill-criterion in the `kill_criteria` array in `research/{TICKER}/verdict.json`:
   - Read the relevant analyst file (fundamentals, moat, valuation, macro, or insider)
   - Check whether the trigger condition is met based on current data
   - Label: TRIGGERED / WATCH / OK

4. Output a kill-criteria status table:

```
Kill-Criteria Review: {TICKER} — {DATE}

| # | Trigger | Status | Evidence |
|---|---|---|---|
| 1 | ROIC < WACC for 2 consecutive years | OK | ROIC FY24: 21.3%, FY23: 20.1% |
| 2 | Gross margin lead < 50bps vs sector | WATCH | Lead narrowed to 80bps (was 150bps) |
```

5. Append to `research/{TICKER}/history.md`. **Append-only — never truncate prior entries.** Record both the kill-criteria status AND a structured, parseable outcome line so the next `/analyze` run can calibrate against this call:

```markdown
## Revisit: YYYY-MM-DD
- Kill-criteria: [N] checked — [N_ok] OK, [N_watch] WATCH, [N_triggered] TRIGGERED
- Prior verdict under test: [verdict] (conviction [X]/10, dated [prior date])
- OUTCOME: [holding|impaired|invalidated] — [one line: what the current data shows vs. what the thesis predicted]
- Calibration note: [was the prior conviction justified by how the thesis has aged? over/under/well-calibrated]
```

The `OUTCOME` and `Calibration note` lines are what the synthesizer reads on the next `/analyze` run to populate `prior_verdict_calibration` and adjust conviction. Be specific and honest — this is the only feedback signal the system gets on its own track record.
