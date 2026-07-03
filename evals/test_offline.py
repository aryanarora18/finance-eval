"""Offline meta-eval of the harness itself — no API calls.

Feeds synthetic model answers with KNOWN defects through Tier-1 and asserts each
defect is caught (and each correct answer passes). If the eval can't catch a
planted failure, the eval is the bug. Run: python -m evals.test_offline
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

from src import config, tier1, runner

golden = json.loads(config.GOLDEN.read_text())
FAILS = []


def check(name, cond):
    print(("  PASS " if cond else "  FAIL ") + name)
    if not cond:
        FAILS.append(name)


def ans(metric, value, unit, inputs=None, determinable=True, confidence=0.9, method="m"):
    return {
        "metric": metric, "determinable": determinable, "value": value, "unit": unit,
        "method": method, "inputs": inputs or [], "caveats": "", "confidence": confidence,
    }


nvda_stmts = config.load_statements("nvda")
dal_stmts = config.load_statements("dal")
aapl_stmts = config.load_statements("aapl")
kr_stmts = config.load_statements("kr")

print("1. correct NVDA revenue passes, grounded")
r = tier1.check_answer(
    ans("revenue", 215938, "USD_millions", [{"label": "Revenue", "value": 215938}]),
    golden["nvda"]["metrics"]["revenue"], nvda_stmts)
check("value_ok", r["value_ok"] is True and r["matched"] == "primary")
check("grounded", r["grounded_ok"] is True)

print("2. NVDA prior-year revenue (memorization) is caught")
r = tier1.check_answer(
    ans("revenue", 130497, "USD_millions", [{"label": "Revenue", "value": 130497}]),
    golden["nvda"]["metrics"]["revenue"], nvda_stmts)
check("value fails", r["value_ok"] is False)
check("prior_period_hit", r["prior_period_hit"] is True)

print("3. billions-vs-millions scale slip flagged")
r = tier1.check_answer(
    ans("revenue", 215.938, "USD_millions"),
    golden["nvda"]["metrics"]["revenue"], nvda_stmts)
check("value fails", r["value_ok"] is False)
check("scale note", any("scale slip" in n for n in r["notes"]))

print("4. DAL gross margin refusal is CORRECT; a value is fabrication")
r = tier1.check_answer(
    ans("gross_margin", None, None, determinable=False),
    golden["dal"]["metrics"]["gross_margin"], dal_stmts)
check("refusal passes", r["value_ok"] is True and r["determinable_ok"] is True)
r = tier1.check_answer(
    ans("gross_margin", 9.19, "percent"),
    golden["dal"]["metrics"]["gross_margin"], dal_stmts)
check("fabricated value fails", r["value_ok"] is False)

print("5. AAPL net debt: primary passes; disclosed-alt matches as alt; garbage fails")
g = golden["aapl"]["metrics"]["net_debt"]
check("primary", tier1.check_answer(ans("net_debt", 43960, "USD_millions"), g, aapl_stmts)["matched"] == "primary")
check("alt", tier1.check_answer(ans("net_debt", -33763, "USD_millions"), g, aapl_stmts)["matched"] == "alt")
check("garbage", tier1.check_answer(ans("net_debt", 12000, "USD_millions"), g, aapl_stmts)["value_ok"] is False)

print("6. percent-as-decimal caught (KR yoy 0.0035 vs 0.35)")
r = tier1.check_answer(
    ans("revenue_yoy_growth", 0.0035, "percent"),
    golden["kr"]["metrics"]["revenue_yoy_growth"], kr_stmts)
check("unit flagged or fail", r["unit_ok"] is False or r["value_ok"] is False)

print("7. hallucinated citation caught")
r = tier1.check_answer(
    ans("current_ratio", 3.905, "ratio", [{"label": "Total current assets", "value": 999999}]),
    golden["nvda"]["metrics"]["current_ratio"], nvda_stmts)
check("ungrounded", r["grounded_ok"] is False)

print("8. KR ebitda: silent impairment addback (7,668) fails Tier-1")
r = tier1.check_answer(
    ans("ebitda", 7668, "USD_millions"),
    golden["kr"]["metrics"]["ebitda"], kr_stmts)
check("fails", r["value_ok"] is False)

print("9. negative-value grounding: DAL -679 cited as 679 still grounds")
r = tier1.check_answer(
    ans("ebitda", 9307, "USD_millions", [{"label": "Interest expense, net", "value": 679}]),
    golden["dal"]["metrics"]["ebitda"], dal_stmts)
check("grounded", r["grounded_ok"] is True)

print("10. parser: fenced / preamble / nested JSON")
t = 'Here you go:\n```json\n[{"metric": "revenue", "inputs": [{"label": "a[b]", "value": 1}]}]\n```'
check("parses", runner.parse_json_array(t)[0]["metric"] == "revenue")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("all offline checks pass — harness ready for a live run")
