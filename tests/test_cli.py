"""Tests for CLI commands - exit codes, reporting, and error handling."""

import subprocess
import tempfile
from pathlib import Path
import pytest
from pydicom import Dataset, dcmread, dcmwrite
from pydicom.dataelem import DataElement
from pydicom.uid import ExplicitVRLittleEndian


def create_test_dicom(path: Path, with_phi: bool = False):
    """Create a test DICOM file."""
    ds = Dataset()
    ds.file_meta = Dataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    
    # Required DICOM elements
    ds.PatientName = "Test^Patient" if with_phi else "ANON"
    ds.PatientID = "12345" if with_phi else "ANON"
    ds.Modality = "CT"
    ds.StudyInstanceUID = "1.2.3"
    ds.SeriesInstanceUID = "1.2.3.4"
    ds.SOPInstanceUID = "1.2.3.4.5"
    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    
    if with_phi:
        ds.PatientAge = "042Y"
        ds.PatientBirthDate = "19800101"
    
    dcmwrite(str(path), ds, write_like_original=False)
    return ds


class TestAnonymizeCommand:
    """Tests for anonymize CLI command."""
    
    def test_anonymize_success(self):
        """Test successful anonymization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            output_file = tmpdir / "output.dcm"
            
            create_test_dicom(input_file, with_phi=True)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'anonymize', 
                 str(input_file), '-o', str(output_file)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert output_file.exists()
            assert b"SUCCESS" in result.stdout.encode()
    
    def test_anonymize_missing_input(self):
        """Test error on missing input file."""
        result = subprocess.run(
            ['python', '-m', 'dicom_privacy_kit.cli', 'anonymize', 
             '/nonexistent/file.dcm'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1
        assert "ERROR" in result.stderr
        assert "not found" in result.stderr
    
    def test_anonymize_with_report(self):
        """Test anonymization with compliance report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            output_file = tmpdir / "output.dcm"
            
            create_test_dicom(input_file, with_phi=True)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'anonymize', 
                 str(input_file), '-o', str(output_file), '-r'],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "COMPLIANCE REPORT" in result.stdout
            assert "Total PHI tags" in result.stdout
    
    def test_anonymize_verbose(self):
        """Test anonymization with verbose output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            output_file = tmpdir / "output.dcm"
            
            create_test_dicom(input_file, with_phi=True)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'anonymize', 
                 str(input_file), '-o', str(output_file), '-v'],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "Anonymization Log" in result.stdout


class TestDiffCommand:
    """Tests for diff CLI command."""
    
    def test_diff_identical_files(self):
        """Test diff with identical files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            file1 = tmpdir / "file1.dcm"
            file2 = tmpdir / "file2.dcm"
            
            create_test_dicom(file1)
            create_test_dicom(file2)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'diff',
                 str(file1), str(file2)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "COMPARISON RESULTS" in result.stdout
            assert "Removed:  0 tags" in result.stdout
    
    def test_diff_missing_before_file(self):
        """Test error on missing before file."""
        result = subprocess.run(
            ['python', '-m', 'dicom_privacy_kit.cli', 'diff',
             '/nonexistent/before.dcm', '/nonexistent/after.dcm'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1
        assert "ERROR" in result.stderr
        assert "not found" in result.stderr
    
    def test_diff_modified_files(self):
        """Test diff with modified files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            before_file = tmpdir / "before.dcm"
            after_file = tmpdir / "after.dcm"
            
            # Create before file
            ds_before = create_test_dicom(before_file, with_phi=True)
            
            # Create after file with some changes
            ds_after = dcmread(str(before_file))
            ds_after.PatientName = "Anonymous"
            dcmwrite(str(after_file), ds_after, write_like_original=False)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'diff',
                 str(before_file), str(after_file)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "COMPARISON RESULTS" in result.stdout
            assert "Modified:" in result.stdout
    
    def test_diff_fail_on_changes(self):
        """Test fail-on-changes flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            before_file = tmpdir / "before.dcm"
            after_file = tmpdir / "after.dcm"
            
            # Create before file
            ds_before = create_test_dicom(before_file, with_phi=True)
            
            # Create modified after file
            ds_after = dcmread(str(before_file))
            ds_after.PatientName = "Anonymous"
            dcmwrite(str(after_file), ds_after, write_like_original=False)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'diff',
                 str(before_file), str(after_file), '--fail-on-changes'],
                capture_output=True,
                text=True
            )
            
            # Should fail because there are changes
            assert result.returncode == 1
            assert "ERROR" in result.stderr


