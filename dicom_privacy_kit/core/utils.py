"""Utility functions for hashing, cloning, and helpers."""

import hashlib
import logging
from typing import Optional
from pydicom import Dataset

logger = logging.getLogger(__name__)


def hash_value(value: str, salt: str = "", algorithm: str = "sha256") -> str:
    """Hash a value using the specified algorithm."""
    data = f"{value}{salt}".encode('utf-8')
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data)
    return hash_obj.hexdigest()[:16]  # Truncate for readability


def clone_dataset(dataset: Dataset) -> Dataset:
    """Create a deep copy of a DICOM dataset."""
    from copy import deepcopy
    return deepcopy(dataset)


def safe_get_tag(dataset: Dataset, tag: str, default: Optional[str] = None) -> Optional[str]:
    """Safely retrieve a tag value from a dataset."""
    try:
        if tag in dataset:
            return str(dataset[tag].value)
        return default
    except Exception:
        return default


def format_tag(tag: str) -> str:
    """Normalize tag format to (GGGG,EEEE)."""
    tag = tag.replace(" ", "")
    if not tag.startswith("("):
        # Convert 0x00100010 or 00100010 format
        tag = tag.replace("0x", "").replace("0X", "")
        tag = tag.upper()
        if len(tag) == 8:
            tag = f"({tag[:4]},{tag[4:]})"
    return tag.upper()

def is_private_tag(tag_input) -> bool:
    """Determine if a DICOM tag is private (manufacturer-specific).
    
    Private tags have odd group numbers (e.g., 0x0011, 0x0013, etc.).
    These are manufacturer-specific tags that may contain PHI.
    
    Args:
        tag_input: DICOM tag as tuple (group, element) or pydicom Tag object
    
    Returns:
        True if tag is private, False otherwise
    """
    try:
        # Handle pydicom Tag objects and tuples
        if isinstance(tag_input, tuple):
            if len(tag_input) != 2:
                return False
            group = tag_input[0]
        else:
            # pydicom Tag object - has group attribute
            if hasattr(tag_input, 'group'):
                group = tag_input.group
            elif isinstance(tag_input, int):
                # Tag as single integer (group << 16 | element)
                group = (tag_input >> 16) & 0xFFFF
            else:
                return False
        
        # Group numbers are 16-bit values; private tags have odd group numbers
        return (group & 0x0001) == 1
    except TypeError:
        # Expected: unsupported input type for private tag check
        logger.debug(f"Invalid tag type for private tag check: {type(tag_input).__name__}")
        return False
    except AttributeError as e:
        # Unexpected: tag object missing expected attributes
        logger.debug(f"AttributeError checking private tag: {e}")
        return False


def get_private_tags(dataset: Dataset) -> list:
    """Extract all private tags from a DICOM dataset.
    
    Private tags (manufacturer-specific) may contain PHI and should not
    be silently ignored during anonymization.
    
    Args:
        dataset: DICOM dataset to scan
    
    Returns:
        List of (tag_tuple, element) tuples for all private tags found
    """
    private = []
    try:
        for elem in dataset:
            if is_private_tag(elem.tag):
                # Convert tag to tuple (group, element)
                tag_tuple = (elem.tag.group, elem.tag.elem)
                private.append((tag_tuple, elem))
    except Exception as e:
        logger.warning(f"Error scanning for private tags: {type(e).__name__}: {e}")
    return private


def flag_private_tags(dataset: Dataset) -> dict:
    """Flag all private tags in a dataset with risk warning.
    
    Private tags (manufacturer-specific) may contain PHI and should be
    reviewed manually since they are not in the standard tag registry.
    
    Args:
        dataset: DICOM dataset to scan
    
    Returns:
        Dictionary with private tags and their PHI risk warnings
    """
    result = {}
    for tag_tuple, elem in get_private_tags(dataset):
        try:
            value = str(elem.value)[:50]  # Truncate for display
            result[str(tag_tuple)] = {
                'keyword': elem.keyword or 'Unknown',
                'value': value,
                'vr': elem.VR if hasattr(elem, 'VR') else 'Unknown',
                'risk_warning': 'UNVERIFIED - Private tags may contain PHI'
            }
        except Exception:
            pass
    return result


def is_sequence_tag(dataset: Dataset, tag: str) -> bool:
    """Determine if a tag contains a DICOM sequence (VR=SQ).
    
    DICOM Sequences are complex nested structures containing multiple
    datasets. This implementation does NOT recursively anonymize
    sequence contents - sequences are either REMOVED or LEFT UNCHANGED.
    
    Args:
        dataset: DICOM dataset containing the tag
        tag: Tag keyword or formatted tag string
    
    Returns:
        True if tag exists and contains a sequence (VR='SQ'), False otherwise
    """
    try:
        if tag not in dataset:
            return False
        
        elem = dataset[tag]
        # Check if VR is 'SQ' (sequence)
        if hasattr(elem, 'VR'):
            return elem.VR == 'SQ'
        
        # Fallback: check if value is a Sequence instance
        from pydicom.sequence import Sequence
        return isinstance(elem.value, Sequence)
    except Exception:
        return False