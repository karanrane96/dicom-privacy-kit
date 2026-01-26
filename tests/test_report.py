"""Tests for compliance reporting."""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.anonymizer.report import (
    ComplianceReport, generate_compliance_report, format_report
)
from dicom_privacy_kit.anonymizer import AnonymizationEngine


def create_phi_dataset():
    """Create a dataset with PHI."""
    ds = Dataset()
    ds.PatientName = "John^Doe"
    ds.PatientID = "12345"
    ds.PatientBirthDate = "19800101"
    ds.PatientSex = "M"
    ds.StudyDate = "20250126"
    ds.StudyInstanceUID = "1.2.3.4.5"
    return ds


class TestComplianceReport:
    """Test cases for compliance reporting."""
    
    def test_generate_report_fully_anonymized(self):
        """Test report for fully anonymized dataset."""
        original = create_phi_dataset()
        engine = AnonymizationEngine()
        anonymized = engine.anonymize(original, "basic")
        
        report = generate_compliance_report(original, anonymized)
        
        assert report.total_phi_tags > 0
        assert report.compliance_percentage > 0
        assert isinstance(report, ComplianceReport)
    
    def test_generate_report_unchanged(self):
        """Test report when dataset is unchanged."""
        original = create_phi_dataset()
        unchanged = original.copy()
        
        report = generate_compliance_report(original, unchanged)
        
        assert report.removed_phi_tags == 0
        assert report.compliance_percentage == 0.0
        assert len(report.remaining_tags) == report.total_phi_tags
    
    def test_generate_report_empty_dataset(self):
        """Test report with empty dataset."""
        original = Dataset()
        anonymized = Dataset()
        
        report = generate_compliance_report(original, anonymized)
        
        assert report.total_phi_tags == 0
        assert report.compliance_percentage == 100.0
    
    def test_generate_report_partial_anonymization(self):
        """Test report with partial anonymization."""
        from copy import deepcopy
        original = create_phi_dataset()
        partial = deepcopy(original)
        # Remove PatientName
        del partial["PatientName"]
        # Modify PatientID to simulate hashing
        partial.PatientID = "hashed_12345"
        
        report = generate_compliance_report(original, partial)
        
        # Should have some changes
        assert report.removed_phi_tags > 0 or report.remaining_phi_tags < report.total_phi_tags
        assert report.total_phi_tags > 0
    
    def test_format_report_structure(self):
        """Test that formatted report has correct structure."""
        original = create_phi_dataset()
        engine = AnonymizationEngine()
        anonymized = engine.anonymize(original, "basic")
        
        report = generate_compliance_report(original, anonymized)
        formatted = format_report(report)
        
        assert "COMPLIANCE REPORT" in formatted
        assert "Total PHI Tags:" in formatted
        assert "Compliance:" in formatted
        assert "%" in formatted
    
    def test_format_report_with_remaining_tags(self):
        """Test formatted report shows remaining tags."""
        original = create_phi_dataset()
        unchanged = original.copy()
        
        report = generate_compliance_report(original, unchanged)
        formatted = format_report(report)
        
        assert "Remaining PHI Tags:" in formatted
    
    def test_format_report_no_remaining_tags(self):
        """Test formatted report when no tags remain."""
        original = create_phi_dataset()
        anonymized = Dataset()  # Empty dataset
        
        report = generate_compliance_report(original, anonymized)
        formatted = format_report(report)
        
        assert isinstance(formatted, str)
        assert "100.0%" in formatted
    
    def test_compliance_report_fields(self):
        """Test ComplianceReport has all required fields."""
        report = ComplianceReport(
            total_phi_tags=10,
            removed_phi_tags=8,
            remaining_phi_tags=2,
            compliance_percentage=80.0,
            remaining_tags=["Tag1", "Tag2"]
        )
        
        assert report.total_phi_tags == 10
        assert report.removed_phi_tags == 8
        assert report.remaining_phi_tags == 2
        assert report.compliance_percentage == 80.0
        assert len(report.remaining_tags) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
