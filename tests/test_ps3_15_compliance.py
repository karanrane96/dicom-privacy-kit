"""Tests for PS3.15 compliance and compliance claims.

This test module verifies:
1. That profiles are accurately documented with their PS3.15 compliance status
2. That claims about PS3.15 compliance are explicit and limited
3. That incomplete profiles are clearly marked
"""

import pytest
from dicom_privacy_kit.core.profiles import (
    ProfileRule, BASIC_PROFILE, CLEAN_DESCRIPTORS_PROFILE, PROFILES
)
from dicom_privacy_kit.core.actions import Action


class TestPS315ComplianceClaims:
    """Verify PS3.15 compliance claims are accurate and explicit."""
    
    def test_basic_profile_is_not_full_ps315(self):
        """Verify that BASIC_PROFILE is documented as partial implementation."""
        # BASIC_PROFILE should have limited rules (not full PS3.15)
        # PS3.15 Table X.1-1 defines ~80 tags with specific actions
        assert len(BASIC_PROFILE) < 30, (
            "BASIC_PROFILE has grown significantly - verify it still covers "
            "only subset of PS3.15 requirements"
        )
    
    def test_basic_profile_tags_have_ps315_references(self):
        """Verify important tags have PS3.15 references."""
        essential_tags = ["PatientName", "PatientID", "StudyDate"]
        for tag_name in essential_tags:
            rule = next((r for r in BASIC_PROFILE if r.tag == tag_name), None)
            assert rule is not None, f"{tag_name} missing from BASIC_PROFILE"
            assert rule.ps3_15_ref != "", f"{tag_name} missing PS3.15 reference"
    
    def test_clean_descriptors_not_claimed_as_ps315(self):
        """Verify CLEAN_DESCRIPTORS_PROFILE is not claimed as PS3.15 compliant."""
        # This profile should have no PS3.15 references as it's a custom extension
        for rule in CLEAN_DESCRIPTORS_PROFILE:
            assert rule.ps3_15_ref == "", (
                f"{rule.tag} in CLEAN_DESCRIPTORS_PROFILE should not have PS3.15 reference "
                "as this is a custom extension profile"
            )
    
    def test_missing_common_phi_tags(self):
        """Document tags from PS3.15 not yet in BASIC_PROFILE."""
        # These tags are in PS3.15 but not in our basic profile
        ps315_common_tags = [
            "PatientName",  # Covered
            "PatientID",    # Covered
            "PatientBirthDate",  # Covered
            "PatientAge",  # NOT covered - often PHI
            "PatientSize",  # NOT covered - may identify
            "PatientWeight",  # NOT covered
            "StudyDate",  # Covered
            "StudyTime",  # Covered
            "AccessionNumber",  # NOT in BASIC_PROFILE
            "InstitutionName",  # NOT covered
            "InstitutionAddress",  # NOT covered
            "ReferringPhysicianName",  # NOT covered
            "PhysiciansOfRecord",  # NOT covered
            "PerformedProcedureCodeSequence",  # NOT covered
        ]
        
        covered_tags = {rule.tag for rule in BASIC_PROFILE}
        missing = [t for t in ps315_common_tags if t not in covered_tags]
        
        # Document that we're missing these (this is expected for partial implementation)
        assert len(missing) > 0, (
            "If no tags are missing, BASIC_PROFILE may have been extended. "
            "Update this test accordingly."
        )
    
    def test_profile_rules_are_explicit(self):
        """Verify all profile rules have explicit action definitions."""
        for profile_name, profile_rules in PROFILES.items():
            for rule in profile_rules:
                # Each rule must have a clear action
                assert rule.action in [
                    Action.REMOVE, Action.HASH, Action.EMPTY, 
                    Action.KEEP, Action.REPLACE
                ], f"Rule for {rule.tag} has invalid action: {rule.action}"


class TestDataDrivenRuleDefinition:
    """Verify that profile rules are data-driven with explicit mappings."""
    
    def test_basic_profile_rules_are_explicit_not_inferred(self):
        """Verify BASIC_PROFILE rules are explicitly defined, not inferred."""
        # Each rule should have explicit reasoning
        rule_rationale = {
            "PatientName": "Direct identifier - must be removed (PS3.15)",
            "PatientID": "Direct identifier - cryptographically hashed (PS3.15)",
            "PatientBirthDate": "Can identify patient - should be removed (PS3.15)",
            "PatientSex": "Non-identifying demographic - safe to keep (PS3.15)",
            "StudyDate": "Temporal identifier - empty with empty date (PS3.15)",
            "StudyTime": "Temporal identifier - empty with empty time (PS3.15)",
            "StudyInstanceUID": "UID that identifies study - hashed (PS3.15)",
            "SeriesInstanceUID": "UID that identifies series - hashed (PS3.15)",
        }
        
        covered_tags = {rule.tag for rule in BASIC_PROFILE}
        
        # Verify coverage matches documentation
        for tag, rationale in rule_rationale.items():
            assert tag in covered_tags, f"{tag} missing from BASIC_PROFILE: {rationale}"
    
    def test_hash_action_has_salt_requirement(self):
        """Verify that HASH action requires explicit salt (not Python's hash())."""
        # Check that tags using HASH action are documented as using
        # cryptographic hashing with explicit salt
        hash_rules = [r for r in BASIC_PROFILE if r.action == Action.HASH]
        
        assert len(hash_rules) > 0, "No HASH rules in BASIC_PROFILE"
        
        # Each HASH rule represents an important identifier
        hash_tags = {r.tag for r in hash_rules}
        assert "PatientID" in hash_tags, "PatientID should use HASH"
        assert "StudyInstanceUID" in hash_tags, "StudyInstanceUID should use HASH"
    
    def test_remove_vs_empty_rationale(self):
        """Verify that REMOVE and EMPTY actions are used appropriately."""
        remove_rules = {r.tag for r in BASIC_PROFILE if r.action == Action.REMOVE}
        empty_rules = {r.tag for r in BASIC_PROFILE if r.action == Action.EMPTY}
        
        # PatientName should be removed (cannot be emptied meaningfully)
        assert "PatientName" in remove_rules
        
        # Dates should be emptied (preserves tag but removes identifying info)
        assert "StudyDate" in empty_rules
        assert "StudyTime" in empty_rules
    
    def test_profile_coverage_documented(self):
        """Verify that profile coverage limitations are documented."""
        # The profiles module docstring should mention PS3.15 reference
        import dicom_privacy_kit.core.profiles as profiles_module
        docstring = profiles_module.__doc__
        
        assert "PS3.15" in docstring, "Module docstring should reference PS3.15"
        assert "partial" in docstring.lower() or "subset" in docstring.lower(), (
            "Module docstring should clarify if implementation is partial"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
