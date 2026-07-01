"""Natural language research question parser."""

from __future__ import annotations

_DESCRIPTIVE_KEYWORDS: list[str] = [
    "describe",
    "description",
    "descriptive",
    "distribution",
    "summary",
    "what is",
    "how many",
    "frequency",
    "overview",
    "profile",
    "mean",
    "average",
    "现状",
    "描述",
    "分布",
    "概述",
]

_DIFFERENCE_KEYWORDS: list[str] = [
    "difference",
    "differ",
    "compare",
    "comparison",
    "between",
    "among",
    "vs",
    "versus",
    "significant",
    "test",
    "group",
    "higher",
    "lower",
    "more than",
    "less than",
    "contrast",
    "gap",
    "差异",
    "比较",
    "对比",
]

_ASSOCIATION_KEYWORDS: list[str] = [
    "association",
    "associated",
    "correlation",
    "correlate",
    "relationship",
    "related",
    "link",
    "connection",
    "相关",
    "关联",
]

_PREDICTION_KEYWORDS: list[str] = [
    "predict",
    "prediction",
    "effect",
    "affect",
    "impact",
    "influence",
    "determine",
    "factor",
    "explain",
    "cause",
    "outcome",
    "determinant",
    "预测",
    "影响",
]

_CAUSAL_KEYWORDS: list[str] = [
    "causal",
    "cause",
    "causality",
    "treatment effect",
]


def classify_question(text: str) -> str:
    text_lower = text.lower()
    scores = {
        "causal": _count(text_lower, _CAUSAL_KEYWORDS),
        "prediction": _count(text_lower, _PREDICTION_KEYWORDS),
        "association": _count(text_lower, _ASSOCIATION_KEYWORDS),
        "difference": _count(text_lower, _DIFFERENCE_KEYWORDS),
        "descriptive": _count(text_lower, _DESCRIPTIVE_KEYWORDS),
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "descriptive"


def extract_variable_roles(text: str, variable_names: list[str]) -> dict:
    """Map mentioned variables to roles. Handles 'X differs by Y' pattern."""
    text_lower = text.lower()
    mentioned = [v for v in variable_names if v.lower() in text_lower]
    roles = {"dependent": None, "independent": []}

    if not mentioned:
        return roles

    # "by X" patterns -> X is independent variable
    iv_from_by = [v for v in mentioned if ("by " + v.lower()) in text_lower]

    # DV keywords
    dv_kw = [
        "affect",
        "impact",
        "influence",
        "predict",
        "explain",
        "effect on",
        "outcome",
        "dependent",
    ]

    for v in mentioned:
        for kw in dv_kw:
            if text_lower.find(kw) >= 0 and text_lower.find(v.lower()) > text_lower.find(kw):
                roles["dependent"] = v
                break
        if roles["dependent"]:
            break

    # If no DV from keywords but we have "by X", first non-IV is DV
    if roles["dependent"] is None and iv_from_by and len(mentioned) >= 2:
        for v in mentioned:
            if v not in iv_from_by:
                roles["dependent"] = v
                break

    # Build independents
    indep = [v for v in mentioned if v != roles["dependent"]]

    # Fallback: last mentioned = DV
    if roles["dependent"] is None and len(mentioned) >= 2:
        roles["dependent"] = mentioned[-1]
        indep = [v for v in mentioned if v != mentioned[-1]]

    roles["independent"] = indep
    return roles


def _count(text: str, keywords: list[str]) -> int:
    return sum(1 for kw in keywords if kw in text)


def infer_design_from_text(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in ["longitudinal", "panel", "wave", "over time"]):
        return "longitudinal"
    if any(kw in t for kw in ["experiment", "random", "randomized", "treatment"]):
        return "experimental"
    return "cross_sectional"
