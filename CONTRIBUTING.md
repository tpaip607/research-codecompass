# Contributing to CodeCompass

Thank you for your interest in CodeCompass! This is primarily a research repository documenting a controlled experiment on graph-based navigation for agentic coding systems.

## Purpose of This Repository

This repository serves two main purposes:

1. **Reproducibility** — Provide complete artifacts (benchmark, harness, MCP server) so others can reproduce our findings
2. **Extension** — Enable researchers to build on our methodology for related studies

## How to Contribute

### Reporting Issues

If you encounter problems reproducing the experiment:

1. Check the [existing issues](https://github.com/tpaip607/research-codecompass/issues)
2. If your issue is new, open an issue with:
   - What you were trying to do
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Claude Code version)

### Questions About Methodology

For questions about the experimental design, metrics, or findings:

- Use [GitHub Discussions](https://github.com/tpaip607/research-codecompass/discussions)
- Tag your question appropriately (methodology, results, reproduction, etc.)

### Bug Fixes

If you find a bug in the harness, MCP server, or analysis code:

1. Fork the repository
2. Create a branch: `git checkout -b fix/issue-description`
3. Make your changes with clear commit messages
4. Submit a pull request with:
   - Description of the bug
   - How your fix addresses it
   - Any test cases you added

### Extensions and Related Work

If you're extending CodeCompass for your own research:

- **Cite the original work** (see README.md for BibTeX)
- **Share your findings** — we'd love to hear how you built on this work!
- **Consider contributing back** if your extension would benefit others reproducing the study

## What We Won't Accept

To maintain the integrity of the published research:

- Changes to benchmark tasks or gold standards
- Modifications to core metrics (ACS, FCTC definitions)
- Retroactive changes to experimental conditions

These are fixed as part of the published study. Extensions should be clearly marked as such.

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/research-codecompass.git
cd research-codecompass

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black ruff

# Run tests (if any)
pytest tests/

# Format code
black .
ruff check .
```

## Code Style

- Python code follows PEP 8
- Use type hints where appropriate
- Keep functions focused and well-documented
- Add docstrings for public APIs

## Questions?

For general questions, use [Discussions](https://github.com/tpaip607/research-codecompass/discussions).

For bugs or specific issues, use [Issues](https://github.com/tpaip607/research-codecompass/issues).

For direct research collaboration inquiries, see contact info in the paper.

---

Thank you for helping advance research in agentic coding systems!
