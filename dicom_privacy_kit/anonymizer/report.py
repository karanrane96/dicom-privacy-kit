"""Compliance and anonymization reporting."""

from typing import Dict, List
from dataclasses import dataclass
import logging
from pydicom import Dataset
from ..core.tags import get_phi_tags, get_tag_metadata

logger = logging.getLogger(__name__)


@dataclass
class ComplianceReport:
    """Report on anonymization compliance."""
    total_phi_tags: int
    removed_phi_tags: int
    remaining_phi_tags: int
    compliance_percentage: float
    remaining_tags: List[str]


def generate_compliance_report(
    original: Dataset,
    anonymized: Dataset
) -> ComplianceReport:
    """
    Generate a compliance report comparing original and anonymized datasets.
    
    Args:
        original: Original DICOM dataset
        anonymized: Anonymized DICOM dataset
    
    Returns:
        ComplianceReport with statistics
    """
    phi_tags = get_phi_tags()
    
    # Count PHI tags in original
    original_phi = [tag for tag in phi_tags if tag in original]
    total_phi = len(original_phi)
    
    # Count remaining PHI tags in anonymized
    remaining_phi = []
    for tag in original_phi:
        try:
            if tag in anonymized:
                # Check if value changed
                original_val = str(original[tag].value)
                anon_val = str(anonymized[tag].value)
                if original_val == anon_val and original_val != "":
                    remaining_phi.append(tag)
        except KeyError:
            # Tag in original but not in anonymized - expected (removed)
            logger.debug(f"PHI tag {tag} not in anonymized dataset (removed as expected)")
        except AttributeError as e:
            # Unexpected: dataset or tag is malformed
            logger.warning(f"AttributeError checking tag {tag} in compliance report: {e}")
    
    removed_phi = total_phi - len(remaining_phi)
    compliance = (removed_phi / total_phi * 100) if total_phi > 0 else 100.0
    
    return ComplianceReport(
        total_phi_tags=total_phi,
        removed_phi_tags=removed_phi,
        remaining_phi_tags=len(remaining_phi),
        compliance_percentage=compliance,
        remaining_tags=remaining_phi
    )


def format_report(report: ComplianceReport) -> str:
    """Format a compliance report as a readable string."""
    lines = [
        "=" * 50,
        "COMPLIANCE REPORT",
        "=" * 50,
        f"Total PHI Tags: {report.total_phi_tags}",
        f"Removed/Modified: {report.removed_phi_tags}",
        f"Remaining Unchanged: {report.remaining_phi_tags}",
        f"Compliance: {report.compliance_percentage:.1f}%",
        "",
    ]
    
    if report.remaining_tags:
        lines.append("Remaining PHI Tags:")
        for tag in report.remaining_tags:
            meta = get_tag_metadata(tag)
            name = meta.name if meta else "Unknown"
            lines.append(f"  - {tag} ({name})")
    
    lines.append("=" * 50)
    return "\n".join(lines)
