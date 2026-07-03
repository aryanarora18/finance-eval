"""Orchestrator: generation → Tier-1 → Tier-2 judge → results/results.json

Usage:
  python -m evals.run --runs 3 --models sonnet opus          # full sweep
  python -m evals.run --runs 1 --models sonnet --tickers dal  # smoke test
  python -m evals.run --skip-judge ...                        # Tier-1 only
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config, prompts, runner, tier1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--models", nargs="+", default=["sonnet", "opus"], choices=list(config.GEN_MODELS))
    ap.add_argument("--tickers", nargs="+", default=config.TICKERS, choices=config.TICKERS)
    ap.add_argument("--skip-judge", action="store_true")
    ap.add_argument("--out", default="results/results.json")
    args = ap.parse_args()

    golden = json.loads(config.GOLDEN.read_text())
    out_path = config.ROOT / args.out
    out_path.parent.mkdir(exist_ok=True)

    # resume support: don't re-buy completed cells
    records = []
    done = set()
    if out_path.exists():
        records = json.loads(out_path.read_text())
        done = {(r["model"], r["ticker"], r["run"]) for r in records}
        print(f"resuming: {len(records)} records already present")

    total = len(args.models) * len(args.tickers) * args.runs
    i = 0
    for model_key in args.models:
        model_id = config.GEN_MODELS[model_key]
        for ticker in args.tickers:
            statements = config.load_statements(ticker)
            g = golden[ticker]
            gen_prompt = prompts.build_gen_prompt(
                config.COMPANY_NAMES[ticker], g["period_end"], statements
            )
            for run_idx in range(args.runs):
                i += 1
                if (model_key, ticker, run_idx) in done:
                    continue
                print(f"[{i}/{total}] gen {model_key} × {ticker} run {run_idx} ...", flush=True)
                t0 = time.time()
                raw = runner.call(model_id, prompts.GEN_SYSTEM, gen_prompt)
                try:
                    answers = runner.parse_json_array(raw)
                except ValueError as e:
                    answers = []
                    print(f"  PARSE FAIL: {e}")
                t1_results = [
                    tier1.check_answer(a, g["metrics"].get(a.get("metric"), {}), statements)
                    for a in answers
                    if a.get("metric") in g["metrics"]
                ]
                rec = {
                    "model": model_key,
                    "model_id": model_id,
                    "ticker": ticker,
                    "run": run_idx,
                    "gen_seconds": round(time.time() - t0, 1),
                    "raw_len": len(raw),
                    "parse_ok": bool(answers),
                    "answers": answers,
                    "tier1": t1_results,
                    "judge": None,
                }

                if not args.skip_judge and answers:
                    jp = prompts.build_judge_prompt(
                        config.COMPANY_NAMES[ticker], statements, g["metrics"], answers, t1_results
                    )
                    jraw = runner.call(config.JUDGE_MODEL, prompts.JUDGE_SYSTEM, jp, max_tokens=3000)
                    try:
                        rec["judge"] = runner.parse_json_array(jraw)
                    except ValueError as e:
                        rec["judge"] = None
                        print(f"  JUDGE PARSE FAIL: {e}")

                records.append(rec)
                out_path.write_text(json.dumps(records, indent=1))  # checkpoint every cell
                s = tier1.summarize(t1_results)
                jf = (
                    sum(1 for j in rec["judge"] if j.get("verdict") == "fail")
                    if rec["judge"] else "—"
                )
                print(
                    f"  tier1 value {s['value_pass']}/{s['n']}"
                    f" | prior-period hits {s['prior_period_hits']}"
                    f" | alt-method {s['alt_method_matches']}"
                    f" | judge fails {jf}"
                )

    print(f"\ndone → {out_path}")


if __name__ == "__main__":
    main()
