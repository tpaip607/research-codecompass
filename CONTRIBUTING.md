# Contributing to CodeCompass

Thank you for your interest in contributing to CodeCompass! This document provides guidelines for contributing to this research project.

## Development Workflow

### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/research-codecompass.git
cd research-codecompass
```

### 2. Create a Feature Branch
```bash
# Always create a new branch for your changes
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `ci/` - CI/CD improvements

### 3. Make Your Changes

**Important guidelines:**
- Do NOT commit paper drafts (in `paper/` folder)
- Do NOT commit trial results (in `results/` folder)
- Do NOT commit API keys or secrets
- Keep commits focused and atomic
- Write clear commit messages

### 4. Test Your Changes

```bash
# Verify imports work
python -c "from harness import calculate_acs, aggregate_results"
python -c "from data_processing import ast_parser"

# Run pylint (should pass with acceptable score)
pylint $(git ls-files '*.py')

# Test scripts execute without errors
python harness/calculate_acs.py --help
```

### 5. Commit Your Changes

```bash
git add <files>
git commit -m "Clear, descriptive commit message"

# Example commit messages:
# - "Add ECR metric calculation to calculate_acs.py"
# - "Fix Neo4j connection timeout in build_graph.py"
# - "Update README with Neo4j setup instructions"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub:
1. Go to the repository on GitHub
2. Click "Pull requests" → "New pull request"
3. Select your branch
4. Fill out the PR template
5. Submit for review

## Pull Request Guidelines

### PR Title Format
```
[Type] Brief description

Examples:
- [Feature] Add statistical validation to results
- [Fix] Resolve Neo4j connection timeout
- [Docs] Update README with setup instructions
- [Refactor] Simplify ACS calculation logic
```

### PR Description
Use the provided template to:
- Describe what changes were made
- Explain why the changes are needed
- Link related issues
- Confirm testing was performed
- Complete the checklist

### Review Process
1. Automated CI checks must pass (pylint, structure validation)
2. At least 1 approval required (for collaborative work)
3. All conversations must be resolved
4. Branch must be up to date with main

## Code Style Guidelines

### Python Style
- Follow PEP 8 guidelines (with relaxed limits per .pylintrc)
- Maximum line length: 120 characters
- Use descriptive variable names
- Add comments for complex logic
- Docstrings for public functions (research scripts can be less formal)

### File Organization
```
research-codecompass/
├── benchmarks/tasks/      # Benchmark task definitions
├── data_processing/       # AST parsing, graph building
├── harness/              # Experiment execution scripts
├── mcp_server/           # MCP server implementation
├── .github/              # CI/CD workflows
└── paper/                # GITIGNORED - paper drafts
```

## Commit Message Guidelines

### Format
```
[Type] Brief summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how.

Fixes #123
Relates to #456
```

### Types
- `[Feature]` - New functionality
- `[Fix]` - Bug fixes
- `[Docs]` - Documentation changes
- `[Refactor]` - Code restructuring
- `[Perf]` - Performance improvements
- `[Test]` - Test additions/changes
- `[CI]` - CI/CD changes

### Examples
```
[Feature] Add Edit Completeness Rate (ECR) metric

Extended calculate_acs.py to track Read vs Edit operations
separately. ECR measures fraction of required files actually
edited, providing a correctness signal beyond navigation.

Relates to #42
```

```
[Fix] Resolve Neo4j connection timeout in CI

Increased healthcheck interval and added retry logic to
docker-compose.yml. Prevents intermittent failures in
GitHub Actions.

Fixes #38
```

## Running the Full Experiment

**Warning:** Full reproduction requires ~$200-300 in API credits and 8-12 hours.

```bash
# Build infrastructure
docker compose up -d
python data_processing/ast_parser.py
python data_processing/build_graph.py
python data_processing/build_bm25_index.py

# Run single trial (test)
./harness/run_trial.sh 23 C 1

# Run full experiment (expensive!)
./harness/run_all.sh
```

## Questions or Issues?

- **Bug reports:** Open an issue with reproduction steps
- **Feature requests:** Open an issue describing the use case
- **Questions:** Use GitHub Discussions

## Research Ethics

This is a research repository. Please:
- Cite the paper if you use this code in your research
- Do not republish experimental results without attribution
- Respect the MIT license terms

---

**Thank you for contributing to CodeCompass!**
