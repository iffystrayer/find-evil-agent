# Contributing

Thank you for your interest in contributing to Find Evil Agent! This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's coding standards

## Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/find-evil-agent.git
cd find-evil-agent

# Add upstream remote
git remote add upstream https://github.com/iffystrayer/find-evil-agent.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install development dependencies
uv pip install -e ".[dev]"

# macOS only: Install system libraries for PDF generation
brew install pango gdk-pixbuf libffi gobject-introspection cairo
```

### 3. Create Feature Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

## Development Workflow

### Test-Driven Development (MANDATORY)

**ALL code MUST be written tests-first:**

1. Write failing test
2. Implement minimal code to pass
3. Refactor and improve
4. Commit

**Example:**

```bash
# Step 1: Write test
cat > tests/unit/test_new_feature.py << 'EOF'
def test_new_feature():
    """Test new feature behavior"""
    assert new_feature() == expected_result
EOF

# Step 2: Run test (should fail)
pytest tests/unit/test_new_feature.py

# Step 3: Implement feature
# ... write code ...

# Step 4: Run test (should pass)
pytest tests/unit/test_new_feature.py

# Step 5: Commit
git add tests/unit/test_new_feature.py src/...
git commit -m "feat: Add new feature with tests"
```

### Code Quality Standards

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/find_evil_agent

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=find_evil_agent --cov-report=term
```

## Pull Request Process

### 1. Ensure Quality

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Code coverage ≥95% (`pytest --cov`)
- [ ] Code formatted (`black src/ tests/`)
- [ ] No linting errors (`ruff check`)
- [ ] Type hints added (`mypy src/`)
- [ ] Documentation updated

### 2. Commit Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature
git commit -m "feat(analyzer): Add email address IOC extraction"

# Bug fix
git commit -m "fix(executor): Handle SSH timeout correctly"

# Documentation
git commit -m "docs: Update LLM configuration guide"

# Test
git commit -m "test(selector): Add confidence threshold tests"

# Refactor
git commit -m "refactor(orchestrator): Simplify state management"
```

### 3. Submit Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create PR on GitHub
# - Provide clear description
# - Link related issues
# - Add screenshots if UI changes
```

### PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Development Guidelines

### Project Structure

- `src/find_evil_agent/` - Source code
- `tests/` - Test suite
- `docs/` - Documentation
- `tools/metadata.yaml` - Tool registry
- `pyproject.toml` - Project configuration

### Coding Standards

- **Python Version:** 3.11+
- **Style:** PEP 8 (via Black)
- **Type Hints:** Required for all functions
- **Docstrings:** Google style
- **Line Length:** 100 characters

### Testing Requirements

- **Coverage:** ≥95% for new code
- **Test Types:** Unit + Integration
- **No Mocks:** Use real integrations in integration tests
- **TDD:** Tests before implementation

## Areas for Contribution

### High Priority

- [ ] Additional forensic tool integrations
- [ ] Performance optimizations
- [ ] Documentation improvements
- [ ] Bug fixes

### Medium Priority

- [ ] New LLM provider support
- [ ] Enhanced report formats
- [ ] UI/UX improvements
- [ ] Example workflows

### Low Priority

- [ ] Additional IOC types
- [ ] Multi-language support
- [ ] Advanced visualizations

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/iffystrayer/find-evil-agent/issues)
- **Discussions:** [GitHub Discussions](https://github.com/iffystrayer/find-evil-agent/discussions)
- **Discord:** [GSD Community](https://discord.gg/gsd)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
