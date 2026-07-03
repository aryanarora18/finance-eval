"""Aggregate results/results.json → results/report.md (pass-rate grids, error taxonomy, calibration)."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config


def main():
    path = config.ROOT / (sys.argv[1] if len(sys.argv) > 1 else "results/results.json")
    records = json.loads(path.read_text())

    # (model, ticker, metric) → list of per-run dicts
    cells = defaultdict(list)
    for rec in records:
        jmap = {j["metric"]: j for j in (rec["judge"] or [])}
        amap = {a["metric"]: a for a in rec["answers"]}
        for t1 in rec["tier1"]:
            m = t1["metric"]
            cells[(rec["model"], rec["ticker"], m)].append(
                {"t1": t1, "judge": jmap.get(m), "ans": amap.get(m, {})}
            )

    models = sorted({k[0] for k in cells})
    lines = ["# Finance-Eval Results", ""]

    # ---- pass-rate grid per model ----
    for model in models:
        lines += [f"## {model} ({config.GEN_MODELS[model]})", ""]
        header = "| ticker | " + " | ".join(config.METRICS) + " |"
        lines += [header, "|" + "---|" * (len(config.METRICS) + 1)]
        for ticker in config.TICKERS:
            row = [ticker.upper()]
            for metric in config.METRICS:
                runs = cells.get((model, ticker, metric), [])
                if not runs:
                    row.append("·")
                    continue
                t1p = sum(1 for r in runs if r["t1"]["value_ok"])
                jp = sum(1 for r in runs if r["judge"] and r["judge"]["verdict"] == "pass")
                jn = sum(1 for r in runs if r["judge"])
                cell = f"T1 {t1p}/{len(runs)}"
                if jn:
                    cell += f", T2 {jp}/{jn}"
                flags = []
                if any(r["t1"]["prior_period_hit"] for r in runs):
                    flags.append("PRIOR-YR")
                if any(r["t1"].get("matched") == "alt" for r in runs):
                    flags.append("alt")
                if any(r["t1"].get("grounded_ok") is False for r in runs):
                    flags.append("unground")
                if flags:
                    cell += " ⚠" + ",".join(flags)
                row.append(cell)
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # ---- error taxonomy ----
    taxo = Counter()
    examples = defaultdict(list)
    for (model, ticker, metric), runs in cells.items():
        for r in runs:
            if r["judge"] and r["judge"]["verdict"] == "fail":
                for ec in r["judge"].get("error_classes", []) or ["unclassified"]:
                    taxo[ec] += 1
                    if len(examples[ec]) < 3:
                        examples[ec].append(f"{model}/{ticker}/{metric}")
    lines += ["## Error taxonomy (judge-failed metric-runs, all models)", ""]
    lines += ["| error class | count | examples |", "|---|---|---|"]
    for ec, n in taxo.most_common():
        lines.append(f"| {ec} | {n} | {', '.join(examples[ec])} |")
    lines.append("")

    # ---- tier1 vs tier2 disagreement: what a generic eval hides ----
    hidden = []
    for (model, ticker, metric), runs in cells.items():
        for i, r in enumerate(runs):
            if r["t1"]["value_ok"] and r["judge"] and r["judge"]["verdict"] == "fail":
                hidden.append((model, ticker, metric, i, ", ".join(r["judge"].get("error_classes", []))))
    lines += [f"## Right number, failed judgment (Tier-1 pass, judge fail): {len(hidden)} metric-runs", ""]
    for h in hidden:
        lines.append(f"- {h[0]}/{h[1]}/{h[2]} run{h[3]}: {h[4]}")
    lines.append("")

    # ---- calibration ----
    lines += ["## Calibration (stated confidence vs Tier-1 value correctness)", ""]
    lines += ["| model | bucket | n | actual pass rate |", "|---|---|---|---|"]
    for model in models:
        buckets = defaultdict(list)
        for (m, _, _), runs in cells.items():
            if m != model:
                continue
            for r in runs:
                c = r["ans"].get("confidence")
                if c is None or r["t1"]["value_ok"] is None:
                    continue
                b = "≥0.95" if c >= 0.95 else "0.8–0.95" if c >= 0.8 else "<0.8"
                buckets[b].append(1 if r["t1"]["value_ok"] else 0)
        for b in ("≥0.95", "0.8–0.95", "<0.8"):
            v = buckets.get(b, [])
            if v:
                lines.append(f"| {model} | {b} | {len(v)} | {sum(v)/len(v):.0%} |")
    lines.append("")

    # ---- flakiness: metrics whose pass/fail flips across runs ----
    flaky = [
        f"- {m}/{t}/{metric}: {[int(bool(r['t1']['value_ok'])) for r in runs]}"
        for (m, t, metric), runs in sorted(cells.items())
        if len({bool(r["t1"]["value_ok"]) for r in runs}) > 1
    ]
    lines += [f"## Non-determinism: {len(flaky)} flaky cells (Tier-1 verdict flips across runs)", ""] + flaky

    # ---- Tier-2 flakiness: judge verdict flips; split out same-value flips (judge/prose noise) ----
    j_flaky, samevalue_flaky = [], []
    for (m, t, metric), runs in sorted(cells.items()):
        verdicts = [r["judge"]["verdict"] for r in runs if r["judge"]]
        if len(verdicts) > 1 and len(set(verdicts)) > 1:
            row = f"- {m}/{t}/{metric}: {verdicts}"
            values = {json.dumps(r["ans"].get("value")) for r in runs if r["judge"]}
            (samevalue_flaky if len(values) == 1 else j_flaky).append(row)
    lines += ["", f"## Non-determinism, Tier-2: {len(j_flaky) + len(samevalue_flaky)} cells where the JUDGE verdict flips", ""]
    lines += [f"### …on the SAME value ({len(samevalue_flaky)}) — gate rides on caveat prose + judge noise, invisible to a value-only eval", ""]
    lines += samevalue_flaky or ["(none)"]
    lines += ["", f"### …with differing values ({len(j_flaky)})", ""]
    lines += j_flaky or ["(none)"]

    out = config.ROOT / "results" / "report.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"→ {out}")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
