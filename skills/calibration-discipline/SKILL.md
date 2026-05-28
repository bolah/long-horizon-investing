---
name: calibration-discipline
description: Enforce calibrated, confidence-weighted conviction in long-horizon verdicts. Anchor conviction to base rates, state an explicit probability the thesis is wrong, and cap conviction by the quality of the underlying analyst data. Loaded by the synthesizer and the verdict-challenger.
---

# Calibration Discipline

A verdict is only as trustworthy as the calibration behind its conviction. LLM judges are systematically overconfident and biased toward agreeable, optimistic conclusions. This skill forces conviction to be earned, not asserted.

## 1. Conviction must carry an explicit probability

Every verdict states `conviction` (1–10) AND `p_thesis_wrong` (0.0–1.0): the probability that, at the stated horizon, the core thesis will have proven materially wrong. The two must be mutually consistent — if you claim conviction 9 but admit a 40% chance the thesis is wrong, one of them is mis-stated.

Rough consistency band (not a hard formula — sanity check, not arithmetic):

| Conviction | Implied `p_thesis_wrong` |
|---|---|
| 9–10 | ≤ 0.15 |
| 7–8  | 0.15–0.30 |
| 5–6  | 0.30–0.45 |
| 3–4  | 0.45–0.60 |
| 1–2  | > 0.60 |

If your conviction and `p_thesis_wrong` fall in different rows, reconcile them before writing the verdict.

## 2. Anchor to base rates, then adjust

Start from the outside view, not the narrative. Relevant base rates for a 10-year horizon:
- A wide-moat, high-ROIC compounder bought at a fair-to-rich price beats the index over 10y far less often than the bull narrative implies — most "obvious" quality names are already priced for it.
- Margin and ROIC mean-revert more often than they persist; assume reversion unless the moat evidence is specific and cited.
- Management capital-allocation skill is the exception, not the rule.

State the base rate you are anchoring to, then justify each notch of conviction you add or subtract from it. "High conviction because the business is great" is not calibration — the question is whether the *price and the data* justify conviction beyond the base rate.

## 3. Confidence-weighting: conviction is capped by data quality

Each analyst envelope carries a `confidence` (1–10) from [[citation-discipline]]. The verdict cannot be more confident than the evidence it rests on:

- Identify which analyst envelopes the thesis **materially depends on** (e.g. an Initiate built on valuation + moat depends on `valuation.json` and `moat.json`).
- **Cap rule:** `conviction` ≤ the minimum `confidence` among those load-bearing envelopes. A thesis resting on a `confidence: 4` valuation cannot earn conviction 8.
- Any argument resting on a field that is `null`, in `gaps[]`, or in an envelope with `confidence < 5` must be explicitly down-weighted and flagged — never treated as solid.
- If a [[citation-discipline]] fact-check (`factcheck.json`) flagged a claim, exclude it or down-weight it; do not let a flagged number support conviction.

Record the cap you applied and which envelopes set it.

## 4. Overconfidence correction

Before finalizing, run the pre-mortem in reverse: assume the verdict is wrong at the horizon and ask what you must have over-weighted to get here. If the honest answer is "the bull narrative" or "recent strong results," subtract conviction. The default failure mode is too high, not too low.

## 5. Self-check before writing

1. Are `conviction` and `p_thesis_wrong` in consistent bands? — yes/no
2. Did I state the base rate I anchored to and justify deviations? — yes/no
3. Is `conviction` ≤ the min confidence of the load-bearing envelopes (cap applied and recorded)? — yes/no
4. Did I down-weight every fact-check-flagged or gap/null-backed claim? — yes/no

If any answer is no, fix it before writing.
