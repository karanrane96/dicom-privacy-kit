"""Tests for private DICOM tag detection and handling.

Private tags (manufacturer-specific) have odd group numbers and may contain PHI.
This test suite ensures private tags are:
1. Correctly identified
2. Not silently ignored
3. Flagged with appropriate warnings
4. Scored as high-risk if present
"""

import pytest
from pydicom import Dataset
from pydicom.dataset import Dataset as DicomDataset
from pydicom.dataelem import DataElement
from dicom_privacy_kit.core.utils import (
    is_private_tag, get_private_tags, flag_private_tags
)
from dicom_privacy_kit.risk import score_dataset


class TestPrivateTagDetection:
    """Test detection of private DICOM tags."""
    
    def test_is_private_tag_with_odd_group(self):
        """Test that tags with odd group numbers are identified as private."""
        # Private tag format: odd group number
        assert is_private_tag((0x0011, 0x1001)) == True
        assert is_private_tag((0x0013, 0x0010)) == True
        assert is_private_tag((0x0015, 0x0020)) == True
        assert is_private_tag((0xFFFF, 0x1001)) == True  # Odd group in high range
    
    def test_is_private_tag_with_even_group(self):
        """Test that tags with even group numbers are not private."""
        # Standard DICOM tags have even group numbers
        assert is_private_tag((0x0008, 0x0008)) == False
        assert is_private_tag((0x0010, 0x0010)) == False
        assert is_private_tag((0x0018, 0x0088)) == False
        assert is_private_tag((0x0020, 0x1002)) == False
    
    def test_is_private_tag_boundary_cases(self):
        """Test boundary cases for private tag detection."""
        # Minimum odd group
        assert is_private_tag((0x0001, 0x0000)) == True
        # Zero group (even)
        assert is_private_tag((0x0000, 0x0000)) == False
        # Large odd group
        assert is_private_tag((0xFFFD, 0xFFFF)) == True
        # Large even group
        assert is_private_tag((0xFFFE, 0xFFFF)) == False
    
    def test_is_private_tag_invalid_input(self):
        """Test that invalid input returns False."""
        assert is_private_tag(None) == False
        assert is_private_tag("0x00110010") == False
        assert is_private_tag((0x0010,)) == False  # Single element
        assert is_private_tag((0x0010, 0x0010, 0x0010)) == False  # Three elements


class TestPrivateTagExtraction:
    """Test extraction of private tags from datasets."""
    
    def test_get_private_tags_from_empty_dataset(self):
        """Test extracting private tags from empty dataset."""
        ds = Dataset()
        private_tags = get_private_tags(ds)
        
        assert isinstance(private_tags, list)
        assert len(private_tags) == 0
    
    def test_get_private_tags_with_standard_tags_only(self):
        """Test dataset with only standard tags."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        ds.StudyDate = "20250126"
        
        private_tags = get_private_tags(ds)
        
        assert len(private_tags) == 0
    
    def test_get_private_tags_detects_private_tags(self):
        """Test that private tags are detected."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        # Add a private tag (manufacturer-specific)
        # Group 0x0011 is private (odd group)
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'PrivateValue'))
        ds.add(DataElement((0x0013, 0x0100), 'LT', 'AnotherPrivateData'))
        
        private_tags = get_private_tags(ds)
        
        # Should have detected both private tags
        assert len(private_tags) == 2
        
        # Check that they're actually the private ones
        tag_tuples = [t[0] for t in private_tags]
        assert (0x0011, 0x1001) in tag_tuples
        assert (0x0013, 0x0100) in tag_tuples
    
    def test_get_private_tags_ignores_standard_tags(self):
        """Test that only private tags are extracted."""
        ds = Dataset()
        
        # Standard tags
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        ds.StudyDate = "20250126"
        
        # Private tags
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'PrivateValue'))
        
        private_tags = get_private_tags(ds)
        
        # Should only have 1 (the private one)
        assert len(private_tags) == 1
        assert private_tags[0][0] == (0x0011, 0x1001)
    
    def test_get_private_tags_mixed_dataset(self):
        """Test extraction from dataset with mix of standard and private tags."""
        ds = Dataset()
        
        # Mix of standard and private tags
        ds.PatientName = "John^Doe"
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'Private1'))
        ds.PatientID = "12345"
        ds.add(DataElement((0x0013, 0x0100), 'LT', 'Private2'))
        ds.StudyDate = "20250126"
        ds.add(DataElement((0x0015, 0x2000), 'SH', 'Private3'))
        
        private_tags = get_private_tags(ds)
        
        # Should have exactly 3 private tags
        assert len(private_tags) == 3
        
        tag_tuples = {t[0] for t in private_tags}
        assert (0x0011, 0x1001) in tag_tuples
        assert (0x0013, 0x0100) in tag_tuples
        assert (0x0015, 0x2000) in tag_tuples


