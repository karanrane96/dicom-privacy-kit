# Changelog

All notable changes to DICOM Privacy Kit are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CLI robustness enhancements with proper exit codes
- Input file validation for all CLI commands
- Progress reporting and structured output
- `--debug` flag for troubleshooting
- `--fail-on-risk` threshold checking for score command
- `--fail-on-changes` option for diff command
- `--ignore-remaining` option for anonymize command
- Comprehensive CLI test suite (19 tests)
- `.gitignore`, `.editorconfig`, and pre-commit configuration
- CONTRIBUTING.md guide for developers
- GitHub Actions workflow for automated testing

### Fixed
- Dataset diff tag iteration using proper keyword extraction
- RawDataElement handling in diff operations
- Exception logging throughout core modules
- Silent exception handlers replaced with explicit logging

## [0.3.0] - 2026-01-27

### Added
- PHI risk scoring audit with bounded, explainable, tunable weights
- Risk level classification (low, medium, high, critical)
- Per-tag risk breakdown and scoring explanation
- Risk assessment tests (22 new tests)

### Fixed
- Silent exception handlers in core modules
- Error logging with appropriate levels (debug/warning)

## [0.2.0] - 2026-01-15

### Added
- Sequence handling audit and documentation
- Explicit handling of DICOM sequences (skipped in anonymization)
- Sequence comparison tests (19 new tests)
- Clarified tag state semantics (MISSING, EMPTY, PRESENT)

### Fixed
- Sequence processing edge cases
- Tag state tracking in diff operations

## [0.1.0] - 2026-01-10

### Added
- Initial DICOM anonymization engine
- Multiple anonymization profiles (basic, strict, custom)
- Risk assessment framework
- Dataset comparison utilities
- CLI interface with anonymize, score, and diff commands
- Comprehensive test suite (88 tests)
- Documentation and examples

### Features
- Tag-based anonymization actions (REMOVE, HASH, REPLACE, EMPTY)
- DICOM element normalization
- Compliance reporting
- Hash-based PHI protection
- Python 3.10+ support

[Unreleased]: https://github.com/yourusername/dicom-privacy-kit/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/yourusername/dicom-privacy-kit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/dicom-privacy-kit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/dicom-privacy-kit/releases/tag/v0.1.0
