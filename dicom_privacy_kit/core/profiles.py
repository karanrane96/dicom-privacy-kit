"""DICOM anonymization profiles based on PS3.15.

This module implements a PARTIAL/SUBSET of anonymization profiles referenced 
in DICOM PS3.15 (Security and System Management Profiles).

IMPORTANT:
- BASIC_PROFILE covers only common PHI tags (~8 tags), not the full PS3.15 
  specification which defines actions for ~80 tags.
- CLEAN_DESCRIPTORS_PROFILE is a CUSTOM extension, not part of PS3.15.

For full PS3.15 compliance, implement complete rule set from PS3.15 Table X.1-1.

References:
- PS3.15 Table X.1-1: Defined Tags and Actions (Basic Profile)
- https://dicom.nema.org/medical/dicom/current/output/html/part15.html
"""

from typing import Dict, List
from dataclasses import dataclass
from .actions import Action


@dataclass
class ProfileRule:
    """Rule defining action for a DICOM tag.
    
    Attributes:
        tag: DICOM tag keyword (e.g., "PatientName")
        action: Action to take (REMOVE, HASH, EMPTY, KEEP, REPLACE)
        replacement_value: Value for REPLACE action
        ps3_15_ref: Section reference in PS3.15 standard (optional)
    """
    tag: str
    action: Action
    replacement_value: str = ""
    ps3_15_ref: str = ""  # PS3.15 standard reference


# PS3.15 BASIC PROFILE - Subset Implementation
# Reference: PS3.15 Section X.4 "Baseline Confidentiality Profile"
# 
# NOTE: This is a PARTIAL implementation of the Basic Profile.
# PS3.15 defines a more comprehensive set of ~80 tags with specific
# actions (Remove, Replace, Hash, Keep, Encrypt).
# 
# This implementation covers only the most common PHI tags.
# For full PS3.15 compliance, use a complete rule set that includes:
# - All patient identifying information (names, IDs, contact info)
# - All dates/times that could identify a patient
# - All descriptive text fields
# - All UIDs and serial numbers
# - Derived/computed values
# 
# See: DICOM PS3.15 Table X.1-1 "Defined Tags and Actions"
BASIC_PROFILE: List[ProfileRule] = [
    ProfileRule("PatientName", Action.REMOVE, ps3_15_ref="X.1-1"),
    ProfileRule("PatientID", Action.HASH, ps3_15_ref="X.1-1"),
    ProfileRule("PatientBirthDate", Action.REMOVE, ps3_15_ref="X.1-1"),
    ProfileRule("PatientSex", Action.KEEP, ps3_15_ref="X.1-1"),  # Non-identifying
    ProfileRule("StudyDate", Action.EMPTY, ps3_15_ref="X.1-1"),
    ProfileRule("StudyTime", Action.EMPTY, ps3_15_ref="X.1-1"),
    ProfileRule("StudyInstanceUID", Action.HASH, ps3_15_ref="X.1-1"),
    ProfileRule("SeriesInstanceUID", Action.HASH, ps3_15_ref="X.1-1"),
]


# CUSTOM PROFILE - Not part of PS3.15
# This profile extends the basic profile with descriptor cleaning.
# NOT OFFICIALLY SPECIFIED IN PS3.15 - for demonstration/reference only.
# 
# WARNING: Using this alone does NOT guarantee PS3.15 compliance.
# This is an optional addition that can be merged with BASIC_PROFILE
# to remove text descriptors that may contain PHI.
CLEAN_DESCRIPTORS_PROFILE: List[ProfileRule] = [
    ProfileRule("AccessionNumber", Action.REMOVE),
    ProfileRule("StudyDescription", Action.REMOVE),
    ProfileRule("SeriesDescription", Action.REMOVE),
]


PROFILES: Dict[str, List[ProfileRule]] = {
    "basic": BASIC_PROFILE,
    "clean_descriptors": CLEAN_DESCRIPTORS_PROFILE,
}


def get_profile(name: str) -> List[ProfileRule]:
    """Retrieve an anonymization profile by name.
    
    Args:
        name: Profile name ("basic", "clean_descriptors", etc.)
    
    Returns:
        List of ProfileRule objects
        
    WARNING:
        - "basic" profile is a PARTIAL implementation of PS3.15
        - "clean_descriptors" is a CUSTOM profile, NOT part of PS3.15 standard
        
    For full PS3.15 compliance, consider implementing complete rule set from
    PS3.15 Table X.1-1 covering all ~80 defined tags.
    """
    return PROFILES.get(name, [])


def merge_profiles(*profile_names: str) -> List[ProfileRule]:
    """Merge multiple profiles into a single rule set.
    
    Args:
        *profile_names: One or more profile names to merge
        
    Returns:
        Combined list of ProfileRule objects (duplicates removed by tag)
        
    WARNING:
        This merges whatever profiles are requested. Ensure that the
        combination of profiles aligns with your compliance requirements.
        
        Example:
            merge_profiles("basic", "clean_descriptors")
            # Combines basic profile with additional descriptor cleaning
    """
    merged = []
    seen_tags = set()
    
    for name in profile_names:
        for rule in get_profile(name):
            if rule.tag not in seen_tags:
                merged.append(rule)
                seen_tags.add(rule.tag)
    
    return merged
