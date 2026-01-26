"""PHI risk scoring for DICOM datasets.

Goals:
- Bounded: risk scores never exceed the weighted maximum for each tag
- Explainable: per-tag breakdown includes base risk, weight, category, and value
- Transparent: aggregate score is derived from the sum of per-tag contributions
"""

from typing import Dict, List
from dataclasses import dataclass
from pydicom import Dataset
import logging
from ..core.tags import get_tag_metadata, get_phi_tags
from .weights import calculate_tag_risk, get_tag_weight

logger = logging.getLogger(__name__)


@dataclass
class RiskScore:
    """Risk assessment for a DICOM dataset."""
    total_score: float
    max_score: float
    risk_percentage: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    tag_scores: Dict[str, float]
    tag_breakdown: Dict[str, Dict[str, float]]


def score_dataset(dataset: Dataset) -> RiskScore:
    """
    Calculate PHI risk score for a DICOM dataset.
    
    Args:
        dataset: DICOM dataset to assess
    
    Returns:
        RiskScore with detailed assessment
    """
    phi_tags = get_phi_tags()
    tag_scores: Dict[str, float] = {}
    tag_breakdown: Dict[str, Dict[str, float]] = {}
    total_score = 0.0
    max_score = 0.0
    
    for tag in phi_tags:
        meta = get_tag_metadata(tag)
        if not meta:
            continue
        
        # Weighted max risk for this tag
        category, weight = get_tag_weight(tag)
        tag_max = float(meta.risk_level) * weight
        max_score += tag_max
        
        try:
            if tag in dataset:
                value = str(dataset[tag].value)
                risk, base_risk, applied_weight, category = calculate_tag_risk(tag, value)
                # Only record entries that contribute (non-zero)
                if risk > 0:
                    tag_scores[tag] = risk
                    tag_breakdown[tag] = {
                        "risk": risk,
                        "base_risk": base_risk,
                        "weight": applied_weight,
                        "max_risk": tag_max,
                        "category": category,
                    }
                    total_score += risk
        except KeyError:
            # Tag not in dataset - expected, skip scoring
            logger.debug(f"PHI tag {tag} not in dataset (skipping score)")
        except AttributeError as e:
            # Unexpected: dataset or tag is malformed
            logger.warning(f"AttributeError scoring tag {tag}: {e}")
    
    risk_percentage = (total_score / max_score * 100) if max_score > 0 else 0.0
    # Bound to [0, 100]
    risk_percentage = max(0.0, min(100.0, risk_percentage))
    
    # Determine risk level
    if risk_percentage >= 75:
        risk_level = "CRITICAL"
    elif risk_percentage >= 50:
        risk_level = "HIGH"
    elif risk_percentage >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return RiskScore(
        total_score=total_score,
        max_score=max_score,
        risk_percentage=risk_percentage,
        risk_level=risk_level,
        tag_scores=tag_scores,
        tag_breakdown=tag_breakdown,
    )


def format_risk_score(score: RiskScore) -> str:
    """Format a risk score as a readable string."""
    lines = [
        "=" * 50,
        "PHI RISK ASSESSMENT",
        "=" * 50,
        f"Risk Level: {score.risk_level}",
        f"Risk Score: {score.total_score:.1f} / {score.max_score:.1f}",
        f"Risk Percentage: {score.risk_percentage:.1f}%",
        "",
        "Tag-level Risks:",
    ]
    
    for tag, risk in sorted(score.tag_scores.items(), key=lambda x: x[1], reverse=True):
        meta = get_tag_metadata(tag)
        name = meta.name if meta else "Unknown"
        breakdown = score.tag_breakdown.get(tag, {})
        weight = breakdown.get("weight", 1.0)
        base = breakdown.get("base_risk", 0.0)
        category = breakdown.get("category", "unknown")
        lines.append(f"  {tag} ({name}) [cat={category}, base={base:.1f}, weight={weight:.2f}]: {risk:.1f}")
    
    lines.append("=" * 50)
    return "\n".join(lines)
