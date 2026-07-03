"""Tier-1: deterministic assertions.

Checks per metric answer:
  schema_ok        — required fields present, types sane
  value_ok         — within tolerance of golden primary OR a listed alt (alt => flagged for judge)
  unit_ok          — unit string matches golden; catches percent-as-decimal and millions/billions slips
  grounded_ok      — every cited input value appears verbatim (normalized) in the source statements
  determinable_ok  — matches golden determinability (catches fabrication on DAL gross margin)
  prior_period_hit — value matches the PRIOR fiscal year instead (memorization / wrong-column signal)
"""
from __future__ import annotations

import re


def _norm_num(x: float) -> set[str]:
    """Renderings a number might take in the statement text."""
    out = set()
    for v in (x, -x):
        if float(v).is_integer():
            i = int(v)
            out.add(f"{i:,}")
            out.add(str(i))
        else:
            out.add(f"{v:,}")
            out.add(str(v))
    return out


def _close(value: float, target: float, spec: dict) -> bool:
    if "tol_abs" in spec:
        return abs(value - target) <= spec["tol_abs"]
    tol = max(spec.get("tol_rel", 0.005) * abs(target), spec.get("tol_abs_min", 0))
    return abs(value - target) <= tol


def check_answer(ans: dict, gspec: dict, statements: str) -> dict:
    r = {
        "metric": ans.get("metric"),
        "schema_ok": True,
        "determinable_ok": True,
        "value_ok": None,
        "matched": None,        # "primary" | "alt" | None
        "unit_ok": None,
        "grounded_ok": None,
        "ungrounded_inputs": [],
        "prior_period_hit": False,
        "notes": [],
    }

    required = {"metric", "determinable", "value", "method", "inputs", "confidence"}
    if not required.issubset(ans.keys()):
        r["schema_ok"] = False
        r["notes"].append(f"missing fields: {sorted(required - set(ans.keys()))}")
        return r

    golden_determinable = gspec.get("determinable", True)
    ans_determinable = bool(ans.get("determinable"))

    if not golden_determinable:
        # Correct behavior: refuse. A confident value here is fabricated determinability.
        r["determinable_ok"] = not ans_determinable and ans.get("value") in (None, 0)
        if not r["determinable_ok"]:
            r["notes"].append("golden says NOT determinable from face; model produced a value")
        r["value_ok"] = r["determinable_ok"]
        return r

    if not ans_determinable or ans.get("value") is None:
        r["determinable_ok"] = False
        r["value_ok"] = False
        r["notes"].append("model declined a metric the golden set says is determinable from the face")
        return r

    try:
        value = float(ans["value"])
    except (TypeError, ValueError):
        r["schema_ok"] = False
        r["notes"].append("value not numeric")
        return r

    target = gspec["primary"]

    # unit / scale checks
    r["unit_ok"] = ans.get("unit") == gspec["unit"]
    if gspec["unit"] == "percent" and abs(value) < 1 and abs(target) >= 1:
        if _close(value * 100, target, gspec):
            r["unit_ok"] = False
            r["notes"].append("percent reported as decimal fraction")
            value = value * 100
    if gspec["unit"] == "USD_millions" and value != 0 and target != 0:
        for scale, label in ((1000, "billions vs millions"), (0.001, "thousands vs millions")):
            if _close(value * scale, target, gspec):
                r["unit_ok"] = False
                r["notes"].append(f"scale slip: {label}")

    # value vs primary, then vs disclosed-method alts
    if _close(value, target, gspec):
        r["value_ok"] = True
        r["matched"] = "primary"
    else:
        for alt in gspec.get("alts", []):
            if _close(value, alt["value"], gspec):
                r["value_ok"] = True
                r["matched"] = "alt"
                r["notes"].append(f"matched ALT method (judge must verify disclosure): {alt['requires']}")
                break
        else:
            r["value_ok"] = False

    # wrong-period detection (memorization / column slip)
    prior = gspec.get("prior")
    if prior is not None and not (r["value_ok"] and r["matched"] == "primary"):
        if _close(value, prior, gspec):
            r["prior_period_hit"] = True
            r["notes"].append(f"value matches PRIOR fiscal year ({prior}) — wrong period or recited priors")

    # grounding: cited inputs must exist in the statement text
    hits, misses = 0, []
    for inp in ans.get("inputs", [])[:20]:
        v = inp.get("value")
        if v is None:
            continue
        try:
            forms = _norm_num(float(v))
        except (TypeError, ValueError):
            misses.append(inp)
            continue
        if any(f in statements for f in forms):
            hits += 1
        else:
            misses.append(inp)
    r["grounded_ok"] = len(misses) == 0
    r["ungrounded_inputs"] = misses
    return r


def summarize(results: list[dict]) -> dict:
    n = len(results)
    return {
        "n": n,
        "value_pass": sum(1 for r in results if r["value_ok"]),
        "grounded_pass": sum(1 for r in results if r.get("grounded_ok") in (True, None)),
        "prior_period_hits": sum(1 for r in results if r["prior_period_hit"]),
        "alt_method_matches": sum(1 for r in results if r.get("matched") == "alt"),
    }
