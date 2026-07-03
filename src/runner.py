"""API calls + robust JSON parsing (lesson from crosby-redline-eval: never trust prose-free output)."""
import json
import re
import time

import anthropic

from . import config

_client = None

def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.API_KEY)
    return _client


def call(model: str, system: str, prompt: str, max_tokens: int = 4000, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = client().messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            # models may emit a thinking block before the text (e.g. sonnet-5);
            # take the first text block rather than assuming content[0] is text
            text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), None)
            if text is None:
                raise RuntimeError(
                    f"no text block in response (blocks: {[getattr(b, 'type', None) for b in resp.content]})"
                )
            return text
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def parse_json_array(text: str):
    """Extract the first top-level JSON array, tolerating markdown fences and preamble."""
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("[")
    if start == -1:
        raise ValueError(f"no JSON array found in: {text[:200]}")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON array")
