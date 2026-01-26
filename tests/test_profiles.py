"""Tests for anonymization profiles."""

import pytest
from dicom_privacy_kit.core.profiles import (
    ProfileRule, BASIC_PROFILE, CLEAN_DESCRIPTORS_PROFILE, 
    PROFILES, get_profile, merge_profiles
)
from dicom_privacy_kit.core.actions import Action


class TestProfiles:
    """Test cases for anonymization profiles."""
    
    def test_basic_profile_exists(self):
        """Test that basic profile is defined."""
        assert len(BASIC_PROFILE) > 0
        assert all(isinstance(rule, ProfileRule) for rule in BASIC_PROFILE)
    
    def test_basic_profile_removes_patient_name(self):
        """Test that basic profile removes patient name."""
        rule = next(r for r in BASIC_PROFILE if r.tag == "PatientName")
        assert rule.action == Action.REMOVE
    
    def test_basic_profile_hashes_patient_id(self):
        """Test that basic profile hashes patient ID."""
        rule = next(r for r in BASIC_PROFILE if r.tag == "PatientID")
        assert rule.action == Action.HASH
    
    def test_basic_profile_keeps_patient_sex(self):
        """Test that basic profile keeps patient sex."""
        rule = next(r for r in BASIC_PROFILE if r.tag == "PatientSex")
        assert rule.action == Action.KEEP
    
    def test_clean_descriptors_profile_exists(self):
        """Test that clean descriptors profile is defined."""
        assert len(CLEAN_DESCRIPTORS_PROFILE) > 0
        assert all(isinstance(rule, ProfileRule) for rule in CLEAN_DESCRIPTORS_PROFILE)
    
    def test_profiles_registry(self):
        """Test that profiles are registered."""
        assert "basic" in PROFILES
        assert "clean_descriptors" in PROFILES
    
    def test_get_profile_basic(self):
        """Test retrieving basic profile."""
        profile = get_profile("basic")
        
        assert profile == BASIC_PROFILE
        assert len(profile) > 0
    
    def test_get_profile_clean_descriptors(self):
        """Test retrieving clean descriptors profile."""
        profile = get_profile("clean_descriptors")
        
        assert profile == CLEAN_DESCRIPTORS_PROFILE
        assert len(profile) > 0
    
    def test_get_profile_nonexistent(self):
        """Test retrieving a non-existent profile."""
        profile = get_profile("nonexistent")
        
        assert profile == []
    
    def test_merge_profiles_single(self):
        """Test merging a single profile."""
        merged = merge_profiles("basic")
        
        assert len(merged) == len(BASIC_PROFILE)
    
    def test_merge_profiles_multiple(self):
        """Test merging multiple profiles."""
        merged = merge_profiles("basic", "clean_descriptors")
        
        # Should have rules from both profiles
        assert len(merged) > len(BASIC_PROFILE)
        assert len(merged) <= len(BASIC_PROFILE) + len(CLEAN_DESCRIPTORS_PROFILE)
    
    def test_merge_profiles_no_duplicates(self):
        """Test that merged profiles don't have duplicate tags."""
        merged = merge_profiles("basic", "basic")
        
        # Should only have unique tags
        tags = [rule.tag for rule in merged]
        assert len(tags) == len(set(tags))
    
    def test_profile_rule_dataclass(self):
        """Test ProfileRule dataclass."""
        rule = ProfileRule("TestTag", Action.REMOVE)
        
        assert rule.tag == "TestTag"
        assert rule.action == Action.REMOVE
        assert rule.replacement_value == ""
    
    def test_profile_rule_with_replacement(self):
        """Test ProfileRule with replacement value."""
        rule = ProfileRule("TestTag", Action.REPLACE, "NewValue")
        
        assert rule.tag == "TestTag"
        assert rule.action == Action.REPLACE
        assert rule.replacement_value == "NewValue"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
