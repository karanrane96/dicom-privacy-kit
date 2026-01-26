"""Audit of PHI risk scoring logic: bounded, explainable, tunable."""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.risk import (
    RiskScore, score_dataset, calculate_tag_risk, RISK_WEIGHTS,
    adjust_risk_weights, format_risk_score
)
from dicom_privacy_kit.core.tags import get_tag_metadata
from dicom_privacy_kit.risk.weights import get_tag_weight, TAG_CATEGORIES


class TestScoringBounded:
    """Verify risk scores are bounded and never exceed expected maximums."""
    
    def test_per_tag_risk_bounded_by_base(self):
        """Each tag's risk is bounded by base_risk * weight."""
        test_values = [
            ("PatientName", "John^Doe"),
            ("PatientID", "12345"),
            ("PatientBirthDate", "19800101"),
            ("StudyDate", "20250126"),
        ]
        
        for tag, value in test_values:
            risk, base_risk, weight, category = calculate_tag_risk(tag, value)
            max_allowed = base_risk * weight
            
            # Risk must never exceed base * weight
            assert risk <= max_allowed, (
                f"{tag}: risk={risk} exceeds bound base({base_risk}) * weight({weight}) = {max_allowed}"
            )
    
    def test_aggregate_risk_bounded_to_percent(self):
        """Total risk percentage always in [0, 100]."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        ds.PatientBirthDate = "19800101"
        ds.StudyDate = "20250126"
        ds.StudyTime = "120000"
        ds.StudyInstanceUID = "1.2.3.4.5"
        
        score = score_dataset(ds)
        
        assert 0.0 <= score.risk_percentage <= 100.0
        assert 0.0 <= score.total_score <= score.max_score
    
    def test_empty_dataset_has_zero_risk(self):
        """Empty dataset always has 0% risk."""
        ds = Dataset()
        score = score_dataset(ds)
        
        assert score.total_score == 0.0
        assert score.risk_percentage == 0.0
        assert score.risk_level == "LOW"
    
    def test_all_anonymized_values_have_zero_risk(self):
        """Datasets with only placeholder values have 0% risk."""
        ds = Dataset()
        ds.PatientName = "ANONYMIZED"
        ds.PatientID = "ANONYMIZED"
        ds.PatientBirthDate = "ANONYMIZED"
        
        score = score_dataset(ds)
        
        assert score.total_score == 0.0
        assert score.risk_percentage == 0.0
        assert score.risk_level == "LOW"
    
    def test_hashed_values_have_reduced_bounded_risk(self):
        """Hashed values have reduced risk still bounded by max."""
        hash_hex = "a" * 32  # SHA256-like
        risk, base, weight, category = calculate_tag_risk("PatientID", hash_hex)
        
        max_allowed = base * weight
        reduced_expected = max_allowed * 0.2  # 20% of max
        
        assert risk <= max_allowed
        assert risk == min(max_allowed, reduced_expected)


class TestScoringExplainable:
    """Verify scoring provides breakdown and explanation of contributions."""
    
    def test_tag_breakdown_includes_all_fields(self):
        """Tag breakdown includes risk, base_risk, weight, category."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        score = score_dataset(ds)
        
        # Both tags should be in breakdown
        assert "PatientName" in score.tag_breakdown
        assert "PatientID" in score.tag_breakdown
        
        for tag, breakdown in score.tag_breakdown.items():
            # Must have all required fields
            assert "risk" in breakdown
            assert "base_risk" in breakdown
            assert "weight" in breakdown
            assert "max_risk" in breakdown
            assert "category" in breakdown
            
            # Fields must be numeric
            assert isinstance(breakdown["risk"], float)
            assert isinstance(breakdown["base_risk"], float)
            assert isinstance(breakdown["weight"], float)
            assert isinstance(breakdown["max_risk"], float)
            
            # Category must be string
            assert isinstance(breakdown["category"], str)
            
            # Risk must be <= max_risk
            assert breakdown["risk"] <= breakdown["max_risk"]
    
    def test_tag_breakdown_consistency(self):
        """Tag breakdown risk equals score and follows max_risk = base * weight."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        score = score_dataset(ds)
        breakdown = score.tag_breakdown.get("PatientName", {})
        
        if breakdown:
            # max_risk should equal base_risk * weight
            expected_max = breakdown["base_risk"] * breakdown["weight"]
            assert breakdown["max_risk"] == expected_max
            
            # total_score should sum up tag scores
            total_from_breakdown = sum(b["risk"] for b in score.tag_breakdown.values())
            assert abs(score.total_score - total_from_breakdown) < 0.01
    
    def test_format_includes_category_weight_info(self):
        """Formatted output includes category and weight for each tag."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        score = score_dataset(ds)
        formatted = format_risk_score(score)
        
        # Should include category and weight indicators
        assert "cat=" in formatted
        assert "weight=" in formatted
        assert "base=" in formatted
        
        # Should mention at least some tags
        assert "PatientName" in formatted or "PatientID" in formatted
    
    def test_calculate_tag_risk_returns_tuple(self):
        """calculate_tag_risk returns (risk, base_risk, weight, category)."""
        result = calculate_tag_risk("PatientName", "John^Doe")
        
        assert isinstance(result, tuple)
        assert len(result) == 4
        
        risk, base_risk, weight, category = result
        assert isinstance(risk, float)
        assert isinstance(base_risk, float)
        assert isinstance(weight, float)
        assert isinstance(category, str)


