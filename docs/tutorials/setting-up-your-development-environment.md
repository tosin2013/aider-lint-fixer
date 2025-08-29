# Setting Up Your Python Development Environment for `aider-lint-fixer`

This tutorial walks you through configuring a modern Python workflow that matches the toolchain used by `aider-lint-fixer`.

## 1. Install Python via `pyenv`

`aider-lint-fixer` targets Python 3.11+.

```bash
# Install pyenv (macOS / Linux)
brew install pyenv            # or: curl https://pyenv.run | bash

# Install and activate the required version
pyenv install 3.11.9
pyenv local 3.11.9            # writes .python-version
```

## 2. Create an isolated virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

> **Tip:** The project’s `Makefile` contains convenience targets like `make venv` that automate these steps.

## 3. Install project dependencies

```bash
pip install -r requirements.txt -r requirements-test.txt
```

These files pin runtime and testing libraries (e.g., `aider-chat`, `ansible-lint`, `pytest`).

## 4. Enable pre-commit hooks (recommended)

```bash
pip install pre-commit
pre-commit install
```

Hooks automatically run linters & formatters on every commit (`ruff`, `black`, `flake8`).

## 5. Recommended VS Code configuration

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.formatting.provider": "black",
  "editor.codeActionsOnSave": {
    "source.organizeImports": "always"
  }
}
```

## 6. Running the CLI

```bash
python -m aider_lint_fixer --help
```

## 7. Running the test suite

```bash
pytest -q
```

## Next Steps

* Read the [Architecture Overview](../explanation/architecture-overview.md) to understand module boundaries.
* See [How-to: Debug Common Issues](../how-to/how-to-debug-common-issues.md) for troubleshooting.
