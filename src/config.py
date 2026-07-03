"""Central config. Reads .env sitting at repo root."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
GOLDEN = DATA / "golden" / "golden.json"
RESULTS = ROOT / "results"

def _load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEN_MODELS = {
    "sonnet": os.environ.get("GEN_MODEL_A", "claude-sonnet-4-6"),
    "opus": os.environ.get("GEN_MODEL_B", "claude-opus-4-8"),
    "sonnet5": os.environ.get("GEN_MODEL_C", "claude-sonnet-5"),
}
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "claude-opus-4-8")

TICKERS = ["aapl", "dal", "cost", "nvda", "kr"]
METRICS = ["revenue", "revenue_yoy_growth", "gross_margin", "current_ratio", "net_debt", "ebitda"]

COMPANY_NAMES = {
    "aapl": "Apple Inc.",
    "dal": "Delta Air Lines, Inc.",
    "cost": "Costco Wholesale Corporation",
    "nvda": "NVIDIA Corporation",
    "kr": "The Kroger Co.",
}

def load_statements(ticker: str) -> str:
    parts = []
    for stmt in ("income", "balance", "cashflow"):
        parts.append((RAW / f"{ticker}_{stmt}.txt").read_text())
    return "\n\n".join(parts)