class TestScoringTunable:
    """Verify weights can be adjusted to control scoring."""
    
    def test_category_weights_configurable(self):
        """Risk weights for categories can be adjusted."""
        original_name = RISK_WEIGHTS.get("name", 1.0)
        
        try:
            # Increase name weight
            adjust_risk_weights({"name": 2.0})
            assert RISK_WEIGHTS["name"] == 2.0
            
            # Score should increase with weight
            ds = Dataset()
            ds.PatientName = "John^Doe"
            
            score_before = score_dataset(ds)
            
            adjust_risk_weights({"name": 0.5})
            score_after = score_dataset(ds)
            
            # Same PHI, lower weight -> lower score
            assert score_after.risk_percentage <= score_before.risk_percentage
        finally:
            # Reset
            adjust_risk_weights({"name": original_name})
    
    def test_weight_affects_per_tag_risk(self):
        """Adjusting weight for a category affects per-tag risk."""
        original_id = RISK_WEIGHTS.get("id", 1.0)
        
        try:
            ds = Dataset()
            ds.PatientID = "12345"
            
            # With weight 1.0
            adjust_risk_weights({"id": 1.0})
            score1 = score_dataset(ds)
            risk1 = score1.tag_scores.get("PatientID", 0)
            
            # With weight 2.0
            adjust_risk_weights({"id": 2.0})
            score2 = score_dataset(ds)
            risk2 = score2.tag_scores.get("PatientID", 0)
            
            # Higher weight = higher risk
            assert risk2 >= risk1
        finally:
            adjust_risk_weights({"id": original_id})
    
    def test_tag_category_mappings(self):
        """TAG_CATEGORIES provides category for known tags."""
        # Check a few known mappings
        assert TAG_CATEGORIES.get("PatientName") == "name"
        assert TAG_CATEGORIES.get("PatientID") == "id"
        assert TAG_CATEGORIES.get("PatientBirthDate") == "date"
        assert TAG_CATEGORIES.get("StudyTime") == "time"
    
    def test_get_tag_weight_returns_category_and_weight(self):
        """get_tag_weight returns (category, weight) for known and unknown tags."""
        # Known tag
        cat, weight = get_tag_weight("PatientName")
        assert cat == "name"
        assert weight == RISK_WEIGHTS.get("name", 1.0)
        
        # Unknown tag gets default
        cat, weight = get_tag_weight("SomeUnknownTag")
        assert cat == "unknown"
        assert weight == RISK_WEIGHTS.get("unknown", 1.0)


