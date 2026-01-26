#!/usr/bin/env python3
"""Example: PHI Risk Scoring - Bounded, Explainable, Tunable"""

from pydicom import Dataset
from dicom_privacy_kit.risk import (
    score_dataset, format_risk_score, 
    adjust_risk_weights, RISK_WEIGHTS
)

def example_default_weights():
    """Example 1: Scoring with default weights"""
    print("=" * 70)
    print("EXAMPLE 1: SCORING WITH DEFAULT WEIGHTS")
    print("=" * 70)
    
    # Create high-risk dataset
    ds = Dataset()
    ds.PatientName = "John^Doe"
    ds.PatientID = "12345"
    
    # Score with default weights
    score = score_dataset(ds)
    print(f"\nDefault Risk Weights: {dict(RISK_WEIGHTS)}")
    print(f"\nRisk Percentage: {score.risk_percentage:.1f}%")
    print(f"Risk Level: {score.risk_level}")
    print(f"\nDetailed Breakdown:")
    for tag, breakdown in score.tag_breakdown.items():
        print(f"  {tag}:")
        print(f"    Category: {breakdown['category']}")
        print(f"    Base Risk: {breakdown['base_risk']:.1f}")
        print(f"    Weight: {breakdown['weight']:.2f}")
        print(f"    Score: {breakdown['risk']:.1f} / {breakdown['max_risk']:.1f}")


def example_tuned_weights():
    """Example 2: Adjusting weights for organizational policy"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: TUNING WEIGHTS FOR STRICTER POLICY")
    print("=" * 70)
    
    ds = Dataset()
    ds.PatientName = "John^Doe"
    ds.PatientID = "12345"
    
    # Score with default
    score_default = score_dataset(ds)
    print(f"\nDefault (name=1.0, id=1.0):")
    print(f"  Risk: {score_default.risk_percentage:.1f}% ({score_default.risk_level})")
    
    # Adjust to more conservative policy
    print(f"\nAdjusting weights for stricter policy...")
    adjust_risk_weights({"name": 2.0, "id": 2.0})
    
    # Score with adjusted
    score_adjusted = score_dataset(ds)
    print(f"\nAdjusted (name=2.0, id=2.0):")
    print(f"  Risk: {score_adjusted.risk_percentage:.1f}% ({score_adjusted.risk_level})")
    
    print(f"\nImpact: {score_adjusted.risk_percentage - score_default.risk_percentage:+.1f} percentage points")
    
    # Reset
    adjust_risk_weights({"name": 1.0, "id": 1.0})


def example_anonymized():
    """Example 3: Risk reduction from anonymization"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: RISK REDUCTION FROM ANONYMIZATION")
    print("=" * 70)
    
    # Original dataset
    original = Dataset()
    original.PatientName = "John^Doe"
    original.PatientID = "12345"
    original.PatientBirthDate = "19800101"
    
    # Score original
    score_before = score_dataset(original)
    print(f"\nBefore Anonymization:")
    print(f"  Risk: {score_before.risk_percentage:.1f}% ({score_before.risk_level})")
    print(f"  Tags with PHI: {len(score_before.tag_scores)}")
    
    # Anonymized (e.g., via AnonymizationEngine)
    anonymized = Dataset()
    anonymized.PatientName = ""  # Cleared
    anonymized.PatientID = "a1b2c3d4e5f6"  # Hashed
    anonymized.PatientBirthDate = ""  # Cleared
    
    score_after = score_dataset(anonymized)
    print(f"\nAfter Anonymization:")
    print(f"  Risk: {score_after.risk_percentage:.1f}% ({score_after.risk_level})")
    print(f"  Tags with PHI: {len(score_after.tag_scores)}")
    
    reduction = score_before.risk_percentage - score_after.risk_percentage
    print(f"\nRisk Reduction: {reduction:.1f} percentage points")


def example_understanding_bounds():
    """Example 4: Understanding bounded scoring"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: UNDERSTANDING BOUNDED SCORING")
    print("=" * 70)
    
    from dicom_privacy_kit.risk import calculate_tag_risk
    
    print("\nExample: PatientName with different values")
    print("  Base risk: 5.0")
    print("  Category weight: 1.0 (name)")
    print("  Max possible: 5.0 × 1.0 = 5.0")
    
    test_values = [
        ("John^Doe", "Normal PHI"),
        ("", "Empty value"),
        ("ANONYMIZED", "Placeholder"),
        ("a" * 32, "Looks hashed (32 hex chars)"),
    ]
    
    print("\nScoring different values:")
    for value, description in test_values:
        risk, base, weight, category = calculate_tag_risk("PatientName", value)
        print(f"  {description:<30} → Risk: {risk:.1f} (bounded ≤ 5.0)")


if __name__ == "__main__":
    example_default_weights()
    example_tuned_weights()
    example_anonymized()
    example_understanding_bounds()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
✓ Bounded: Risk percentage always ∈ [0, 100]
✓ Explainable: Full breakdown of category, base risk, weight, contribution
✓ Tunable: adjust_risk_weights() changes scoring without code changes
    """)
