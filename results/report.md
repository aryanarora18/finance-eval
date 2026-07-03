# Finance-Eval Results

## opus (claude-opus-4-8)

| ticker | revenue | revenue_yoy_growth | gross_margin | current_ratio | net_debt | ebitda |
|---|---|---|---|---|---|---|
| AAPL | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 0/3, T2 0/3 | T1 3/3, T2 1/3 |
| DAL | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |
| COST | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 2/3 ⚠alt | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |
| NVDA | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |
| KR | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |

## sonnet (claude-sonnet-4-6)

| ticker | revenue | revenue_yoy_growth | gross_margin | current_ratio | net_debt | ebitda |
|---|---|---|---|---|---|---|
| AAPL | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 1/3, T2 0/3 ⚠alt | T1 3/3, T2 3/3 |
| DAL | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |
| COST | T1 2/2, T2 2/2 | T1 2/2, T2 2/2 | T1 2/2, T2 0/2 ⚠alt | T1 2/2, T2 2/2 | T1 2/2, T2 2/2 | T1 2/2, T2 2/2 ⚠alt |
| NVDA | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 2/3 ⚠alt |
| KR | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |

## sonnet5 (claude-sonnet-5)

| ticker | revenue | revenue_yoy_growth | gross_margin | current_ratio | net_debt | ebitda |
|---|---|---|---|---|---|---|
| AAPL | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 2/3, T2 1/3 ⚠alt | T1 3/3, T2 1/3 |
| DAL | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |
| COST | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |
| NVDA | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 1/3, T2 1/3 | T1 3/3, T2 3/3 ⚠alt |
| KR | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 | T1 3/3, T2 3/3 ⚠alt |

## Error taxonomy (judge-failed metric-runs, all models)

| error class | count | examples |
|---|---|---|
| missing_materiality_caveat | 12 | sonnet/aapl/net_debt, sonnet/aapl/net_debt, sonnet/aapl/net_debt |
| wrong_value | 10 | sonnet/aapl/net_debt, sonnet/aapl/net_debt, sonnet/cost/gross_margin |
| method_choice_undisclosed | 5 | sonnet/aapl/net_debt, sonnet/cost/gross_margin, opus/aapl/net_debt |
| method_error_undisclosed | 5 | sonnet/cost/gross_margin, sonnet/cost/gross_margin, opus/cost/gross_margin |
| citation_mismatch | 4 | sonnet/aapl/net_debt, sonnet/aapl/net_debt, sonnet/aapl/net_debt |
| other | 3 | sonnet/cost/gross_margin, opus/aapl/net_debt, opus/aapl/net_debt |

## Right number, failed judgment (Tier-1 pass, judge fail): 10 metric-runs

- sonnet/aapl/net_debt run2: missing_materiality_caveat, citation_mismatch
- sonnet/cost/gross_margin run0: wrong_value, method_error_undisclosed, method_choice_undisclosed
- sonnet/cost/gross_margin run1: wrong_value, method_error_undisclosed, other
- sonnet/nvda/ebitda run2: missing_materiality_caveat
- opus/aapl/ebitda run1: missing_materiality_caveat
- opus/aapl/ebitda run2: missing_materiality_caveat
- opus/cost/gross_margin run2: method_error_undisclosed
- sonnet5/aapl/net_debt run0: missing_materiality_caveat
- sonnet5/aapl/ebitda run0: missing_materiality_caveat
- sonnet5/aapl/ebitda run2: missing_materiality_caveat

## Calibration (stated confidence vs Tier-1 value correctness)

| model | bucket | n | actual pass rate |
|---|---|---|---|
| opus | ≥0.95 | 52 | 100% |
| opus | 0.8–0.95 | 32 | 94% |
| opus | <0.8 | 6 | 83% |
| sonnet | ≥0.95 | 50 | 100% |
| sonnet | 0.8–0.95 | 31 | 100% |
| sonnet | <0.8 | 3 | 33% |
| sonnet5 | ≥0.95 | 55 | 100% |
| sonnet5 | 0.8–0.95 | 26 | 92% |
| sonnet5 | <0.8 | 9 | 89% |

## Non-determinism: 3 flaky cells (Tier-1 verdict flips across runs)

- sonnet/aapl/net_debt: [0, 0, 1]
- sonnet5/aapl/net_debt: [1, 0, 1]
- sonnet5/nvda/net_debt: [0, 0, 1]

## Non-determinism, Tier-2: 6 cells where the JUDGE verdict flips

### …on the SAME value (3) — gate rides on caveat prose + judge noise, invisible to a value-only eval

- opus/aapl/ebitda: ['pass', 'fail', 'fail']
- sonnet/nvda/ebitda: ['pass', 'pass', 'fail']
- sonnet5/aapl/ebitda: ['fail', 'pass', 'fail']

### …with differing values (3)

- opus/cost/gross_margin: ['pass', 'pass', 'fail']
- sonnet5/aapl/net_debt: ['fail', 'fail', 'pass']
- sonnet5/nvda/net_debt: ['fail', 'fail', 'pass']