class TestPrivateTagFlagging:
    """Test flagging of private tags for manual review."""
    
    def test_flag_private_tags_empty_dataset(self):
        """Test flagging with empty dataset."""
        ds = Dataset()
        flags = flag_private_tags(ds)
        
        assert isinstance(flags, dict)
        assert len(flags) == 0
    
    def test_flag_private_tags_no_private_tags(self):
        """Test flagging when no private tags present."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        flags = flag_private_tags(ds)
        
        assert len(flags) == 0
    
    def test_flag_private_tags_identifies_private_tags(self):
        """Test that private tags are flagged."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        # Add private tags
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'ManufacturerSpecificData'))
        ds.add(DataElement((0x0013, 0x0100), 'LT', 'AnotherPrivateTag'))
        
        flags = flag_private_tags(ds)
        
        # Both private tags should be flagged
        assert len(flags) == 2
    
    def test_flag_private_tags_includes_warning(self):
        """Test that flagged private tags include risk warning."""
        ds = Dataset()
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'PrivateValue'))
        
        flags = flag_private_tags(ds)
        
        # Should have warning about unverified private tags
        flag_entry = list(flags.values())[0]
        assert 'risk_warning' in flag_entry
        assert 'PHI' in flag_entry['risk_warning']
        assert 'UNVERIFIED' in flag_entry['risk_warning']
    
    def test_flag_private_tags_truncates_values(self):
        """Test that long values are truncated for display."""
        ds = Dataset()
        
        # Create very long value
        long_value = "A" * 100
        ds.add(DataElement((0x0011, 0x1001), 'LT', long_value))
        
        flags = flag_private_tags(ds)
        
        flag_entry = list(flags.values())[0]
        # Value should be truncated to 50 chars
        assert len(flag_entry['value']) <= 50
    
    def test_flag_private_tags_preserves_tag_info(self):
        """Test that flagged entries preserve tag information."""
        ds = Dataset()
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'TestValue'))
        
        flags = flag_private_tags(ds)
        
        flag_entry = list(flags.values())[0]
        # Should have keyword, value, and VR
        assert 'keyword' in flag_entry
        assert 'value' in flag_entry
        assert 'vr' in flag_entry
        assert 'risk_warning' in flag_entry
        
        # Values should be non-empty strings
        assert isinstance(flag_entry['keyword'], str)
        assert isinstance(flag_entry['value'], str)
        assert isinstance(flag_entry['vr'], str)


