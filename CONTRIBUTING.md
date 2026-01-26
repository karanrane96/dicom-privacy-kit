# CONTRIBUTING.md

## Contributing to DICOM Privacy Kit

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### 1. Set Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/dicom-privacy-kit.git
cd dicom-privacy-kit

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install in development mode with dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Development Guidelines

### Code Style

We use:
- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **Ruff** for linting
- **EditorConfig** for consistent editor settings

Auto-format code before committing:
```bash
black dicom_privacy_kit tests
isort dicom_privacy_kit tests
ruff check --fix dicom_privacy_kit tests
```

### Testing

All code must have tests:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_anonymizer.py -v

# Run with coverage
pytest tests/ --cov=dicom_privacy_kit --cov-report=html
```

Requirements:
- Minimum 80% code coverage
- All edge cases tested
- Error handling verified
- Exit codes validated for CLI commands

### Commit Messages

Use clear, descriptive commit messages:
```
feat: Add batch processing support to CLI

- Add --batch flag to process multiple files
- Process files sequentially with progress reporting
- Aggregate results across files
- Closes #42
```

Format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Test additions
- `refactor:` Code structure changes
- `perf:` Performance improvements
- `chore:` Maintenance tasks

### Documentation

- Update README.md for user-facing changes
- Add docstrings to all functions
- Document parameters and return values
- Include examples for complex features
- Update CHANGELOG.md

## Pull Request Process

1. **Fork & Create Branch**: Create a feature branch from `develop`

2. **Make Changes**: 
   - Write code following guidelines
   - Add/update tests
   - Update documentation

3. **Pre-Commit Checks**:
   ```bash
   pre-commit run --all-files
   ```

4. **Local Testing**:
   ```bash
   pytest tests/ -v --cov=dicom_privacy_kit
   ```

5. **Push & Create PR**:
   ```bash
   git push origin feature/your-feature
   ```
   Then create PR with clear description

6. **Review**:
   - Address review comments
   - Maintain conversation thread
   - Rebase if needed

7. **Merge**: Squash commits before merging to main

## Architecture & Design

### Core Modules

- **anonymizer/**: DICOM anonymization engine
- **risk/**: PHI risk assessment and scoring
- **diff/**: Dataset comparison utilities
- **core/**: Common utilities and actions
- **cli/**: Command-line interface

### Design Principles

1. **Fail Fast**: Validate inputs immediately
2. **Explicit Errors**: Always report what went wrong
3. **Bounded Scoring**: Risk scores have defined min/max
4. **Explainable Results**: Break down results by tag/component
5. **Testable**: Pure functions where possible
6. **Composable**: Tools work independently and together

### Adding Features

For new features:
1. Create feature branch
2. Add failing tests first
3. Implement feature
4. Update documentation
5. Ensure all tests pass
6. Submit PR

## Testing Philosophy

### Test Organization

```
tests/
├── test_actions.py          # Core action functions
├── test_anonymizer.py       # Engine tests
├── test_cli.py             # CLI commands
├── test_diff.py            # Comparison logic
├── test_risk.py            # Scoring system
└── ...
```

### Test Types

- **Unit Tests**: Individual functions
- **Integration Tests**: Component interactions
- **CLI Tests**: Command-line behavior and exit codes
- **Error Tests**: Exception handling and edge cases

### Coverage Requirements

- Core modules: 90%+ coverage
- CLI modules: 80%+ coverage (subprocess calls counted)
- Error paths: All exception handlers tested

## Reporting Issues

When reporting bugs, include:
- DICOM file example (if possible)
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version and dependencies
- Error messages and stack traces

## Performance Considerations

- Test with realistic DICOM files (1000+ elements)
- Profile memory usage for large batches
- Log processing performance
- Monitor risk scoring computation time

## License

By contributing, you agree your code will be licensed under the MIT License.

## Questions?

- Open an issue for discussions
- Check existing issues/PRs first
- Be patient - maintainers are volunteers
