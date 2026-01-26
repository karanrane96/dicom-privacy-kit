"""Tests for dataset comparison."""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.diff import (
    TagDiff, DatasetDiff, compare_datasets, format_diff
)
from dicom_privacy_kit.anonymizer import AnonymizationEngine


def create_sample_dataset():
    """Create a sample dataset."""
    ds = Dataset()
    ds.PatientName = "John^Doe"
    ds.PatientID = "12345"
    ds.PatientSex = "M"
    ds.StudyDate = "20250126"
    return ds


class TestDatasetDiff:
    """Test cases for dataset comparison."""
    
    def test_compare_identical_datasets(self):
        """Test comparing identical datasets."""
        ds1 = create_sample_dataset()
        ds2 = ds1.copy()
        
        diff = compare_datasets(ds1, ds2)
        
        assert len(diff.removed) == 0
        assert len(diff.modified) == 0
        assert len(diff.added) == 0
        assert len(diff.unchanged) > 0
    
    def test_compare_removed_tags(self):
        """Test detecting removed tags."""
        from copy import deepcopy
        ds1 = create_sample_dataset()
        ds2 = deepcopy(ds1)
        del ds2["PatientName"]
        
        diff = compare_datasets(ds1, ds2)
        
        assert len(diff.removed) == 1
        assert diff.removed[0].tag == "PatientName"
        assert diff.removed[0].status == "REMOVED"
    
    def test_compare_added_tags(self):
        """Test detecting added tags."""
        from copy import deepcopy
        ds1 = create_sample_dataset()
        ds2 = deepcopy(ds1)
        ds2.PatientBirthDate = "19800101"
        
        diff = compare_datasets(ds1, ds2)
        
        assert len(diff.added) == 1
        assert diff.added[0].tag == "PatientBirthDate"
        assert diff.added[0].status == "ADDED"
    
    def test_compare_modified_tags(self):
        """Test detecting modified tags."""
        from copy import deepcopy
        ds1 = create_sample_dataset()
        ds2 = deepcopy(ds1)
        ds2.PatientName = "Jane^Doe"
        
        diff = compare_datasets(ds1, ds2)
        
        assert len(diff.modified) == 1
        assert diff.modified[0].tag == "PatientName"
        assert diff.modified[0].before_value == "John^Doe"
        assert diff.modified[0].after_value == "Jane^Doe"
        assert diff.modified[0].status == "MODIFIED"
    
    def test_compare_anonymized_dataset(self):
        """Test comparing original and anonymized datasets."""
        original = create_sample_dataset()
        engine = AnonymizationEngine()
        anonymized = engine.anonymize(original, "basic")
        
        diff = compare_datasets(original, anonymized)
        
        assert len(diff.removed) > 0 or len(diff.modified) > 0
    
    def test_format_diff_basic(self):
        """Test formatting a diff."""
        from copy import deepcopy
        ds1 = create_sample_dataset()
        ds2 = deepcopy(ds1)
        ds2.PatientName = "Jane^Doe"
        
        diff = compare_datasets(ds1, ds2)
        formatted = format_diff(diff)
        
        assert "DATASET DIFF" in formatted
        assert "MODIFIED TAGS:" in formatted
        assert "PatientName" in formatted
    
    def test_format_diff_with_removed(self):
        """Test formatting diff with removed tags."""
        from copy import deepcopy
        ds1 = create_sample_dataset()
        ds2 = deepcopy(ds1)
        del ds2["PatientName"]
        
        diff = compare_datasets(ds1, ds2)
        formatted = format_diff(diff)
        
        assert "REMOVED TAGS:" in formatted
        assert "[-]" in formatted
    
    def test_format_diff_with_added(self):
        """Test formatting diff with added tags."""
        from copy import deepcopy
        ds1 = create_sample_dataset()
        ds2 = deepcopy(ds1)
        ds2.PatientBirthDate = "19800101"
        
        diff = compare_datasets(ds1, ds2)
        formatted = format_diff(diff)
        
        assert "ADDED TAGS:" in formatted
        assert "[+]" in formatted
    
    def test_format_diff_show_unchanged(self):
        """Test formatting diff with unchanged tags shown."""
        ds1 = create_sample_dataset()
        ds2 = ds1.copy()
        
        diff = compare_datasets(ds1, ds2)
        formatted = format_diff(diff, show_unchanged=True)
        
        assert "UNCHANGED TAGS:" in formatted
        assert "[=]" in formatted
    
    def test_format_diff_hide_unchanged(self):
        """Test formatting diff with unchanged tags hidden."""
        ds1 = create_sample_dataset()
        ds2 = ds1.copy()
        
        diff = compare_datasets(ds1, ds2)
        formatted = format_diff(diff, show_unchanged=False)
        
        assert "UNCHANGED TAGS:" not in formatted
    
    def test_tag_diff_dataclass(self):
        """Test TagDiff dataclass."""
        tag_diff = TagDiff(
            tag="TestTag",
            tag_name="TestTag",
            before_value="before",
            after_value="after",
            status="MODIFIED"
        )
        
        assert tag_diff.tag == "TestTag"
        assert tag_diff.before_value == "before"
        assert tag_diff.after_value == "after"
        assert tag_diff.status == "MODIFIED"
    
    def test_dataset_diff_dataclass(self):
        """Test DatasetDiff dataclass."""
        diff = DatasetDiff(
            removed=[],
            modified=[],
            unchanged=[],
            added=[]
        )
        
        assert isinstance(diff.removed, list)
        assert isinstance(diff.modified, list)
        assert isinstance(diff.unchanged, list)
        assert isinstance(diff.added, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
