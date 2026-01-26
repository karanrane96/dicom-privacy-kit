"""Tests for missing/empty/present tag handling in anonymization and diff.

This test suite audits how the codebase distinguishes between:
1. MISSING tags - not present in the dataset at all
2. EMPTY tags - present in dataset but with empty/null value
3. PRESENT tags - present in dataset with actual value
"""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.core.actions import (
    remove_tag, hash_tag, empty_tag, keep_tag, replace_tag
)
from dicom_privacy_kit.diff import compare_datasets
from dicom_privacy_kit.anonymizer import AnonymizationEngine
from dicom_privacy_kit.core.profiles import ProfileRule
from dicom_privacy_kit.core.actions import Action


class TestMissingTagHandling:
    """Test handling of missing tags."""
    
    def test_remove_missing_tag_is_safe(self):
        """Test that removing a missing tag doesn't raise error."""
        ds = Dataset()
        ds.PatientID = "12345"
        
        # PatientName doesn't exist
        assert "PatientName" not in ds
        
        # Should not raise error
        remove_tag(ds, "PatientName")
        
        # PatientID should still be there
        assert "PatientID" in ds
    
    def test_hash_missing_tag_is_safe(self):
        """Test that hashing a missing tag doesn't raise error."""
        ds = Dataset()
        
        hash_fn = lambda x: f"hash_{x}"
        
        # Should not raise error
        hash_tag(ds, "PatientName", hash_fn)
        
        # Tag should still be missing after hash attempt
        assert "PatientName" not in ds
    
    def test_empty_missing_tag_is_safe(self):
        """Test that emptying a missing tag doesn't raise error."""
        ds = Dataset()
        
        # Should not raise error
        empty_tag(ds, "PatientName")
        
        # Tag should still be missing
        assert "PatientName" not in ds
    
    def test_replace_missing_tag_is_safe(self):
        """Test that replacing a missing tag doesn't raise error."""
        ds = Dataset()
        
        # Should not raise error
        replace_tag(ds, "PatientName", "Anonymous")
        
        # Tag should still be missing (not auto-created)
        assert "PatientName" not in ds
    
    def test_keep_missing_tag_is_safe(self):
        """Test that keeping a missing tag is safe."""
        ds = Dataset()
        
        # Should not raise error
        keep_tag(ds, "PatientName")
        
        # Tag should still be missing
        assert "PatientName" not in ds


class TestEmptyTagHandling:
    """Test handling of empty tags."""
    
    def test_empty_tag_with_empty_value(self):
        """Test that a tag with empty string value is considered present."""
        ds = Dataset()
        ds.PatientName = ""
        
        # Tag should be present but empty
        assert "PatientName" in ds
        assert ds.PatientName == ""
    
    def test_empty_action_on_empty_tag(self):
        """Test that EMPTY action on already-empty tag doesn't error."""
        ds = Dataset()
        ds.PatientName = ""
        
        # Should not raise error
        empty_tag(ds, "PatientName")
        
        # Tag should still be empty
        assert "PatientName" in ds
        assert ds.PatientName == ""
    
    def test_hash_empty_tag(self):
        """Test that hashing an empty tag creates a hash of empty string."""
        ds = Dataset()
        ds.PatientName = ""
        
        hash_fn = lambda x: f"hash({x})"
        hash_tag(ds, "PatientName", hash_fn)
        
        # Tag should be hashed version of empty string
        assert "PatientName" in ds
        assert ds.PatientName == "hash()"
    
    def test_remove_empty_tag(self):
        """Test that removing an empty tag removes it completely."""
        ds = Dataset()
        ds.PatientName = ""
        
        assert "PatientName" in ds
        
        remove_tag(ds, "PatientName")
        
        # Tag should now be missing
        assert "PatientName" not in ds
    
    def test_replace_empty_tag(self):
        """Test that replacing an empty tag updates it."""
        ds = Dataset()
        ds.PatientName = ""
        
        replace_tag(ds, "PatientName", "Anonymous")
        
        # Tag should now have the replacement value
        assert "PatientName" in ds
        assert ds.PatientName == "Anonymous"


