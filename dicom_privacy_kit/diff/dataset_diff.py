"""Before/after comparison for DICOM datasets.

This module compares two datasets and identifies tag differences.

Tag State Semantics:
- MISSING: Tag not present in dataset
- EMPTY: Tag present but with empty value ("")
- PRESENT: Tag present with non-empty value

Diff Categories:
- REMOVED: Tag present in 'before', missing in 'after'
- MODIFIED: Tag present in both, values differ
- UNCHANGED: Tag present in both, values identical
- ADDED: Tag missing in 'before', present in 'after'

Important: EMPTY is considered PRESENT for diff purposes.
- Empty tag in both datasets = UNCHANGED
- Missing tag going to empty value = ADDED
- Present value becoming empty = MODIFIED

Value Comparison:
Comparisons use normalized element values, not string representations.
This ensures proper handling of:
- Numeric values (1.0 == 1)
- Date/time values
- Binary data
- Sequences
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging
from pydicom import Dataset
from .element_compare import normalize_element_value, elements_are_equal

logger = logging.getLogger(__name__)


@dataclass
class TagDiff:
    """Difference for a single tag."""
    tag: str
    tag_name: str
    before_value: str
    after_value: str
    status: str  # REMOVED, MODIFIED, UNCHANGED, ADDED


@dataclass
class DatasetDiff:
    """Complete diff between two datasets."""
    removed: List[TagDiff]
    modified: List[TagDiff]
    unchanged: List[TagDiff]
    added: List[TagDiff]


def compare_datasets(before: Dataset, after: Dataset) -> DatasetDiff:
    """
    Compare two DICOM datasets and identify differences.
    
    Handles all tag state combinations (missing, empty, present):
    - REMOVED: present -> missing
    - MODIFIED: value1 -> value2 (where value1 != value2)
    - UNCHANGED: same value in both (including both empty)
    - ADDED: missing -> present (including missing -> empty)
    
    Args:
        before: Original dataset
        after: Modified dataset
    
    Returns:
        DatasetDiff with categorized changes
        
    Note: Tags missing in both datasets are not listed in any category.
    """
    removed = []
    modified = []
    unchanged = []
    added = []
    
    # Get all tags from both datasets using dir_* which gives keywords
    before_tags = {elem.keyword for elem in before if elem.keyword}
    after_tags = {elem.keyword for elem in after if elem.keyword}
    
    # Check removed tags
    for keyword in before_tags - after_tags:
        try:
            elem = before[keyword]
            before_val = str(elem.value) if elem else ""
            removed.append(TagDiff(
                tag=keyword,
                tag_name=keyword,
                before_value=before_val,
                after_value="",
                status="REMOVED"
            ))
        except (KeyError, AttributeError) as e:
            # Unexpected: tag listed as removed but inaccessible
            logger.warning(f"Error accessing removed tag {keyword}: {type(e).__name__}: {e}")
    
    # Check added tags
    for keyword in after_tags - before_tags:
        try:
            elem = after[keyword]
            after_val = str(elem.value) if elem else ""
            added.append(TagDiff(
                tag=keyword,
                tag_name=keyword,
                before_value="",
                after_value=after_val,
                status="ADDED"
            ))
        except (KeyError, AttributeError) as e:
            # Unexpected: tag listed as added but inaccessible
            logger.warning(f"Error accessing added tag {keyword}: {type(e).__name__}: {e}")
    
    # Check modified/unchanged tags
    for keyword in before_tags & after_tags:
        try:
            before_elem = before[keyword]
            after_elem = after[keyword]
            
            # Use normalized element comparison
            if elements_are_equal(before_elem, after_elem):
                # Elements are equal - generate string representation for display
                before_val = str(before_elem.value) if before_elem else ""
                after_val = str(after_elem.value) if after_elem else ""
                unchanged.append(TagDiff(
                    tag=keyword,
                    tag_name=keyword,
                    before_value=before_val,
                    after_value=after_val,
                    status="UNCHANGED"
                ))
            else:
                # Elements differ - generate string representations
                before_val = str(before_elem.value) if before_elem else ""
                after_val = str(after_elem.value) if after_elem else ""
                modified.append(TagDiff(
                    tag=keyword,
                    tag_name=keyword,
                    before_value=before_val,
                    after_value=after_val,
                    status="MODIFIED"
                ))
        except (KeyError, AttributeError) as e:
            # Unexpected: tag in intersection but inaccessible or element structure invalid
            logger.warning(f"Error accessing tag {keyword} in diff: {type(e).__name__}: {e}")
    
    return DatasetDiff(
        removed=removed,
        modified=modified,
        unchanged=unchanged,
        added=added
    )


def format_diff(diff: DatasetDiff, show_unchanged: bool = False) -> str:
    """
    Format a dataset diff as a readable string.
    
    Args:
        diff: DatasetDiff to format
        show_unchanged: Include unchanged tags in output
    
    Returns:
        Formatted diff string
    """
    lines = [
        "=" * 70,
        "DATASET DIFF",
        "=" * 70,
        f"Removed: {len(diff.removed)} | Modified: {len(diff.modified)} | "
        f"Unchanged: {len(diff.unchanged)} | Added: {len(diff.added)}",
        "",
    ]
    
    if diff.removed:
        lines.append("REMOVED TAGS:")
        for item in diff.removed:
            lines.append(f"  [-] {item.tag}: {item.before_value}")
        lines.append("")
    
    if diff.modified:
        lines.append("MODIFIED TAGS:")
        for item in diff.modified:
            lines.append(f"  [~] {item.tag}:")
            lines.append(f"      Before: {item.before_value}")
            lines.append(f"      After:  {item.after_value}")
        lines.append("")
    
    if diff.added:
        lines.append("ADDED TAGS:")
        for item in diff.added:
            lines.append(f"  [+] {item.tag}: {item.after_value}")
        lines.append("")
    
    if show_unchanged and diff.unchanged:
        lines.append("UNCHANGED TAGS:")
        for item in diff.unchanged:
            lines.append(f"  [=] {item.tag}: {item.before_value}")
        lines.append("")
    
    lines.append("=" * 70)
    return "\n".join(lines)
