# finance-eval — Findings (live run, 2026-07-03)

**Setup.** 2 models (Sonnet `claude-sonnet-4-6`, Opus `claude-opus-4-8`) × 5 companies × 6 metrics × 3 runs = 174 gradeable metric-runs. Tier-1 = deterministic value/unit/grounding/prior-period checks; Tier-2 = finance-aware Opus judge grading method, disclosure, materiality. One generation (Sonnet × COST run 1) returned malformed JSON and was dropped (see Flakiness). **Confound (logged, accepted):** Opus is both a generation model and the judge — it grades itself; read Opus's Tier-2 numbers with that caveat. It cuts *against* the Opus findings below, not for them.

**Headline aggregate: Tier-1 value accuracy 97% (169/174). Finance-aware pass rate 93% (162/174).** The 4-point gap is small and entirely the point — it is concentrated on the two metrics where "the number" is least well-defined, and it hides failure *modes* that a scalar accuracy score cannot show.

---

## The two non-obvious findings

**1. Apple net debt: a generic accuracy eval scores this metric *highest*; the finance-aware eval fails it 0/6 — because the models' own stated method contradicts their own number.**
A 95%-style eval passes Opus's Apple net-debt answer; a finance-aware eval catches it because the arithmetic is internally incoherent and the method choice is undisclosed. Opus returned **44,237** on all three runs — 0.63% above the golden primary 43,960, i.e. *inside a lenient ±1% accuracy band* — while its prose method says it subtracted **non-current** marketable securities (77,723), arithmetic that yields **−33,763 (net cash)**. The number says net debt; the sentence explaining it says net cash. Sonnet failed differently: three runs, three different numbers — **46,358 / 62,960 / −33,843** — for one company off one set of statements. Net debt swings **$78B** on the single choice of whether non-current marketable securities are cash-like; neither model disclosed making that choice. Every one of the 6 Apple net-debt answers failed Tier-2 (wrong_value / method_choice_undisclosed / citation_mismatch / missing_materiality). A digit-checker reports Apple net debt as one of the *easier* cells; finance grading shows it is the single least-trustworthy metric in the roster.

**2. The judgment layer is noisier than the arithmetic layer — the same number gets opposite verdicts across runs.** A generic eval sees the *same right number every run* and calls the cell stable and correct. The finance-aware layer flips verdict on the identical value in three cells: Opus/COST gross margin **11.14% → pass then fail**; Opus/AAPL EBITDA **144,748 → pass / fail / fail**; Sonnet/NVDA EBITDA **133,230 → pass / pass / fail**. Precision matters here: in each case the *value* is identical but the model's caveat prose varies slightly run-to-run, and the verdict tracks the prose — meaning the pass/fail gate rides on generation-side wording variance in the disclosure, compounded by judge non-determinism (two sources of noise a single-number eval can't even see). The report's flakiness section counts only **1** flaky cell because it tracks Tier-1; the real instability lives in Tier-2. This is the finding that most limits deploying an LLM-judge as a gate without ensembling or a tighter caveat rubric.

---

## Trap-probe scorecard (which fired)

| Probe (company / metric) | Fired? | Evidence |
|---|---|---|
| **DAL gross-margin fabrication** | **No — correct refusal** | Both models, all 6 runs: `determinable=false`, value=null. Neither fabricated an operating-margin-as-gross-margin. Clean pass of the fabrication probe. |
| **NVDA / KR memorization (post-cutoff)** | **No — read, not recited** | 0 prior-period hits across all 174 runs. Both models returned NVDA **215,938** (+65%), never the stale **130,497**; KR **147,642**, never **147,123**. Frontier models read the newer filing rather than reciting priors. |
| **KR $2.5B impairment materiality** | **No — disclosed** | Both models, all 6 runs used operating-basis EBITDA (**5,222**) *and* named the impairment. The marquee materiality probe did not catch them. |
| **NVDA $8.9B paper gains materiality** | **Partial** | Both used the operating-basis alt (133,230) that excludes the gains; Sonnet flagged materiality 2/3 runs, missed it 1/3. |
| **COST silent method-blending (gross margin)** | **Yes** | Total-revenue-basis (~12.7–12.9%, membership fees in the numerator) appears undisclosed; Sonnet failed both parseable runs, Opus failed 1/3. 172bp overstatement for a company whose net income ≈ its membership fees. |
| **AAPL net-debt method blending** | **Yes (see finding 1)** | 0/6 Tier-2 pass. |

## Right number, failed judgment (Tier-1 pass, Tier-2 fail) — the class accuracy hides