class TestPresentTagHandling:
    """Test handling of tags with actual values."""
    
    def test_remove_present_tag(self):
        """Test that removing a present tag removes it."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        assert "PatientName" in ds
        
        remove_tag(ds, "PatientName")
        
        # Tag should be gone
        assert "PatientName" not in ds
    
    def test_hash_present_tag(self):
        """Test that hashing a present tag changes the value."""
        ds = Dataset()
        ds.PatientID = "12345"
        
        hash_fn = lambda x: f"hash_{x}"
        hash_tag(ds, "PatientID", hash_fn)
        
        # Tag should be hashed
        assert "PatientID" in ds
        assert ds.PatientID == "hash_12345"
        assert ds.PatientID != "12345"
    
    def test_empty_present_tag(self):
        """Test that emptying a present tag clears it."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        empty_tag(ds, "PatientName")
        
        # Tag should still be present but empty
        assert "PatientName" in ds
        assert ds.PatientName == ""
    
    def test_replace_present_tag(self):
        """Test that replacing a present tag updates it."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        replace_tag(ds, "PatientName", "Anonymous")
        
        # Tag should have new value
        assert "PatientName" in ds
        assert ds.PatientName == "Anonymous"
    
    def test_keep_present_tag(self):
        """Test that keeping a present tag leaves it unchanged."""
        ds = Dataset()
        ds.PatientID = "12345"
        
        keep_tag(ds, "PatientID")
        
        # Tag should be unchanged
        assert "PatientID" in ds
        assert ds.PatientID == "12345"


class TestDiffMissingVsEmptyVsPresent:
    """Test that diff correctly distinguishes missing, empty, and present tags."""
    
    def test_diff_detects_added_missing_tag(self):
        """Test that diff shows tag as ADDED when it goes from missing to present."""
        before = Dataset()
        after = Dataset()
        after.PatientName = "John^Doe"
        
        diff = compare_datasets(before, after)
        
        # Should show as ADDED
        assert len(diff.added) == 1
        added_tag = diff.added[0]
        assert added_tag.tag == "PatientName"
        assert added_tag.before_value == ""
        assert added_tag.after_value == "John^Doe"
        assert added_tag.status == "ADDED"
    
    def test_diff_detects_removed_present_tag(self):
        """Test that diff shows tag as REMOVED when it goes from present to missing."""
        before = Dataset()
        before.PatientName = "John^Doe"
        after = Dataset()
        
        diff = compare_datasets(before, after)
        
        # Should show as REMOVED
        assert len(diff.removed) == 1
        removed_tag = diff.removed[0]
        assert removed_tag.tag == "PatientName"
        assert removed_tag.before_value == "John^Doe"
        assert removed_tag.after_value == ""
        assert removed_tag.status == "REMOVED"
    
    def test_diff_detects_emptied_tag(self):
        """Test that diff shows MODIFIED when tag goes from present to empty."""
        before = Dataset()
        before.PatientName = "John^Doe"
        after = Dataset()
        after.PatientName = ""
        
        diff = compare_datasets(before, after)
        
        # Should show as MODIFIED (present -> empty, not removed)
        assert len(diff.modified) == 1
        assert len(diff.removed) == 0
        modified_tag = diff.modified[0]
        assert modified_tag.tag == "PatientName"
        assert modified_tag.before_value == "John^Doe"
        assert modified_tag.after_value == ""
        assert modified_tag.status == "MODIFIED"
    
    def test_diff_detects_empty_to_present_transition(self):
        """Test that diff shows MODIFIED when tag goes from empty to present."""
        before = Dataset()
        before.PatientName = ""
        after = Dataset()
        after.PatientName = "Jane^Doe"
        
        diff = compare_datasets(before, after)
        
        # Should show as MODIFIED
        assert len(diff.modified) == 1
        assert len(diff.added) == 0
        modified_tag = diff.modified[0]
        assert modified_tag.before_value == ""
        assert modified_tag.after_value == "Jane^Doe"
        assert modified_tag.status == "MODIFIED"
    
    def test_diff_detects_missing_to_empty_transition(self):
        """Test that diff shows ADDED when tag goes from missing to empty."""
        before = Dataset()
        after = Dataset()
        after.PatientName = ""
        
        diff = compare_datasets(before, after)
        
        # Should show as ADDED (was missing, now present even if empty)
        assert len(diff.added) == 1
        added_tag = diff.added[0]
        assert added_tag.before_value == ""
        assert added_tag.after_value == ""
        assert added_tag.status == "ADDED"
    
    def test_diff_detects_unchanged_empty_tag(self):
        """Test that diff shows UNCHANGED when tag is empty in both."""
        before = Dataset()
        before.PatientName = ""
        after = Dataset()
        after.PatientName = ""
        
        diff = compare_datasets(before, after)
        
        # Should show as UNCHANGED
        assert len(diff.unchanged) == 1
        assert len(diff.modified) == 0
        unchanged_tag = diff.unchanged[0]
        assert unchanged_tag.before_value == ""
        assert unchanged_tag.after_value == ""
        assert unchanged_tag.status == "UNCHANGED"
    
    def test_diff_unchanged_missing_in_both(self):
        """Test that diff doesn't list tags missing in both datasets."""
        before = Dataset()
        before.PatientID = "123"
        after = Dataset()
        after.PatientID = "123"
        
        diff = compare_datasets(before, after)
        
        # PatientName is missing in both - should not be listed anywhere
        assert len(diff.removed) == 0
        assert len(diff.added) == 0
        
        # PatientID should be unchanged
        assert len(diff.unchanged) == 1


