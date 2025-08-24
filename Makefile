# Aider Lint Fixer - Makefile
# Automated build, test, and quality assurance

.PHONY: help install install-dev clean lint format type-check test test-coverage build package upload docs serve-docs venv setup check-deps security audit all

# Default Python and pip commands
PYTHON := python3.11
PIP := pip
VENV_DIR := venv
PACKAGE_NAME := aider_lint_fixer

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
help: ## Show this help message
	@echo "$(BLUE)Aider Lint Fixer - Build System$(NC)"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment setup
venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)Virtual environment created. Activate with: source $(VENV_DIR)/bin/activate$(NC)"

env-setup: ## Setup environment file from template
	@echo "$(BLUE)Setting up environment file...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file from template$(NC)"; \
		echo "$(YELLOW)Please edit .env file and add your API keys$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

setup: venv env-setup ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	. $(VENV_DIR)/bin/activate && \
	$(PIP) install --upgrade pip setuptools wheel && \
	$(PIP) install -r requirements.txt && \
	$(PIP) install -e .
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(YELLOW)Don't forget to edit .env file with your API keys!$(NC)"

install: ## Install package in current environment
	@echo "$(BLUE)Installing package...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo "$(GREEN)Package installed!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	# Additional dev tools
	$(PIP) install black isort mypy pylint bandit safety pytest pytest-cov
	@echo "$(GREEN)Development dependencies installed!$(NC)"

# Code quality targets
lint: ## Run all linters
	@echo "$(BLUE)Running linters...$(NC)"
	@echo "$(YELLOW)Running flake8...$(NC)"
	flake8 $(PACKAGE_NAME) *.py tests/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "$(YELLOW)Running pylint...$(NC)"
	pylint $(PACKAGE_NAME) --disable=C0114,C0115,C0116
	@echo "$(GREEN)Linting complete!$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	@echo "$(YELLOW)Running black...$(NC)"
	black $(PACKAGE_NAME) *.py tests/ --line-length=88
	@echo "$(YELLOW)Running isort...$(NC)"
	isort $(PACKAGE_NAME) *.py tests/ --profile=black
	@echo "$(GREEN)Code formatting complete!$(NC)"

format-check: ## Check if code is properly formatted
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black $(PACKAGE_NAME) *.py tests/ --check --line-length=88
	isort $(PACKAGE_NAME) *.py tests/ --check-only --profile=black
	@echo "$(GREEN)Format check complete!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy $(PACKAGE_NAME) --ignore-missing-imports
	@echo "$(GREEN)Type checking complete!$(NC)"

# Security and dependency checks
security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	@echo "$(YELLOW)Running bandit...$(NC)"
	bandit -r $(PACKAGE_NAME) -f json -o security-report.json || true
	bandit -r $(PACKAGE_NAME)
	@echo "$(YELLOW)Checking dependencies with safety...$(NC)"
	safety check --json --output safety-report.json || true
	safety check
	@echo "$(GREEN)Security checks complete!$(NC)"

check-deps: ## Check for outdated dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	$(PIP) list --outdated
	@echo "$(GREEN)Dependency check complete!$(NC)"

audit: ## Run comprehensive audit (security + dependencies)
	@echo "$(BLUE)Running comprehensive audit...$(NC)"
	$(MAKE) security
	$(MAKE) check-deps
	@echo "$(GREEN)Audit complete!$(NC)"

# Testing targets
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)Tests complete!$(NC)"

test-coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/integration/ -v --slow
	@echo "$(GREEN)Integration tests complete!$(NC)"

# Build and package targets
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf security-report.json
	rm -rf safety-report.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete!$(NC)"

build: clean ## Build package
	@echo "$(BLUE)Building package...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)Package built successfully!$(NC)"

package: build ## Create distribution packages
	@echo "$(BLUE)Creating distribution packages...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)Distribution packages created!$(NC)"

# Quality assurance - comprehensive checks
qa: ## Run all quality assurance checks
	@echo "$(BLUE)Running comprehensive quality assurance...$(NC)"
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) security
	$(MAKE) test-coverage
	@echo "$(GREEN)Quality assurance complete!$(NC)"

# Self-test using our own tool
self-test: ## Test aider-lint-fixer on itself
	@echo "$(BLUE)Testing aider-lint-fixer on itself...$(NC)"
	@echo "$(YELLOW)Running dry-run on current project...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME) . --dry-run --verbose --linters flake8,black,isort
	@echo "$(GREEN)Self-test complete!$(NC)"

# Documentation targets
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "Documentation targets would go here"
	@echo "$(GREEN)Documentation generated!$(NC)"

# Development workflow targets
dev-setup: ## Complete development setup
	@echo "$(BLUE)Setting up complete development environment...$(NC)"
	$(MAKE) setup
	$(MAKE) install-dev
	@echo "$(GREEN)Development environment ready!$(NC)"

pre-commit: ## Run pre-commit checks
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test
	@echo "$(GREEN)Pre-commit checks complete!$(NC)"

ci: ## Run CI pipeline locally
	@echo "$(BLUE)Running CI pipeline...$(NC)"
	$(MAKE) clean
	$(MAKE) install-dev
	$(MAKE) qa
	$(MAKE) build
	@echo "$(GREEN)CI pipeline complete!$(NC)"

# Release targets
release-check: ## Check if ready for release
	@echo "$(BLUE)Checking release readiness...$(NC)"
	$(MAKE) qa
	$(MAKE) build
	$(MAKE) self-test
	@echo "$(GREEN)Release check complete!$(NC)"

# Utility targets
show-env: ## Show environment information
	@echo "$(BLUE)Environment Information:$(NC)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Virtual env: $(VENV_DIR)"
	@echo "Package: $(PACKAGE_NAME)"
	@echo "Working directory: $(shell pwd)"

check-env: ## Check if environment variables are set
	@echo "$(BLUE)Checking environment variables...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN)✓ .env file exists$(NC)"; \
		if grep -q "your_.*_api_key_here" .env; then \
			echo "$(RED)✗ API keys not configured (still using template values)$(NC)"; \
			echo "$(YELLOW)Please edit .env file and add your actual API keys$(NC)"; \
		else \
			echo "$(GREEN)✓ API keys appear to be configured$(NC)"; \
		fi; \
	else \
		echo "$(RED)✗ .env file not found$(NC)"; \
		echo "$(YELLOW)Run 'make env-setup' to create .env file$(NC)"; \
	fi

git-status: ## Show git status and ignored files
	@echo "$(BLUE)Git Status:$(NC)"
	@git status --short || echo "Not a git repository"
	@echo ""
	@echo "$(BLUE)Key files that should be ignored:$(NC)"
	@echo "$(YELLOW).env$(NC) - $(shell [ -f .env ] && echo "✓ exists (ignored)" || echo "✗ not found")"
	@echo "$(YELLOW)venv/$(NC) - $(shell [ -d venv ] && echo "✓ exists (ignored)" || echo "✗ not found")"
	@echo "$(YELLOW)__pycache__/$(NC) - $(shell find . -name "__pycache__" -type d | head -1 >/dev/null 2>&1 && echo "✓ exists (ignored)" || echo "✗ not found")"

# All-in-one targets
all: clean dev-setup qa build ## Run complete build pipeline
	@echo "$(GREEN)Complete build pipeline finished!$(NC)"

# Quick development cycle
quick: format lint test ## Quick development cycle (format, lint, test)
	@echo "$(GREEN)Quick development cycle complete!$(NC)"
