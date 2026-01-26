"""Tests for basic anonymization profile."""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.anonymizer import AnonymizationEngine
from dicom_privacy_kit.core.profiles import BASIC_PROFILE
from dicom_privacy_kit.risk import score_dataset


def create_sample_dataset():
    """Create a sample DICOM dataset with PHI."""
    ds = Dataset()
    ds.PatientName = "John^Doe"
    ds.PatientID = "12345"
    ds.PatientBirthDate = "19800101"
    ds.PatientSex = "M"
    ds.StudyDate = "20250126"
    ds.StudyTime = "120000"
    ds.StudyInstanceUID = "1.2.3.4.5.6.7.8.9"
    ds.SeriesInstanceUID = "1.2.3.4.5.6.7.8.10"
    return ds


class TestBasicProfile:
    """Test cases for basic anonymization profile."""
    
    def test_anonymization_removes_patient_name(self):
        """Test that patient name is removed."""
        dataset = create_sample_dataset()
        engine = AnonymizationEngine()
        
        anonymized = engine.anonymize(dataset, BASIC_PROFILE)
        
        assert not hasattr(anonymized, 'PatientName')
    
    def test_anonymization_hashes_patient_id(self):
        """Test that patient ID is hashed."""
        dataset = create_sample_dataset()
        engine = AnonymizationEngine(salt="test")
        
        original_id = dataset.PatientID
        anonymized = engine.anonymize(dataset, BASIC_PROFILE)
        
        assert hasattr(anonymized, 'PatientID')
        assert anonymized.PatientID != original_id
        assert len(anonymized.PatientID) == 16  # Truncated hash
    
    def test_anonymization_keeps_patient_sex(self):
        """Test that patient sex is kept."""
        dataset = create_sample_dataset()
        engine = AnonymizationEngine()
        
        original_sex = dataset.PatientSex
        anonymized = engine.anonymize(dataset, BASIC_PROFILE)
        
        assert anonymized.PatientSex == original_sex
    
    def test_anonymization_empties_dates(self):
        """Test that study date is emptied."""
        dataset = create_sample_dataset()
        engine = AnonymizationEngine()
        
        anonymized = engine.anonymize(dataset, BASIC_PROFILE)
        
        assert hasattr(anonymized, 'StudyDate')
        assert anonymized.StudyDate == ""
    
    def test_risk_reduction_after_anonymization(self):
        """Test that risk score is reduced after anonymization."""
        dataset = create_sample_dataset()
        engine = AnonymizationEngine()
        
        before_score = score_dataset(dataset)
        anonymized = engine.anonymize(dataset, BASIC_PROFILE)
        after_score = score_dataset(anonymized)
        
        assert after_score.risk_percentage < before_score.risk_percentage
        assert after_score.total_score < before_score.total_score
    
    def test_in_place_anonymization(self):
        """Test in-place modification."""
        dataset = create_sample_dataset()
        engine = AnonymizationEngine()
        
        original_id = id(dataset)
        engine.anonymize(dataset, BASIC_PROFILE, in_place=True)
        
        assert id(dataset) == original_id
        assert not hasattr(dataset, 'PatientName')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