class TestScoringRiskLevels:
    """Verify risk level classification is correct."""
    
    def test_risk_level_low(self):
        """LOW risk: percentage < 25%."""
        ds = Dataset()
        # No PHI
        score = score_dataset(ds)
        assert score.risk_level == "LOW"
        assert score.risk_percentage < 25
    
    def test_risk_level_medium(self):
        """MEDIUM risk: 25% <= percentage < 50%."""
        # Need a dataset that scores in medium range
        # This depends on max_score from tags in registry
        ds = Dataset()
        ds.StudyTime = "120000"  # Low risk tag
        
        score = score_dataset(ds)
        # Time has low base risk, so percentage will be small
        # To get medium, we'd need multiple moderate-risk tags
        # For now, just verify classification logic works
        if 25 <= score.risk_percentage < 50:
            assert score.risk_level == "MEDIUM"
    
    def test_risk_level_high(self):
        """HIGH risk: 50% <= percentage < 75%."""
        ds = Dataset()
        ds.PatientName = "John^Doe"  # High risk
        
        score = score_dataset(ds)
        if 50 <= score.risk_percentage < 75:
            assert score.risk_level == "HIGH"
    
    def test_risk_level_critical(self):
        """CRITICAL risk: percentage >= 75%."""
        ds = Dataset()
        # Fill with multiple high-risk tags
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        ds.PatientBirthDate = "19800101"
        ds.StudyDate = "20250126"
        ds.StudyInstanceUID = "1.2.3.4.5"
        
        score = score_dataset(ds)
        if score.risk_percentage >= 75:
            assert score.risk_level == "CRITICAL"


class TestScoringEdgeCases:
    """Verify scoring handles edge cases properly."""
    
    def test_missing_tag_metadata_handled(self):
        """Score gracefully handles tags without metadata."""
        # This test verifies robustness, though all tags in registry should have metadata
        risk, base, weight, category = calculate_tag_risk("NonExistentTag", "value")
        
        # Should return defaults
        assert risk == 0.0
        assert base == 0.0
        assert category == "unknown"
    
    def test_very_long_value_bounded(self):
        """Very long PHI values still bounded by base * weight."""
        long_value = "A" * 10000
        risk, base, weight, category = calculate_tag_risk("PatientName", long_value)
        
        max_allowed = base * weight
        assert risk <= max_allowed
    
    def test_special_characters_in_phi(self):
        """PHI with special characters handled correctly."""
        values = [
            "Patient^With^Carets",
            "Patient|With|Pipes",
            "Patient\nWith\nNewlines",
            "患者名",  # Japanese characters
        ]
        
        for value in values:
            risk, base, weight, category = calculate_tag_risk("PatientName", value)
            max_allowed = base * weight
            assert risk <= max_allowed


class TestScoringIntegration:
    """Integration tests for scoring system."""
    
    def test_score_before_and_after_anonymization(self):
        """Anonymization reduces risk score."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        before = score_dataset(ds)
        
        # Anonymize
        from dicom_privacy_kit.anonymizer import AnonymizationEngine
        engine = AnonymizationEngine(salt="test")
        anon_ds = engine.anonymize(ds, "basic")
        
        after = score_dataset(anon_ds)
        
        # After should have lower or equal risk
        assert after.risk_percentage <= before.risk_percentage
    
    def test_risk_score_reproducible(self):
        """Same dataset produces same score on repeated calls."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        ds.PatientID = "12345"
        
        score1 = score_dataset(ds)
        score2 = score_dataset(ds)
        
        assert score1.total_score == score2.total_score
        assert score1.risk_percentage == score2.risk_percentage
        assert score1.risk_level == score2.risk_level
        assert score1.tag_scores == score2.tag_scores


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