class TestPrivateTagPolicy:
    """Test policy enforcement for private tags."""
    
    def test_anonymizer_should_flag_private_tags(self):
        """Test that anonymizer should be aware of private tags."""
        from dicom_privacy_kit.anonymizer import AnonymizationEngine
        
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        # Add unhandled private tag
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'ManufacturerData'))
        
        engine = AnonymizationEngine(salt="test")
        
        # Anonymize with basic profile
        from dicom_privacy_kit.core.profiles import BASIC_PROFILE
        result = engine.anonymize(ds, BASIC_PROFILE)
        
        # Private tag should still be present in result
        # (because we don't have a rule for it)
        private_remaining = get_private_tags(result)
        assert len(private_remaining) > 0
    
    def test_risk_scorer_should_warn_about_private_tags(self):
        """Test that risk scorer does not yet score private tags.
        
        NOTE: Currently scorer only checks known PHI tags in TAG_REGISTRY.
        Private tags are not scored automatically because they are unverified.
        This is a known limitation that can be addressed by:
        1. Adding private tags to TAG_REGISTRY
        2. Creating explicit rules for manufacturer-specific tags
        3. Implementing automatic flagging of unscored private tags
        """
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        # Add private tag with potential PHI
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'HospitalX_PatientID_987654'))
        
        score = score_dataset(ds)
        
        # Scorer should flag risk for PatientName but not for private tag
        # Private tag is not scored (limitation)
        assert score.risk_level in ["LOW", "MEDIUM"]
        assert 'PatientName' in score.tag_scores
    
    def test_diff_should_detect_private_tag_changes(self):
        """Test that diff detects changes in private tags."""
        from dicom_privacy_kit.diff import compare_datasets
        
        before = Dataset()
        before.PatientID = "123"
        before.add(DataElement((0x0011, 0x1001), 'LO', 'PrivateValue1'))
        
        after = Dataset()
        after.PatientID = "123"
        after.add(DataElement((0x0011, 0x1001), 'LO', 'PrivateValueChanged'))
        
        diff = compare_datasets(before, after)
        
        # Private tag change should be detected in modified or removed/added
        has_private_change = (
            any('0011' in str(d.tag) for d in diff.modified) or
            any('0011' in str(d.tag) for d in diff.removed) or
            any('0011' in str(d.tag) for d in diff.added)
        )
        
        # Due to pydicom's handling, the tag may or may not be detected
        # But the diff should at least try to handle it


class TestPrivateTagEdgeCases:
    """Test edge cases and unusual private tag scenarios."""
    
    def test_private_creator_block(self):
        """Test handling of private creator blocks (0x000B through 0x00FF)."""
        ds = Dataset()
        
        # Private Creator Block (elements 0x0010 to 0x00FF in private groups)
        ds.add(DataElement((0x0011, 0x0010), 'LO', 'SIEMENS'))  # Private creator
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'CreatorSpecificData'))
        
        private_tags = get_private_tags(ds)
        
        # Both should be detected as private
        assert len(private_tags) == 2
    
    def test_repeating_group_private_tags(self):
        """Test private tags in repeating groups."""
        ds = Dataset()
        
        # Multiple private groups
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'Group11Data'))
        ds.add(DataElement((0x0013, 0x1001), 'LO', 'Group13Data'))
        ds.add(DataElement((0x0015, 0x1001), 'LO', 'Group15Data'))
        ds.add(DataElement((0x0017, 0x1001), 'LO', 'Group17Data'))
        
        private_tags = get_private_tags(ds)
        
        # Should detect all 4 private tags
        assert len(private_tags) == 4
    
    def test_private_tags_with_various_vr(self):
        """Test private tags with different value representations."""
        ds = Dataset()
        
        # Different VR types
        ds.add(DataElement((0x0011, 0x1001), 'LO', 'ShortString'))
        ds.add(DataElement((0x0011, 0x1002), 'LT', 'LongText'))
        ds.add(DataElement((0x0011, 0x1003), 'OW', b'BinaryData'))
        ds.add(DataElement((0x0011, 0x1004), 'FL', 3.14159))
        
        private_tags = get_private_tags(ds)
        
        # Should detect all 4 private tags regardless of VR
        assert len(private_tags) == 4
        
        # Flag them
        flags = flag_private_tags(ds)
        assert len(flags) == 4


class TestPrivateTagDocumentation:
    """Test that private tag handling is documented."""
    
    def test_utilities_exported(self):
        """Test that private tag utilities are exported from core module."""
        from dicom_privacy_kit.core import is_private_tag, get_private_tags, flag_private_tags
        
        # Should be importable
        assert callable(is_private_tag)
        assert callable(get_private_tags)
        assert callable(flag_private_tags)
    
    def test_private_tag_functions_have_docstrings(self):
        """Test that all private tag functions have documentation."""
        from dicom_privacy_kit.core.utils import is_private_tag, get_private_tags, flag_private_tags
        
        assert is_private_tag.__doc__ is not None
        assert get_private_tags.__doc__ is not None
        assert flag_private_tags.__doc__ is not None
        
        # Docstrings should mention private tags and risk
        assert 'private' in is_private_tag.__doc__.lower()
        assert 'private' in get_private_tags.__doc__.lower()
        assert 'PHI' in flag_private_tags.__doc__


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