class TestScoreCommand:
    """Tests for score CLI command."""
    
    def test_score_low_risk(self):
        """Test scoring on file with low PHI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            
            # Create file with minimal PHI
            create_test_dicom(input_file, with_phi=False)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'score',
                 str(input_file)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "RISK ASSESSMENT" in result.stdout
            assert "SUCCESS" in result.stdout
    
    def test_score_high_phi_content(self):
        """Test scoring on file with high PHI content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            
            create_test_dicom(input_file, with_phi=True)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'score',
                 str(input_file)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "RISK ASSESSMENT" in result.stdout
            assert "SUCCESS" in result.stdout
    
    def test_score_missing_file(self):
        """Test error on missing file."""
        result = subprocess.run(
            ['python', '-m', 'dicom_privacy_kit.cli', 'score',
             '/nonexistent/file.dcm'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1
        assert "ERROR" in result.stderr
        assert "not found" in result.stderr
    
    def test_score_fail_on_risk_threshold(self):
        """Test fail-on-risk threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            
            create_test_dicom(input_file, with_phi=True)
            
            # Set very low threshold - should always exceed it
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'score',
                 str(input_file), '--fail-on-risk', '0'],
                capture_output=True,
                text=True
            )
            
            # Should fail because threshold is 0%
            assert result.returncode == 1
            assert "ERROR" in result.stderr
            assert "Risk threshold exceeded" in result.stderr
    
    def test_score_pass_risk_threshold(self):
        """Test passing risk threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            
            create_test_dicom(input_file, with_phi=True)
            
            # Set very high threshold - should not exceed it
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'score',
                 str(input_file), '--fail-on-risk', '99'],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "SUCCESS" in result.stdout


class TestCLIMainEntry:
    """Tests for main CLI entry point."""
    
    def test_help_command(self):
        """Test help output."""
        result = subprocess.run(
            ['python', '-m', 'dicom_privacy_kit.cli', '-h'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "anonymize" in result.stdout
        assert "score" in result.stdout
        assert "diff" in result.stdout
    
    def test_debug_flag(self):
        """Test debug flag enables debug logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            output_file = tmpdir / "output.dcm"
            
            create_test_dicom(input_file, with_phi=True)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', '--debug',
                 'anonymize', str(input_file), '-o', str(output_file)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert output_file.exists()
    
    def test_invalid_dicom_file(self):
        """Test error handling for invalid DICOM files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            invalid_file = tmpdir / "invalid.dcm"
            output_file = tmpdir / "output.dcm"
            
            # Create an invalid DICOM file (just text)
            invalid_file.write_text("This is not a DICOM file")
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'anonymize',
                 str(invalid_file), '-o', str(output_file)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 1
            assert "ERROR" in result.stderr


class TestExitCodes:
    """Tests for proper exit code handling."""
    
    def test_success_exit_code_0(self):
        """Verify successful operations exit with 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.dcm"
            output_file = tmpdir / "output.dcm"
            
            create_test_dicom(input_file)
            
            result = subprocess.run(
                ['python', '-m', 'dicom_privacy_kit.cli', 'anonymize',
                 str(input_file), '-o', str(output_file)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
    
    def test_failure_exit_code_1(self):
        """Verify failed operations exit with 1."""
        result = subprocess.run(
            ['python', '-m', 'dicom_privacy_kit.cli', 'anonymize',
             '/nonexistent/file.dcm'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1
    
    def test_no_command_exit_code_0(self):
        """Verify showing help exits with 0."""
        result = subprocess.run(
            ['python', '-m', 'dicom_privacy_kit.cli'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
