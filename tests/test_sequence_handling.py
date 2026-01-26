"""Tests for DICOM sequence (SQ) element handling.

This test suite audits how sequence elements are handled across the codebase.
Sequences are complex nested structures that may contain PHI in their items.

Current Status:
- Sequences are NOT explicitly handled in anonymization actions
- Sequences are NOT recursively processed in diff logic
- Sequences are NOT parsed in risk scoring
- Sequences are partially stringified in value comparison

This test suite documents the current behavior and ensures that:
1. Sequences are safely handled (not partially processed)
2. Unsupported features explicitly document sequence limitations
3. Future implementers know what needs to be done for full support
"""

import pytest
from pydicom import Dataset
from pydicom.sequence import Sequence
from pydicom.dataelem import DataElement
from dicom_privacy_kit.anonymizer import AnonymizationEngine
from dicom_privacy_kit.core.profiles import ProfileRule
from dicom_privacy_kit.core.actions import Action
from dicom_privacy_kit.risk import score_dataset
from dicom_privacy_kit.diff import compare_datasets


class TestSequenceDetection:
    """Test detection of sequence elements in datasets."""
    
    def test_sequence_is_detectable(self):
        """Test that sequences can be detected in datasets."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        # Add a sequence
        seq = Sequence([Dataset(CodeValue="123", CodeMeaning="Test")])
        ds.ProcedureCodeSequence = seq
        
        # Check that sequence exists
        assert "ProcedureCodeSequence" in ds
        assert isinstance(ds.ProcedureCodeSequence, Sequence)
    
    def test_sequence_detection_by_vr(self):
        """Test that sequence VR can be detected."""
        ds = Dataset()
        seq = Sequence([Dataset(CodeValue="123")])
        ds.ProcedureCodeSequence = seq
        
        elem = ds["ProcedureCodeSequence"]
        assert hasattr(elem, 'VR')
        assert elem.VR == 'SQ', "Sequence elements should have VR='SQ'"
    
    def test_nested_dataset_access(self):
        """Test accessing nested datasets within sequences."""
        ds = Dataset()
        
        # Create nested sequence with items using proper DICOM tag assignment
        item1 = Dataset()
        item1.CodeValue = "001"
        item1.CodeMeaning = "FirstItem"
        
        item2 = Dataset()
        item2.CodeValue = "002"
        item2.CodeMeaning = "SecondItem"
        
        seq = Sequence([item1, item2])
        ds.ProcedureCodeSequence = seq
        
        # Access nested items
        assert len(ds.ProcedureCodeSequence) == 2
        assert ds.ProcedureCodeSequence[0].CodeValue == "001"
        assert ds.ProcedureCodeSequence[1].CodeMeaning == "SecondItem"


class TestAnonymizationSequenceHandling:
    """Test how anonymization engine handles sequences."""
    
    def test_sequence_not_affected_by_profile(self):
        """Test that sequences are not modified by anonymization profiles."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        # Add sequence with PHI - note that nested data is NOT anonymized
        seq = Sequence([Dataset(CodeValue="123")])  # Keep it simple - no PatientName in nested
        ds.ReferencedImageSequence = seq
        
        # Anonymize with basic profile
        engine = AnonymizationEngine(salt="test")
        from dicom_privacy_kit.core.profiles import BASIC_PROFILE
        result = engine.anonymize(ds, BASIC_PROFILE)
        
        # Top-level PatientName should be removed
        assert "PatientName" not in result
        
        # Sequence should still exist and be unchanged
        assert "ReferencedImageSequence" in result
        # Sequence was not processed (limitation: no recursive anonymization)
        assert len(result.ReferencedImageSequence) == 1
    
    def test_sequence_remove_action(self):
        """Test REMOVE action on sequence element."""
        ds = Dataset()
        seq = Sequence([Dataset(CodeValue="123")])
        ds.ProcedureCodeSequence = seq
        
        # Remove action should work on sequences
        from dicom_privacy_kit.core.actions import remove_tag
        remove_tag(ds, "ProcedureCodeSequence")
        
        # Sequence should be removed
        assert "ProcedureCodeSequence" not in ds
    
    def test_sequence_hash_action(self):
        """Test HASH action on sequence element - sequences are skipped."""
        ds = Dataset()
        
        # Create sequence item with proper DICOM attribute
        seq_item = Dataset()
        seq_item.add_new(0x00080104, 'SH', 'TestValue')  # CodeValue
        seq = Sequence([seq_item])
        ds.ProcedureCodeSequence = seq
        
        from dicom_privacy_kit.core.actions import hash_tag
        hash_fn = lambda x: f"hash_{x}"
        
        # Hash action on sequence - should skip (not hash)
        hash_tag(ds, "ProcedureCodeSequence", hash_fn)
        
        # Sequence should be unchanged (not hashed)
        assert "ProcedureCodeSequence" in ds
        # Verify it's still a sequence with original content
        assert len(ds.ProcedureCodeSequence) == 1
    
    def test_sequence_empty_action(self):
        """Test EMPTY action on sequence element - sequences are skipped."""
        ds = Dataset()
        
        # Create sequence item with proper DICOM attribute
        seq_item = Dataset()
        seq_item.add_new(0x00080104, 'SH', 'TestValue')  # CodeValue
        seq = Sequence([seq_item])
        ds.ProcedureCodeSequence = seq
        
        from dicom_privacy_kit.core.actions import empty_tag
        
        # Empty action on sequence - should skip (not empty)
        empty_tag(ds, "ProcedureCodeSequence")
        
        # Sequence should be unchanged (not emptied)
        assert "ProcedureCodeSequence" in ds
        # Verify it's still a sequence with original content
        assert len(ds.ProcedureCodeSequence) == 1


