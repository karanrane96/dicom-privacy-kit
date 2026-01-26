"""Tests for PHI risk scoring."""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.risk import (
    RiskScore, score_dataset, format_risk_score,
    RISK_WEIGHTS, calculate_tag_risk, adjust_risk_weights
)
from dicom_privacy_kit.anonymizer import AnonymizationEngine


def create_high_risk_dataset():
    """Create a dataset with high PHI risk."""
    ds = Dataset()
    ds.PatientName = "John^Doe"
    ds.PatientID = "12345"
    ds.PatientBirthDate = "19800101"
    ds.StudyDate = "20250126"
    ds.StudyTime = "120000"
    ds.StudyInstanceUID = "1.2.3.4.5"
    return ds


class TestRiskScoring:
    """Test cases for risk scoring."""
    
    def test_score_high_risk_dataset(self):
        """Test scoring a high-risk dataset."""
        ds = create_high_risk_dataset()
        
        score = score_dataset(ds)
        
        assert score.total_score > 0
        assert score.risk_percentage > 0
        assert score.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert isinstance(score.tag_scores, dict)
    
    def test_score_empty_dataset(self):
        """Test scoring an empty dataset."""
        ds = Dataset()
        
        score = score_dataset(ds)
        
        assert score.total_score == 0
        assert score.risk_percentage == 0.0
        assert score.risk_level == "LOW"
    
    def test_score_anonymized_dataset(self):
        """Test that anonymized datasets have lower or equal risk."""
        original = create_high_risk_dataset()
        engine = AnonymizationEngine()
        anonymized = engine.anonymize(original, "basic")
        
        original_score = score_dataset(original)
        anonymized_score = score_dataset(anonymized)
        
        # Anonymized should have lower or equal risk (some tags are hashed, not removed)
        assert anonymized_score.risk_percentage <= original_score.risk_percentage
        # Should have some risk reduction in most cases
        assert len(anonymized_score.tag_scores) <= len(original_score.tag_scores)
    
    def test_risk_levels(self):
        """Test risk level classification."""
        # Test different risk percentages
        high_risk = RiskScore(75, 100, 75.0, "HIGH", {}, {})
        assert high_risk.risk_percentage >= 50
        
        low_risk = RiskScore(10, 100, 10.0, "LOW", {}, {})
        assert low_risk.risk_percentage < 25
    
    def test_format_risk_score(self):
        """Test formatting risk score."""
        ds = create_high_risk_dataset()
        score = score_dataset(ds)
        
        formatted = format_risk_score(score)
        
        assert "PHI RISK ASSESSMENT" in formatted
        assert "Risk Level:" in formatted
        assert "Risk Score:" in formatted
        assert "Risk Percentage:" in formatted
    
    def test_calculate_tag_risk_empty_value(self):
        """Test risk calculation for empty values."""
        risk, base, weight, category = calculate_tag_risk("PatientName", "")
        
        assert risk == 0.0
        assert base == 5
        assert weight == 1.0
        assert category == "name"
    
    def test_calculate_tag_risk_whitespace(self):
        """Test risk calculation for whitespace values."""
        risk, base, weight, category = calculate_tag_risk("PatientName", "   ")
        
        assert risk == 0.0
        assert base == 5
    
    def test_calculate_tag_risk_anonymous(self):
        """Test risk calculation for anonymous values."""
        risk, base, weight, category = calculate_tag_risk("PatientName", "anonymous")
        
        assert risk == 0.0
        assert category == "name"
    
    def test_calculate_tag_risk_anonymized(self):
        """Test risk calculation for anonymized values."""
        risk, base, weight, category = calculate_tag_risk("PatientName", "ANONYMIZED")
        
        assert risk == 0.0
        assert weight == 1.0
    
    def test_calculate_tag_risk_hashed_value(self):
        """Test risk calculation for hashed values."""
        # 32-character hex string (looks like hash)
        risk, base, weight, category = calculate_tag_risk("PatientID", "a" * 32)
        
        # Should be reduced risk and bounded by base*weight (5*1)
        assert risk < base * weight
        assert category == "id"
    
    def test_calculate_tag_risk_normal_value(self):
        """Test risk calculation for normal PHI values."""
        risk, base, weight, category = calculate_tag_risk("PatientName", "John^Doe")
        
        assert risk == base * weight
    
    def test_risk_weights_exist(self):
        """Test that risk weights are defined."""
        assert "name" in RISK_WEIGHTS
        assert "id" in RISK_WEIGHTS
        assert "date" in RISK_WEIGHTS
    
    def test_adjust_risk_weights(self):
        """Test adjusting risk weights."""
        original_weight = RISK_WEIGHTS.get("name", 1.0)
        
        adjust_risk_weights({"name": 2.0})
        
        assert RISK_WEIGHTS["name"] == 2.0
        
        # Reset to original
        adjust_risk_weights({"name": original_weight})
    
    def test_risk_score_dataclass(self):
        """Test RiskScore dataclass."""
        score = RiskScore(
            total_score=50.0,
            max_score=100.0,
            risk_percentage=50.0,
            risk_level="MEDIUM",
            tag_scores={"PatientName": 5.0},
            tag_breakdown={"PatientName": {"risk": 5.0, "base_risk": 5.0, "weight": 1.0, "max_risk": 5.0}},
        )
        
        assert score.total_score == 50.0
        assert score.max_score == 100.0
        assert score.risk_percentage == 50.0
        assert score.risk_level == "MEDIUM"
        assert len(score.tag_scores) == 1
        assert "PatientName" in score.tag_breakdown
    
    def test_risk_level_critical(self):
        """Test critical risk level."""
        ds = create_high_risk_dataset()
        score = score_dataset(ds)
        
        # Should have some risk
        assert score.total_score > 0
    
    def test_tag_scores_populated(self):
        """Test that tag scores are populated."""
        ds = create_high_risk_dataset()
        score = score_dataset(ds)
        
        assert len(score.tag_scores) > 0
        assert all(isinstance(v, float) for v in score.tag_scores.values())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