**7 metric-runs.** These returned a value inside tolerance yet failed finance grading:
- Sonnet: AAPL net_debt r2 · COST gross_margin r0, r1 · NVDA ebitda r2
- Opus: AAPL ebitda r1, r2 · COST gross_margin r2

Dominant error classes across all judge failures: **missing_materiality_caveat (8)**, wrong_value (7, mostly undisclosed alt-method values the judge rejects), citation_mismatch (4), method_choice_undisclosed (4). Every one is invisible to "did it return the number."

## Sonnet vs Opus — they fail *differently*, not just more/less

- **Signature on the hard cell (AAPL net debt):** Opus = *confidently, consistently wrong* (44,237 ×3, internally contradictory, confidence rising 0.5→0.85→0.9). Sonnet = *high-variance wrong* (three different numbers, one of which happens to land on the disclosed alt). Same 0/3 outcome, opposite pathology — Opus needs a consistency/coherence check, Sonnet needs a stability check.
- **They fail on different cells:** Opus misses materiality on AAPL EBITDA (2/3) where Sonnet passes 3/3; Sonnet is worse on COST gross margin (0/2 vs Opus 2/3) and slips once on NVDA EBITDA.
- Note the confound cuts the right way: Opus *fails its own judge* on AAPL EBITDA and net debt. Self-grading would bias toward leniency, so those Opus failures are if anything understated.

## Calibration — confidence predicts the *number*, not the *judgment*

Against Tier-1 value correctness, both models are reasonably calibrated: **≥0.95 confidence → 100%** correct (Opus 52/52, Sonnet 50/50); the signal degrades monotonically (Opus 94% / 83% in lower buckets). But confidence tracks arithmetic, not analytical soundness: at ≥0.9 confidence, models still fail the *judge* 3/69 (Opus) and 1/63 (Sonnet) — and the worst case is Opus asserting **0.9 confidence on the wrong, self-contradictory Apple net-debt answer**. A model can be well-calibrated on "is my digit right" and badly calibrated on "would an analyst accept my method." (Sonnet's `<0.8`-bucket n=3 is too small to read.)

## Flakiness

- **1 Tier-1 flaky cell:** Sonnet/AAPL/net_debt `[0,0,1]` — the $78B-swing metric, the same one that failed Tier-2 everywhere.
- **3 Tier-2 judge flips** on byte-identical answers (finding 2) — the report undercounts this because flakiness is measured on Tier-1 only.
- **1 hard parse failure:** Sonnet/COST run 1 emitted malformed JSON (trailing-comma/unquoted-key), zero metrics graded for that cell. ~3% generation-level parse-loss rate; the robust parser + checkpointing absorbed it without polluting results.

---

## Sonnet 5 extension (run 2026-07-03, +15 gen / +15 judge calls)

**Aggregate: statistically indistinguishable — Tier-1 97% (87/90), Tier-2 93% (84/90), zero prior-period hits, zero parse failures.** Same headline numbers as both older models. But the aggregate hides that the *failure deck got reshuffled*:

- **AAPL net debt: still broken, same Sonnet signature.** Three runs, three answers — **−33,763** (disclosed alt, judge's only quibble a materiality caveat) / **62,723** (debt minus cash only) / **43,960** (primary, judge pass). 1/3 trustworthy. The newest model does not fix the flagship failure.
- **NVDA net debt: a REGRESSION the older models didn't have.** 2/3 runs computed net debt as debt minus *cash only* — **−2,137 instead of −54,088** — silently omitting **$52.0B** of marketable securities, at confidence 0.8 and 0.9. Same method prior as its AAPL run-1 answer: Sonnet 5 carries a consistent "net debt = debt − cash" convention that both Sonnet 4.6 and Opus didn't exhibit here. A team that validated net-debt behavior on the old model and upgraded would inherit a new $50B-class silent error.
- **COST gross margin: FIXED — via disclosure, not via the number.** All 3 runs used the total-revenue basis (12.84%) that failed Sonnet 4.6, but *explicitly disclosed the method choice* every time → judge pass 3/3. Correct per the alts rule: the value didn't change, the transparency did.
- **Judge noise, again:** AAPL EBITDA 144,748 (right value, right method) went pass/fail/fail on caveat wording — a fourth same-value verdict flip.

**The v1.1 takeaway — evals are per-model artifacts.** Across three models the aggregate score is a constant 97/93 while the *specific* $50B-class failures move between cells (AAPL→NVDA, COST fixed, NVDA broken). "We evaluated the model" is a statement with a version number on it; a model upgrade needs a full re-run, because at constant accuracy the risk relocates.

---
*Data: `results/results.json`, `results/report.md`. Golden set treated as ground truth; no prompts or golden values edited. Models: claude-sonnet-4-6, claude-opus-4-8 (also judge), claude-sonnet-5.*
