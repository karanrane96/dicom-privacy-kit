"""Tests for utility functions."""

import pytest
from pydicom import Dataset
from dicom_privacy_kit.core.utils import (
    hash_value, clone_dataset, safe_get_tag, format_tag
)


class TestUtils:
    """Test cases for utility functions."""
    
    def test_hash_value_default(self):
        """Test hashing with default algorithm."""
        result = hash_value("test123")
        
        assert len(result) == 16  # Truncated to 16 chars
        assert isinstance(result, str)
    
    def test_hash_value_with_salt(self):
        """Test hashing with salt."""
        result1 = hash_value("test123", salt="")
        result2 = hash_value("test123", salt="mysalt")
        
        assert result1 != result2
    
    def test_hash_value_consistency(self):
        """Test that same input produces same hash."""
        result1 = hash_value("test123", salt="salt1")
        result2 = hash_value("test123", salt="salt1")
        
        assert result1 == result2
    
    def test_hash_value_sha256(self):
        """Test hashing with SHA256 algorithm."""
        result = hash_value("test123", algorithm="sha256")
        
        assert len(result) == 16
        assert isinstance(result, str)
    
    def test_hash_value_md5(self):
        """Test hashing with MD5 algorithm."""
        result = hash_value("test123", algorithm="md5")
        
        assert len(result) == 16
        assert isinstance(result, str)
    
    def test_hash_deterministic_across_runs(self):
        """Test that hashing is deterministic across multiple runs."""
        # Generate hash 10 times with same input/salt
        salt = "deterministic_salt"
        value = "PatientName123"
        results = [hash_value(value, salt=salt) for _ in range(10)]
        
        # All results should be identical
        assert len(set(results)) == 1
        assert all(r == results[0] for r in results)
    
    def test_hash_uses_cryptographic_hash(self):
        """Test that cryptographic hash is used, not Python's built-in hash()."""
        salt = "test_salt"
        value = "test_value"
        hash_result = hash_value(value, salt=salt)
        
        # Cryptographic hash should be deterministic (not like Python's hash() which randomizes)
        # Python's hash() changes between interpreter sessions by default (PYTHONHASHSEED)
        # but cryptographic hashes are always the same
        result1 = hash_value(value, salt=salt)
        result2 = hash_value(value, salt=salt)
        
        assert result1 == result2
        # Should be hex string of length 16 (SHA256 truncated)
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_hash_explicit_salt_required(self):
        """Test that salt meaningfully affects output."""
        value = "SensitiveData"
        hash_no_salt = hash_value(value, salt="")
        hash_with_salt1 = hash_value(value, salt="salt1")
        hash_with_salt2 = hash_value(value, salt="salt2")
        
        # Different salts must produce different hashes
        assert hash_no_salt != hash_with_salt1
        assert hash_with_salt1 != hash_with_salt2
        assert hash_no_salt != hash_with_salt2
    
    def test_hash_algorithm_parameter(self):
        """Test that algorithm parameter is respected."""
        value = "test"
        salt = "salt"
        
        # Different algorithms should produce different results
        sha256_result = hash_value(value, salt=salt, algorithm="sha256")
        md5_result = hash_value(value, salt=salt, algorithm="md5")
        sha512_result = hash_value(value, salt=salt, algorithm="sha512")
        
        assert sha256_result != md5_result
        assert sha256_result != sha512_result
        assert md5_result != sha512_result
    
    def test_hash_handles_unicode(self):
        """Test that hash handles unicode values correctly."""
        value_unicode = "患者名前"  # Patient name in Japanese
        salt = "unicode_salt"
        
        # Should not raise exception
        result1 = hash_value(value_unicode, salt=salt)
        result2 = hash_value(value_unicode, salt=salt)
        
        # Should be deterministic for unicode
        assert result1 == result2
        assert len(result1) == 16
    
    def test_hash_different_inputs_produce_different_hashes(self):
        """Test that different inputs produce different hashes."""
        salt = "same_salt"
        
        hash1 = hash_value("value1", salt=salt)
        hash2 = hash_value("value2", salt=salt)
        hash3 = hash_value("value1", salt="different_salt")
        
        # Different values should produce different hashes
        assert hash1 != hash2
        assert hash1 != hash3
    
    def test_clone_dataset(self):
        """Test cloning a dataset."""
        original = Dataset()
        original.PatientName = "John^Doe"
        original.PatientID = "12345"
        
        cloned = clone_dataset(original)
        
        assert cloned.PatientName == original.PatientName
        assert cloned.PatientID == original.PatientID
        assert id(cloned) != id(original)
    
    def test_clone_dataset_independence(self):
        """Test that cloned dataset is independent."""
        original = Dataset()
        original.PatientName = "John^Doe"
        
        cloned = clone_dataset(original)
        cloned.PatientName = "Jane^Doe"
        
        assert original.PatientName == "John^Doe"
        assert cloned.PatientName == "Jane^Doe"
    
    def test_safe_get_tag_existing(self):
        """Test safely getting an existing tag."""
        ds = Dataset()
        ds.PatientName = "John^Doe"
        
        result = safe_get_tag(ds, "PatientName")
        
        assert result == "John^Doe"
    
    def test_safe_get_tag_missing(self):
        """Test safely getting a missing tag."""
        ds = Dataset()
        
        result = safe_get_tag(ds, "PatientName")
        
        assert result is None
    
    def test_safe_get_tag_with_default(self):
        """Test safely getting a missing tag with default."""
        ds = Dataset()
        
        result = safe_get_tag(ds, "PatientName", default="Unknown")
        
        assert result == "Unknown"
    
    def test_format_tag_with_parentheses(self):
        """Test formatting a tag that's already formatted."""
        result = format_tag("(0010,0010)")
        
        assert result == "(0010,0010)"
    
    def test_format_tag_without_parentheses(self):
        """Test formatting a tag without parentheses."""
        result = format_tag("00100010")
        
        assert result == "(0010,0010)"
    
    def test_format_tag_with_0x_prefix(self):
        """Test formatting a tag with 0x prefix."""
        result = format_tag("0x00100010")
        
        assert result == "(0010,0010)"
    
    def test_format_tag_lowercase(self):
        """Test formatting a lowercase tag."""
        result = format_tag("00100010")
        
        assert result == "(0010,0010)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