class TestAnonymizationWithMissingTags:
    """Test that anonymization engine correctly handles missing tags."""
    
    def test_anonymize_missing_tag_with_remove(self):
        """Test that REMOVE action on missing tag doesn't error."""
        ds = Dataset()
        ds.PatientID = "12345"
        
        engine = AnonymizationEngine()
        profile = [ProfileRule("PatientName", Action.REMOVE)]
        
        # Should not raise error even though PatientName is missing
        result = engine.anonymize(ds, profile)
        
        # PatientID should still be there (unchanged)
        assert "PatientID" in result
    
    def test_anonymize_missing_tag_with_hash(self):
        """Test that HASH action on missing tag doesn't error."""
        ds = Dataset()
        ds.PatientID = "12345"
        
        engine = AnonymizationEngine(salt="test")
        profile = [ProfileRule("PatientName", Action.HASH)]
        
        # Should not raise error
        result = engine.anonymize(ds, profile)
        
        # PatientID should still be there
        assert "PatientID" in result
    
    def test_anonymize_empty_tag_with_empty_action(self):
        """Test that EMPTY action on empty tag doesn't error."""
        ds = Dataset()
        ds.PatientName = ""
        ds.PatientID = "12345"
        
        engine = AnonymizationEngine()
        profile = [ProfileRule("PatientName", Action.EMPTY)]
        
        result = engine.anonymize(ds, profile)
        
        # PatientName should still be empty
        assert "PatientName" in result
        assert result.PatientName == ""
        # PatientID unchanged
        assert result.PatientID == "12345"
    
    def test_anonymize_present_tag_with_hash(self):
        """Test that HASH action on present tag hashes correctly."""
        ds = Dataset()
        ds.PatientID = "12345"
        
        engine = AnonymizationEngine(salt="test_salt")
        profile = [ProfileRule("PatientID", Action.HASH)]
        
        result = engine.anonymize(ds, profile)
        
        # PatientID should be hashed
        assert "PatientID" in result
        assert result.PatientID != "12345"
    
    def test_anonymize_mixed_tags(self):
        """Test anonymization with mix of missing, empty, and present tags."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        ds.PatientBirthDate = ""
        # PatientSex is missing
        
        engine = AnonymizationEngine(salt="salt")
        profile = [
            ProfileRule("PatientName", Action.REMOVE),
            ProfileRule("PatientID", Action.HASH),
            ProfileRule("PatientBirthDate", Action.EMPTY),
            ProfileRule("PatientSex", Action.KEEP),
        ]
        
        result = engine.anonymize(ds, profile)
        
        # PatientName should be removed
        assert "PatientName" not in result
        # PatientID should be hashed
        assert "PatientID" in result
        assert result.PatientID != "12345"
        # PatientBirthDate should still be empty
        assert "PatientBirthDate" in result
        assert result.PatientBirthDate == ""
        # PatientSex should still be missing
        assert "PatientSex" not in result


class TestEdgeCases:
    """Test edge cases in missing/empty/present tag handling."""
    
    def test_tag_with_none_value(self):
        """Test handling of tags with None value."""
        ds = Dataset()
        # Some DICOM values might be None
        ds.PatientName = None
        
        # Should not error
        empty_tag(ds, "PatientName")
        
        # Tag should still exist
        assert "PatientName" in ds
    
    def test_tag_with_zero_value(self):
        """Test handling of tags with zero value."""
        ds = Dataset()
        ds.PatientAge = 0
        
        hash_fn = lambda x: f"hash_{x}"
        hash_tag(ds, "PatientAge", hash_fn)
        
        # Should hash the zero value
        assert "PatientAge" in ds
        assert ds.PatientAge == "hash_0"
    
    def test_tag_with_whitespace_value(self):
        """Test handling of tags with whitespace-only value."""
        ds = Dataset()
        ds.PatientName = "   "
        
        # Tag is present (not empty string)
        assert "PatientName" in ds
        assert ds.PatientName == "   "
        
        empty_tag(ds, "PatientName")
        
        # After empty action, should be empty string
        assert ds.PatientName == ""
    
    def test_diff_with_whitespace_vs_empty(self):
        """Test that diff distinguishes whitespace from empty."""
        before = Dataset()
        before.PatientName = "   "
        after = Dataset()
        after.PatientName = ""
        
        diff = compare_datasets(before, after)
        
        # Should show as modified (different values)
        assert len(diff.modified) == 1
        assert diff.modified[0].before_value == "   "
        assert diff.modified[0].after_value == ""


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
