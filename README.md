# finance-eval — a finance-aware trust harness for financial-statement AI

**[Start with the findings →](findings/FINDINGS.md)**

Measures whether LLMs can be **trusted** to read financial statements and reason over the numbers — and produces a **taxonomy of where/why they fail**. The differentiator: correctness is defined with finance rigor (method choices, materiality, disclosure), not just "did it return the number."

## The shape of every test

Feed a model the three primary statements from a real 10-K (SEC EDGAR, verbatim) and ask for six metrics: revenue, YoY growth, gross margin, current ratio, net debt, EBITDA. **The prompt deliberately does not define the metrics** — method choice under ambiguity is what's being measured. Then check two ways:

- **Tier 1 (deterministic, `src/tier1.py`)** — value within tolerance? Right unit/scale/sign? Cited line items actually on the statements? Does the value match the *prior* fiscal year instead (memorization / column-slip detector)? Correct refusal where a metric isn't determinable from the face?
- **Tier 2 (finance-aware judge, `src/judge`-prompt in `prompts.py`)** — right *method* for this company's presentation? Grounded in the right column? Did it disclose the material caveats (embedded one-time items, face-of-statement limitations)? **A numerically right answer that hides a material caveat fails.**

## The roster is the test design

| Company | FY end | Why it's here |
|---|---|---|
| DAL | 2025-12-31 | No gross-profit line exists → fabrication probe. Debt+finance leases combined on face. EBITDA embeds a $1.2B investment gain. |
| COST | 2025-08-31 | Gross margin has two defensible methods 172bp apart (membership fees in or out) → silent-method-blending probe. Current debt portion not on face. |
| NVDA | 2026-01-25 | Post-cutoff filing, revenue +65% → memorization probe. $52B marketable securities → net-debt method. $8.9B paper gains inside EBITDA. |
| KR | 2026-01-31 | Post-cutoff, boring, levered. $2.5B one-time impairment halved operating profit → the materiality-blindness probe. |
| AAPL | 2025-09-27 | Control + "recite vs read" test. Net debt swings $78B on one method choice (non-current marketable securities). Interest expense not on face → EBITDA add-back impossible. |

Golden set: `data/golden/golden.json` — every value hand-derived from the face of the statements, arithmetic machine-verified, with `method`, `alts` (defensible only-if-disclosed alternatives), `traps`, and `prior` (wrong-period detector).

## Run it

```bash
cd finance-eval
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m evals.test_offline          # meta-eval of the harness itself, no API calls
.venv/bin/python -m evals.run --runs 3          # full sweep: 2 models × 5 companies × 3 runs (+judge)
.venv/bin/python -m evals.report                # → results/report.md
```

Needs `ANTHROPIC_API_KEY` in `.env` — copy `.env.example` to `.env` and fill in your key (the `GEN_MODEL_*` / `JUDGE_MODEL` keys are prefilled with the versions used here). The run checkpoints after every cell and resumes — safe to interrupt. Smoke test first: `--runs 1 --models sonnet --tickers dal`.

Results in this repo were produced with `claude-sonnet-4-6` (`sonnet`), `claude-opus-4-8` (`opus`, also the judge), and `claude-sonnet-5` (`sonnet5`).

Known confound (logged, accepted for v1): Opus is both a generation model and the judge — it grades itself. Tier-1 is deterministic and unaffected; treat Tier-2 deltas between models with that caveat.

## Layout

```
data/raw/          verbatim EDGAR R-file statement text + manifest.json (provenance)
data/golden/       golden.json — the finance-defined answer key
src/               config, prompts, API runner, tier1 assertions
evals/run.py       orchestrator (gen → tier1 → judge → results/results.json)
evals/report.py    pass-rate grids, error taxonomy, calibration, flakiness
evals/test_offline.py  meta-eval: plants known defects, asserts the harness catches them
findings/          the actual product: what broke and why it matters
DECISIONS.md       decision/tradeoff log
```
