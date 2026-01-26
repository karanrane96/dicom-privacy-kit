# DICOM Privacy Kit

A Python toolkit for anonymizing and assessing PHI risk in DICOM medical imaging files, with support for PS3.15-inspired anonymization profiles.

## Features

- 🔒 **Anonymization**: Apply customizable profiles inspired by PS3.15 to remove/hash PHI
- 📊 **Risk Scoring**: Assess remaining PHI risk in datasets
- 🔍 **Dataset Diff**: Compare before/after anonymization
- ⚙️ **Configurable**: Custom profiles, cryptographic hashing with explicit salt, adjustable risk weights
- 🧪 **Tested**: Comprehensive test coverage

## Installation

```bash
pip install -e .
```

## Quick Start

### Anonymize a DICOM file

```python
from pydicom import dcmread
from dicom_privacy_kit.anonymizer import AnonymizationEngine

# Load DICOM
dataset = dcmread("patient_scan.dcm")

# Anonymize with basic profile
engine = AnonymizationEngine(salt="my-secret")
anonymized = engine.anonymize(dataset, "basic")

# Save
anonymized.save_as("patient_scan_anon.dcm")
```

### Score PHI risk

```python
from dicom_privacy_kit.risk import score_dataset, format_risk_score

score = score_dataset(dataset)
print(format_risk_score(score))
```

### Compare datasets

```python
from dicom_privacy_kit.diff import compare_datasets, format_diff

diff = compare_datasets(original, anonymized)
print(format_diff(diff))
```

## CLI Usage

```bash
# Anonymize
dicom-privacy-kit anonymize input.dcm -o output.dcm --profile basic --report

# Score risk
dicom-privacy-kit score input.dcm --fail-on-risk 50

# Compare files
dicom-privacy-kit diff original.dcm anonymized.dcm
```

## Project Structure

```
dicom_privacy_kit/
├── core/          # Tag registry, actions, profiles
├── anonymizer/    # Anonymization engine
├── risk/          # PHI risk scoring
├── diff/          # Dataset comparison
└── cli/           # Command-line interface
```

## Anonymization Profiles

### Basic Profile (PS3.15 Partial Implementation)

**IMPORTANT**: This is a PARTIAL implementation of the PS3.15 Basic Confidentiality Profile.

The Basic Profile includes the most common PHI tags but does not cover the full ~80 tags defined in PS3.15 Table X.1-1. For full compliance, a complete rule set is needed.

Actions:
- **Removes**: Patient Name, Birth Date
- **Hashes**: Patient ID, Study/Series UIDs (with cryptographic hash + salt)
- **Empties**: Study Date, Study Time
- **Keeps**: Patient Sex (non-identifying)

**Limitations**:
- Does not remove all DICOM tags that may contain identifiable information
- Does not handle all date/time fields
- Does not process text descriptors or comments
- Does not handle private creator blocks or manufacturer-specific tags

For production use, consider extending with `CLEAN_DESCRIPTORS_PROFILE` or creating a comprehensive rule set covering all tags in PS3.15 Table X.1-1.

### Custom & Extended Profiles

```python
from dicom_privacy_kit.core import ProfileRule, Action

custom_profile = [
    ProfileRule("(0010,0010)", Action.HASH),  # Hash name instead
    ProfileRule("(0008,1030)", Action.REMOVE),  # Remove study description
]

anonymized = engine.anonymize(dataset, custom_profile)
```

## Risk Scoring

Risk scores range from 0-100%:
- **0-25%**: LOW risk
- **25-50%**: MEDIUM risk
- **50-75%**: HIGH risk
- **75-100%**: CRITICAL risk

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=dicom_privacy_kit tests/
```

## Dependencies

- `pydicom>=2.3.0` - DICOM file handling
- `pytest>=7.0.0` - Testing (dev)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or PR.

## References

- [DICOM PS3.15](https://dicom.nema.org/medical/dicom/current/output/html/part15.html) - Security and System Management Profiles
- [HIPAA Guidelines](https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html)
