"""Configurable risk heuristics and weights.

Scoring goals:
- Bounded: per-tag risk is capped at base_risk * category_weight (0-5 * weight)
- Explainable: each tag exposes its category and applied weight
- Tunable: weights can be adjusted without changing tag registry
"""

from typing import Dict, Tuple
from ..core.tags import get_tag_metadata


# Risk weights for different tag categories
RISK_WEIGHTS: Dict[str, float] = {
    "name": 1.0,
    "id": 1.0,
    "date": 0.8,
    "time": 0.6,
    "uid": 0.7,
    "descriptor": 0.5,
}


# Map known tags to categories (controls weight application)
TAG_CATEGORIES: Dict[str, str] = {
    "PatientName": "name",
    "PatientID": "id",
    "PatientBirthDate": "date",
    "StudyDate": "date",
    "StudyTime": "time",
    "StudyInstanceUID": "uid",
    "SeriesInstanceUID": "uid",
}


def get_tag_weight(tag: str) -> Tuple[str, float]:
    """Return (category, weight) for a tag, defaulting to neutral weight.
    
    Unknown tags fall back to category "unknown" with weight 1.0 to avoid
    accidental down-weighting.
    """
    category = TAG_CATEGORIES.get(tag, "unknown")
    return category, RISK_WEIGHTS.get(category, 1.0)


def calculate_tag_risk(tag: str, value: str) -> Tuple[float, float, float, str]:
    """
    Calculate risk for a specific tag and value.
    
    Returns a tuple of (risk, base_risk, weight, category) for explainability.
    Risk is bounded to [0, base_risk * weight].
    """
    meta = get_tag_metadata(tag)
    if not meta:
        return 0.0, 0.0, 1.0, "unknown"

    base_risk = float(meta.risk_level)
    category, weight = get_tag_weight(tag)
    max_risk = base_risk * weight

    # Empty/whitespace or anonymized placeholders carry no risk
    if not value or not value.strip():
        return 0.0, base_risk, weight, category

    lowered = value.lower()
    if lowered in {"anonymous", "anonymized", "n/a", "none"}:
        return 0.0, base_risk, weight, category

    # Hash-like values: reduce but keep bounded
    looks_hashed = len(value) in {16, 32, 64} and all(c in "0123456789abcdef" for c in lowered)
    if looks_hashed:
        reduced = max_risk * 0.2
        return min(max_risk, reduced), base_risk, weight, category

    # Normal PHI value
    return max_risk, base_risk, weight, category


def adjust_risk_weights(custom_weights: Dict[str, float]) -> None:
    """Update risk weights with custom values (category -> weight)."""
    RISK_WEIGHTS.update(custom_weights)
