"""Tests for anonymization actions."""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.core.actions import (
    Action, remove_tag, hash_tag, empty_tag, keep_tag, replace_tag, ACTION_HANDLERS
)


class TestActions:
    """Test cases for anonymization actions."""
    
    def test_remove_tag(self):
        """Test removing a tag from dataset."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        remove_tag(ds, "PatientName")
        
        assert "PatientName" not in ds
        assert "PatientID" in ds
    
    def test_remove_nonexistent_tag(self):
        """Test removing a tag that doesn't exist."""
        ds = Dataset()
        ds.PatientID = "12345"
        
        # Should not raise an error
        remove_tag(ds, "PatientName")
        assert "PatientID" in ds
    
    def test_hash_tag(self):
        """Test hashing a tag value."""
        ds = Dataset()
        ds.PatientID = "12345"
        original_value = ds.PatientID
        
        hash_fn = lambda x: f"hashed_{x}"
        hash_tag(ds, "PatientID", hash_fn)
        
        assert ds.PatientID == "hashed_12345"
        assert ds.PatientID != original_value
    
    def test_hash_nonexistent_tag(self):
        """Test hashing a tag that doesn't exist."""
        ds = Dataset()
        
        hash_fn = lambda x: f"hashed_{x}"
        # Should not raise an error
        hash_tag(ds, "PatientID", hash_fn)
    
    def test_empty_tag(self):
        """Test emptying a tag value."""
        ds = Dataset()
        ds.StudyDate = "20250126"
        
        empty_tag(ds, "StudyDate")
        
        assert "StudyDate" in ds
        assert ds.StudyDate == ""
    
    def test_empty_nonexistent_tag(self):
        """Test emptying a tag that doesn't exist."""
        ds = Dataset()
        
        # Should not raise an error
        empty_tag(ds, "StudyDate")
    
    def test_keep_tag(self):
        """Test keeping a tag unchanged."""
        ds = Dataset()
        ds.PatientSex = "M"
        original_value = ds.PatientSex
        
        keep_tag(ds, "PatientSex")
        
        assert ds.PatientSex == original_value
    
    def test_replace_tag(self):
        """Test replacing a tag value."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        replace_tag(ds, "PatientName", "Anonymous")
        
        assert ds.PatientName == "Anonymous"
    
    def test_replace_nonexistent_tag(self):
        """Test replacing a tag that doesn't exist."""
        ds = Dataset()
        
        # Should not raise an error
        replace_tag(ds, "PatientName", "Anonymous")
    
    def test_action_handlers_mapping(self):
        """Test that all actions have handlers."""
        assert Action.REMOVE in ACTION_HANDLERS
        assert Action.HASH in ACTION_HANDLERS
        assert Action.EMPTY in ACTION_HANDLERS
        assert Action.KEEP in ACTION_HANDLERS
        assert Action.REPLACE in ACTION_HANDLERS


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
