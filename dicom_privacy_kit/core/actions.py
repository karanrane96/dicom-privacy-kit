"""Anonymization actions for DICOM tags.

This module provides action handlers for anonymizing DICOM tags.

Tag State Semantics:
- MISSING tag: Not present in dataset (dataset[tag] raises KeyError)
- EMPTY tag: Present in dataset but with empty value ("")
- PRESENT tag: Present in dataset with non-empty value

Action Behavior:
- REMOVE: Deletes tag from dataset (missing -> stays missing, present -> becomes missing)
- HASH: Hashes tag value if present (missing stays missing, empty->hash(""), value->hash(value))
- EMPTY: Sets tag value to empty string (missing stays missing, any value -> "")
- KEEP: No change (all states preserved)
- REPLACE: Sets tag to specific value if present (missing stays missing)

Key Invariant:
- Actions never CREATE missing tags; they only modify or remove existing tags
- This preserves the distinction between "not applicable" (missing) and "redacted" (empty)

SEQUENCE HANDLING (VR=SQ):
- DICOM Sequences are nested datasets that this implementation does NOT recursively process
- All actions (including HASH, EMPTY, REPLACE) SKIP sequences without modification
- To remove PHI from sequences, use REMOVE action to delete the entire sequence
- Sequences encountered during anonymization are silently left unchanged with a warning
"""

from enum import Enum
from typing import Any, Callable
from pydicom import Dataset
import logging

logger = logging.getLogger(__name__)


class Action(Enum):
    """Available anonymization actions."""
    REMOVE = "remove"
    HASH = "hash"
    EMPTY = "empty"
    KEEP = "keep"
    REPLACE = "replace"


def remove_tag(dataset: Dataset, tag: str) -> None:
    """Remove a tag from the dataset.
    
    Behavior:
    - If tag is present: removes it (present -> missing)
    - If tag is missing: no-op (missing stays missing)
    - If tag is empty: removes it (empty -> missing)
    
    Special handling:
    - SEQUENCES: Removes the entire sequence (nested datasets not individually processed)
    
    This distinguishes between "not applicable" (missing) and "redacted" (removed).
    """
    try:
        del dataset[tag]
    except KeyError:
        # Tag not in dataset - expected, no-op
        logger.debug(f"Tag {tag} not present in dataset (no removal needed)")
    except AttributeError as e:
        # Unexpected: dataset is malformed or invalid
        logger.warning(f"AttributeError removing tag {tag}: {e} (dataset may be invalid)")


def hash_tag(dataset: Dataset, tag: str, hash_fn: Callable) -> None:
    """Hash a tag value.
    
    Behavior:
    - If tag is present: hashes the value (including empty string)
    - If tag is missing: no-op (missing stays missing)
    
    Special handling:
    - SEQUENCES: Skipped without modification (recursive sequence anonymization not supported)
    
    Important: Hash of empty string is different from no hash (preserves semantics).
    """
    try:
        if tag in dataset:
            from dicom_privacy_kit.core.utils import is_sequence_tag
            
            # Skip sequences - they are not hashed
            if is_sequence_tag(dataset, tag):
                logger.warning(
                    f"Tag {tag} is a DICOM Sequence (VR=SQ). Sequences are not hashed "
                    "because this implementation does not recursively process nested datasets. "
                    "Use REMOVE action to delete the sequence, or KEEP to leave it unchanged."
                )
                return
            
            original_value = str(dataset[tag].value)
            hashed_value = hash_fn(original_value)
            dataset[tag].value = hashed_value
    except KeyError:
        # Tag not in dataset - expected, no-op
        logger.debug(f"Tag {tag} not present in dataset (no hashing needed)")
    except AttributeError as e:
        # Unexpected: dataset is malformed or tag access failed
        logger.warning(f"AttributeError hashing tag {tag}: {e} (dataset may be invalid)")
    except Exception as e:
        # Unexpected exception during hashing
        logger.error(f"Unexpected error hashing tag {tag}: {type(e).__name__}: {e}")


def empty_tag(dataset: Dataset, tag: str) -> None:
    """Empty a tag value (set to empty string).
    
    Behavior:
    - If tag is present: sets to empty string (value -> "")
    - If tag is missing: no-op (missing stays missing)
    
    Special handling:
    - SEQUENCES: Skipped without modification (clearing sequence items not supported)
    
    Use to indicate tag is redacted/cleared while keeping tag presence.
    """
    try:
        if tag in dataset:
            from dicom_privacy_kit.core.utils import is_sequence_tag
            
            # Skip sequences - they are not emptied
            if is_sequence_tag(dataset, tag):
                logger.warning(
                    f"Tag {tag} is a DICOM Sequence (VR=SQ). Sequences are not emptied "
                    "because this implementation does not recursively process nested datasets. "
                    "Use REMOVE action to delete the sequence, or KEEP to leave it unchanged."
                )
                return
            
            dataset[tag].value = ""
    except KeyError:
        # Tag not in dataset - expected, no-op
        logger.debug(f"Tag {tag} not present in dataset (no emptying needed)")
    except AttributeError as e:
        # Unexpected: dataset is malformed or tag access failed
        logger.warning(f"AttributeError emptying tag {tag}: {e} (dataset may be invalid)")
    except Exception as e:
        # Unexpected exception during emptying
        logger.error(f"Unexpected error emptying tag {tag}: {type(e).__name__}: {e}")


def keep_tag(dataset: Dataset, tag: str) -> None:
    """Keep tag unchanged (no-op).
    
    All states preserved:
    - Missing stays missing
    - Empty stays empty
    - Present value unchanged
    - SEQUENCES: Left unchanged (no processing)
    """
    pass


def replace_tag(dataset: Dataset, tag: str, value: Any) -> None:
    """Replace tag with a specific value.
    
    Behavior:
    - If tag is present: replaces the value
    - If tag is missing: no-op (missing stays missing)
    
    Special handling:
    - SEQUENCES: Skipped without modification (replacing sequence items not supported)
    
    Note: This does not CREATE missing tags (preserves semantics).
    """
    try:
        if tag in dataset:
            from dicom_privacy_kit.core.utils import is_sequence_tag
            
            # Skip sequences - they are not replaced
            if is_sequence_tag(dataset, tag):
                logger.warning(
                    f"Tag {tag} is a DICOM Sequence (VR=SQ). Sequences are not replaced "
                    "because this implementation does not recursively process nested datasets. "
                    "Use REMOVE action to delete the sequence, or KEEP to leave it unchanged."
                )
                return
            
            dataset[tag].value = value
    except KeyError:
        # Tag not in dataset - expected, no-op
        logger.debug(f"Tag {tag} not present in dataset (no replacement needed)")
    except AttributeError as e:
        # Unexpected: dataset is malformed or tag access failed
        logger.warning(f"AttributeError replacing tag {tag}: {e} (dataset may be invalid)")
    except Exception as e:
        # Unexpected exception during replacement
        logger.error(f"Unexpected error replacing tag {tag}: {type(e).__name__}: {e}")


# Action handler mapping
ACTION_HANDLERS = {
    Action.REMOVE: remove_tag,
    Action.HASH: hash_tag,
    Action.EMPTY: empty_tag,
    Action.KEEP: keep_tag,
    Action.REPLACE: replace_tag,
}