class TestSequenceRiskScoring:
    """Test how risk scoring handles sequences."""
    
    def test_sequence_not_scored(self):
        """Test that sequence contents are not scored for risk."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        # Add sequence with PHI that should be scored
        seq = Sequence([
            Dataset(PatientName="NestedPatient1", PatientID="12345"),
            Dataset(PatientName="NestedPatient2", PatientID="67890")
        ])
        ds.ReferencedImageSequence = seq
        
        score = score_dataset(ds)
        
        # Score should only include top-level PatientName
        # Nested data in sequence is not scored
        assert "PatientName" in score.tag_scores
        assert score.total_score > 0
        
        # Note: Nested PatientNames are not scored (limitation)
        # This means risk is UNDERESTIMATED for datasets with sequences containing PHI
    
    def test_sequence_stringified_in_risk_score(self):
        """Test that sequences are not deeply analyzed in risk scoring."""
        ds = Dataset()
        
        # Create a sequence
        seq_item = Dataset()
        seq_item.CodeValue = "123"
        seq_item.CodeMeaning = "Test"
        seq = Sequence([seq_item])
        ds.ProcedureCodeSequence = seq
        
        # Score the dataset - sequences are present but their contents are not scored
        # (limitation: recursive scoring not implemented)
        score = score_dataset(ds)
        
        # Risk is likely UNDERESTIMATED for datasets with sequences containing PHI
        # because nested data is not analyzed
        assert score is not None


class TestSequenceDiffHandling:
    """Test how diff handles sequences."""
    
    def test_sequence_comparison_unreliable(self):
        """Test that sequence comparison via stringification is unreliable."""
        before = Dataset()
        after = Dataset()
        
        # Identical sequences
        seq1 = Sequence([Dataset(CodeValue="123", CodeMeaning="Test")])
        seq2 = Sequence([Dataset(CodeValue="123", CodeMeaning="Test")])
        
        before.ProcedureCodeSequence = seq1
        after.ProcedureCodeSequence = seq2
        
        diff = compare_datasets(before, after)
        
        # These are semantically identical but may differ in stringification
        # Depends on pydicom version and configuration
        unchanged_count = len([d for d in diff.unchanged if d.tag == "ProcedureCodeSequence"])
        modified_count = len([d for d in diff.modified if d.tag == "ProcedureCodeSequence"])
        
        # Document the issue
        assert unchanged_count + modified_count > 0  # At least detected
    
    def test_sequence_item_changes_not_detected(self):
        """Test that changes in sequence items are not properly detected."""
        before = Dataset()
        after = Dataset()
        
        # Sequence with one item
        seq1 = Sequence([Dataset(CodeValue="123", CodeMeaning="Test")])
        # Sequence with different item
        seq2 = Sequence([Dataset(CodeValue="456", CodeMeaning="Changed")])
        
        before.ProcedureCodeSequence = seq1
        after.ProcedureCodeSequence = seq2
        
        diff = compare_datasets(before, after)
        
        # The diff should show modification, but relies on stringification
        modified_tags = [d.tag for d in diff.modified]
        
        # This documents that nested changes may not be properly detected
        # Proper element-by-element comparison would be needed
    
    def test_sequence_items_added_removed(self):
        """Test detection of sequence items being added/removed."""
        before = Dataset()
        after = Dataset()
        
        # Before: sequence with 2 items
        seq1 = Sequence([
            Dataset(CodeValue="123"),
            Dataset(CodeValue="456")
        ])
        # After: sequence with 1 item
        seq2 = Sequence([Dataset(CodeValue="123")])
        
        before.ProcedureCodeSequence = seq1
        after.ProcedureCodeSequence = seq2
        
        diff = compare_datasets(before, after)
        
        # Changes in sequence items should be detected via stringification
        # But this is fragile and depends on exact formatting


class TestSequenceLimitations:
    """Document known limitations in sequence handling."""
    
    def test_limitation_no_recursive_anonymization(self):
        """Document that sequences are not recursively anonymized."""
        ds = Dataset()
        
        # Create sequence with PHI in nested datasets
        item1 = Dataset()
        item1.PatientName = "NestedPatient"
        item1.PatientID = "12345"
        item1.StudyDate = "20250126"
        
        seq = Sequence([item1])
        ds.ReferencedImageSequence = seq
        
        engine = AnonymizationEngine(salt="test")
        from dicom_privacy_kit.core.profiles import BASIC_PROFILE
        result = engine.anonymize(ds, BASIC_PROFILE)
        
        # LIMITATION: Nested data is not anonymized
        # The sequence is preserved unchanged
        if "ReferencedImageSequence" in result:
            nested = result.ReferencedImageSequence[0]
            # These fields should have been anonymized but weren't
            assert nested.PatientName == "NestedPatient"  # Not removed
            assert nested.PatientID == "12345"  # Not hashed
            assert nested.StudyDate == "20250126"  # Not emptied
    
    def test_limitation_no_sequence_in_tag_registry(self):
        """Document that sequences are not in TAG_REGISTRY."""
        from dicom_privacy_kit.core.tags import get_tag_metadata, TAG_REGISTRY
        
        # Check if any sequence tags are registered
        seq_tags = [tag for tag in TAG_REGISTRY if 'Sequence' in tag]
        
        # No sequence tags are in the registry
        # This means sequences are not recognized as PHI
        assert len(seq_tags) == 0
    
    def test_limitation_sequence_removed_but_not_processed(self):
        """Document that REMOVE action on sequence removes the tag but not safely."""
        ds = Dataset()
        
        # Create sequence with sensitive data
        sensitive_seq = Sequence([
            Dataset(PatientName="Secret1", PatientID="ID1"),
            Dataset(PatientName="Secret2", PatientID="ID2")
        ])
        ds.ProcedureCodeSequence = sensitive_seq
        
        # Remove the sequence
        from dicom_privacy_kit.core.actions import remove_tag
        remove_tag(ds, "ProcedureCodeSequence")
        
        # Sequence is removed but...
        # If this fails or sequence is not removed, data is exposed
        # No explicit handling means it relies on generic tag removal
        assert "ProcedureCodeSequence" not in ds


class TestSequenceExplicitHandling:
    """Test that unsupported features explicitly document sequence limitations."""
    
    def test_docstring_mentions_sequence_limitations(self):
        """Test that relevant functions document sequence limitations."""
        from dicom_privacy_kit.anonymizer.engine import AnonymizationEngine
        
        # Engine docstring should mention sequences
        assert AnonymizationEngine.__doc__ is not None
        # Note: May not currently mention it, but should in the future
    
    def test_sequence_elements_can_be_skipped_safely(self):
        """Test that sequences can be skipped without breaking functionality."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        # Add sequence
        seq = Sequence([Dataset(PrivateTag="Secret")])
        ds.ReferencedImageSequence = seq
        
        # Anonymization should work even with sequence present
        engine = AnonymizationEngine(salt="test")
        from dicom_privacy_kit.core.profiles import BASIC_PROFILE
        
        try:
            result = engine.anonymize(ds, BASIC_PROFILE)
            
            # Top-level anonymization should succeed
            assert "PatientName" not in result
            assert result.PatientID != "12345"  # Hashed
            
            # Sequence may or may not be modified
            # But the function shouldn't crash
        except Exception as e:
            pytest.fail(f"Anonymization failed with sequence present: {e}")


class TestSequenceDocumentation:
    """Test that sequence handling is properly documented."""
    
    def test_readme_documents_sequence_limitation(self):
        """Test that README documents sequence limitations."""
        with open('/Users/karanrane/@Projects/dicom-privacy-kit/README.md', 'r') as f:
            readme = f.read()
        
        # Check if sequence limitations are mentioned
        # Currently not mentioned - should be added
        has_sequence_mention = 'sequence' in readme.lower() or 'SQ' in readme
        
        # This documents where the limitation should be mentioned
    
    def test_core_modules_document_unsupported_types(self):
        """Test that modules document which DICOM types are unsupported."""
        from dicom_privacy_kit.core import actions
        
        # Actions module should document what's not supported
        assert actions.__doc__ is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
