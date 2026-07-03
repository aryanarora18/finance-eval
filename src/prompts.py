"""Prompt builders for generation and the finance-aware judge.

Design choice (deliberate): the generation prompt does NOT define the metrics.
Method choice under ambiguity is exactly what we are measuring — defining
"net debt" in the prompt would evaluate instruction-following, not finance judgment.
"""
import json

GEN_SYSTEM = (
    "You are a financial analyst. You answer ONLY from the financial statements provided "
    "to you. Do not use any outside knowledge of the company's financials — the statements "
    "are the sole source of truth, and they may be more recent than anything you have seen."
)

GEN_TEMPLATE = """Below are the three primary financial statements from {company}'s latest Form 10-K (period ended {period_end}). All dollar figures are in USD millions unless a caption says otherwise.

<statements>
{statements}
</statements>

For the LATEST fiscal year shown, compute each of the following metrics:
1. revenue — total revenue
2. revenue_yoy_growth — year-over-year revenue growth
3. gross_margin — gross margin
4. current_ratio — current ratio
5. net_debt — net debt
6. ebitda — EBITDA

Return ONLY a JSON array, no prose before or after. One object per metric:
{{
  "metric": "<name from the list above>",
  "determinable": true|false,        // false if it cannot be computed from these statements alone
  "value": <number or null>,          // dollar amounts in USD millions; percentages as percent (6.4 not 0.064); ratios as decimals
  "unit": "USD_millions"|"percent"|"ratio"|null,
  "method": "<the formula/line items you used and any method choices you made>",
  "inputs": [{{"label": "<line item caption>", "value": <number as it appears>}}],
  "caveats": "<anything a careful analyst should know: limitations of the face of the statements, embedded one-time items, comparability issues. Empty string if none.>",
  "confidence": <0.0-1.0, your honest probability that a careful finance professional would accept your value AND method>
}}

Rules:
- If a metric is not determinable from the provided statements, set determinable=false, value=null, and explain why in method.
- Cite in inputs the exact line-item captions and values you used.
- Do not round intermediate values; report final percentages to 2 decimals."""


def build_gen_prompt(company: str, period_end: str, statements: str) -> str:
    return GEN_TEMPLATE.format(company=company, period_end=period_end, statements=statements)


JUDGE_SYSTEM = (
    "You are a rigorous finance-aware evaluator — think senior equity-research/credit analyst "
    "grading a junior's work. You grade METHOD and ANALYTICAL JUDGMENT, not just the digit: "
    "a numerically correct answer with an undisclosed method trap or a missed material caveat is a FAIL. "
    "Critique first, verdict last. When uncertain, prefer fail."
)

JUDGE_TEMPLATE = """A model was given ONLY the three primary financial statements from {company}'s latest 10-K and asked to compute six metrics. You are grading its answers against a golden set authored by a finance professional.

<statements>
{statements}
</statements>

<golden_set>
{golden}
</golden_set>

<model_answers>
{answers}
</model_answers>

<tier1_results>
{tier1}
</tier1_results>

For EACH of the six metrics, grade the model's answer. Tier-1 already checked the raw number; your job is what Tier-1 cannot see:
- method_sound: is the method finance-correct for THIS company's presentation (right line items, right method choices)? If the golden set lists an "alt" method, it is acceptable ONLY when the answer explicitly discloses that method choice.
- grounded: do the cited inputs actually exist on the statements, with the right values, from the right column/period?
- materiality_aware: does the answer disclose the material caveats the golden set's method/traps notes call out (embedded one-time items, face-of-statements limitations, non-comparability)? A right number that hides a material caveat is not a trustworthy number.

Error classes (tag all that apply per metric, or [] if pass):
wrong_value | wrong_period_or_column | scale_or_unit_error | method_error_undisclosed | method_choice_undisclosed | fabricated_determinability | missing_materiality_caveat | citation_mismatch | overclaimed_confidence | other

Return ONLY a JSON array, one object per metric:
{{
  "metric": "<name>",
  "critique": "<2-4 sentences: what the model did, what a finance professional would say about it>",
  "method_sound": true|false,
  "grounded": true|false,
  "materiality_aware": true|false,
  "error_classes": [<strings from the list>],
  "verdict": "pass"|"fail"
}}

Verdict rule: pass requires method_sound AND grounded AND (materiality_aware OR the golden notes flag no material caveat for this metric). Tier-1 value failures are almost always judge failures too, unless the golden set marks the answer as an acceptable disclosed alternative."""


def build_judge_prompt(company: str, statements: str, golden: dict, answers: list, tier1: list) -> str:
    return JUDGE_TEMPLATE.format(
        company=company,
        statements=statements,
        golden=json.dumps(golden, indent=1),
        answers=json.dumps(answers, indent=1),
        tier1=json.dumps(tier1, indent=1),
    )
