# Error Codes Reference

This document provides a comprehensive reference for all error codes, exit codes, and error messages used by aider-lint-fixer.

## Exit Codes

aider-lint-fixer uses standard Unix exit codes to indicate the result of operations:

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| `0` | Success | No errors found or all errors successfully fixed |
| `1` | Errors Found | Lint errors were detected (in check-only mode) |
| `2` | System Error | Tool configuration or system error occurred |

## Linter-Specific Exit Codes

Different linters use different exit codes, which aider-lint-fixer normalizes:

### ESLint Exit Codes
| Code | Meaning | aider-lint-fixer Handling |
|------|---------|---------------------------|
| `0` | No problems | Success |
| `1` | Issues found | Analyzed and prioritized |
| `2` | Fatal error | System error reported |

### Ansible-lint Exit Codes
| Code | Meaning | aider-lint-fixer Handling |
|------|---------|---------------------------|
| `0` | No violations | Success |
| `2` | Violations found | Analyzed and prioritized |
| `3` | Fatal error | System error reported |

### Python Linters Exit Codes
| Linter | Success | Issues | Fatal |
|--------|---------|--------|-------|
| flake8 | `0` | `1` | `2` |
| pylint | `0` | Non-zero | System error |
| mypy | `0` | `1` | `2` |

## Error Categories

aider-lint-fixer categorizes errors for intelligent handling:

### STYLE
Low-risk formatting and style issues that are safe to auto-fix.

**Examples:**
- `semi` (ESLint): Missing semicolons
- `quotes` (ESLint): Inconsistent quote styles
- `indent` (ESLint): Incorrect indentation
- `E101` (flake8): Indentation contains mixed spaces and tabs
- `W291` (flake8): Trailing whitespace

### LOGIC
Moderate-risk logic issues that may need careful handling.

**Examples:**
- `no-unused-vars` (ESLint): Unused variables
- `no-undef` (ESLint): Undefined variables
- `F401` (flake8): Module imported but unused
- `W0612` (pylint): Unused variable

### STRUCTURAL
High-risk structural issues that require architect mode.

**Examples:**
- `no-implicit-any` (TypeScript): Missing type annotations
- `strict-boolean-expressions` (TypeScript): Complex boolean logic
- `C0103` (pylint): Invalid name conventions
- Complex refactoring requirements

## Common Error Codes by Linter

### ESLint Error Codes

#### High Success Rate (>90%)
| Rule ID | Description | Fix Rate | Category |
|---------|-------------|----------|----------|
| `semi` | Missing semicolons | 98% | STYLE |
| `quotes` | Quote style consistency | 95% | STYLE |
| `indent` | Indentation issues | 92% | STYLE |
| `no-trailing-spaces` | Trailing whitespace | 99% | STYLE |
| `prefer-const` | Use const instead of let | 94% | STYLE |

#### Medium Success Rate (70-90%)
| Rule ID | Description | Fix Rate | Category |
|---------|-------------|----------|----------|
| `no-unused-vars` | Unused variables | 88% | LOGIC |
| `no-undef` | Undefined variables | 75% | LOGIC |
| `arrow-spacing` | Arrow function spacing | 92% | STYLE |
| `comma-spacing` | Comma spacing | 89% | STYLE |

#### Complex Rules (<70%)
| Rule ID | Description | Fix Rate | Category |
|---------|-------------|----------|----------|
| `no-implicit-any` | Missing TypeScript types | 45% | STRUCTURAL |
| `strict-boolean-expressions` | Complex boolean logic | 35% | STRUCTURAL |
| `prefer-nullish-coalescing` | Nullish coalescing | 60% | LOGIC |

### Python Error Codes (flake8)

#### High Success Rate (>90%)
| Code | Description | Fix Rate | Category |
|------|-------------|----------|----------|
| `E101` | Indentation mixed spaces/tabs | 98% | STYLE |
| `E111` | Indentation not multiple of 4 | 95% | STYLE |
| `E203` | Whitespace before ':' | 99% | STYLE |
| `E231` | Missing whitespace after ',' | 97% | STYLE |
| `W291` | Trailing whitespace | 99% | STYLE |

#### Medium Success Rate (70-90%)
| Code | Description | Fix Rate | Category |
|------|-------------|----------|----------|
| `F401` | Module imported but unused | 85% | LOGIC |
| `F841` | Local variable assigned but never used | 80% | LOGIC |
| `E501` | Line too long | 75% | STYLE |

#### Complex Rules (<70%)
| Code | Description | Fix Rate | Category |
|------|-------------|----------|----------|
| `F821` | Undefined name | 45% | STRUCTURAL |
| `C901` | Function too complex | 25% | STRUCTURAL |
| `E712` | Comparison to True/False | 65% | LOGIC |

### Ansible-lint Error Codes

#### High Success Rate (>90%)
| Rule | Description | Fix Rate | Category |
|------|-------------|----------|----------|
| `yaml[indentation]` | YAML indentation | 95% | STYLE |
| `yaml[line-length]` | YAML line length | 88% | STYLE |
| `yaml[trailing-spaces]` | Trailing spaces | 99% | STYLE |

#### Medium Success Rate (70-90%)
| Rule | Description | Fix Rate | Category |
|------|-------------|----------|----------|
| `name[missing]` | Missing task names | 85% | LOGIC |
| `key-order[task]` | Task key ordering | 78% | STYLE |

#### Complex Rules (<70%)
| Rule | Description | Fix Rate | Category |
|------|-------------|----------|----------|
| `no-changed-when` | Missing changed_when | 45% | STRUCTURAL |
| `risky-shell-pipe` | Dangerous shell usage | 35% | STRUCTURAL |

## Error Messages and Meanings

### Configuration Errors

#### "Configuration Not Found"
```
❌ Error: Configuration file not found
💡 Hint: Create .aider-lint-fixer.yml or use --config flag
```
**Solution**: Create a configuration file or specify path with `--config`

#### "Linter Not Available"
```
❌ Error: eslint not found in PATH
💡 Hint: Install with: npm install -g eslint
```
**Solution**: Install the missing linter using the suggested command

#### "Invalid Configuration"
```
❌ Error: Invalid YAML syntax in configuration file
💡 Hint: Check indentation and quotes in .aider-lint-fixer.yml
```
**Solution**: Validate and fix YAML syntax errors

### Runtime Errors

#### "No Files to Process"
```
⚠️ Warning: No files found matching the specified patterns
💡 Hint: Check --include and --exclude patterns
```
**Solution**: Verify file patterns and directory paths

#### "API Key Missing"
```
❌ Error: API key not found for provider 'deepseek'
💡 Hint: Set DEEPSEEK_API_KEY environment variable
```
**Solution**: Configure the appropriate API key environment variable

#### "Cost Limit Exceeded"
```
⚠️ Warning: Maximum cost limit ($100.00) reached
💡 Hint: Increase --max-cost or focus on fewer files
```
**Solution**: Increase budget or reduce scope

### Linter Execution Errors

#### "Linter Command Failed"
```
❌ Error: ESLint exited with code 2
💡 Hint: Check ESLint configuration and project setup
```
**Solution**: Verify linter configuration and installation

#### "Parse Error"
```
❌ Error: Could not parse linter output
💡 Hint: Check if linter version is supported
```
**Solution**: Update to supported linter version

## Error Handling Strategies

### Automatic Error Recovery

aider-lint-fixer implements several automatic recovery strategies:

1. **Fallback Providers**: If primary LLM fails, automatically tries fallback providers
2. **Incremental Fixing**: Processes errors in batches to avoid overwhelming the system
3. **Error Categorization**: Routes complex errors to architect mode automatically

### User Intervention Points

#### Interactive Mode Prompts
```bash
🤔 Complex error detected: no-implicit-any in src/utils.ts:45
   This requires type annotation changes that may affect other files.
   
   Options:
   [f] Fix automatically (may need manual review)
   [s] Skip this error
   [a] Use architect mode for careful analysis
   [q] Quit
   
Choose: 
```

#### Confirmation Dialogs
```bash
⚠️ About to modify 15 files with 47 changes
   Estimated cost: $2.40
   
Continue? [y/N]:
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "Too Many Errors"
**Symptoms**: Tool reports excessive errors and stops
**Solution**: Use `--max-errors` flag or `--force` mode with strategic analysis

#### 2. "Low Success Rate"
**Symptoms**: Many fixes fail or create new errors
**Solution**: Use `--profile basic` for safer fixes, or `--architect-mode` for complex errors

#### 3. "Performance Issues"
**Symptoms**: Tool runs slowly on large projects
**Solution**: Use `--max-files`, `--exclude` patterns, or `--smart-linter-selection`

#### 4. "Inconsistent Results"
**Symptoms**: Different results on repeated runs
**Solution**: Check for configuration drift, use `--dag-workflow` for deterministic processing

### Debug Mode Information

Enable debug mode with `--verbose` or `--debug` for detailed error information:

```bash
aider-lint-fixer --verbose --dry-run ./src
```

**Debug Output Includes:**
- Linter detection results
- Configuration loading details
- Error categorization reasoning
- Cost calculations
- Strategic decision explanations

### Logging and Error Tracking

#### Log Levels
| Level | Purpose | Example |
|-------|---------|---------|
| `DEBUG` | Detailed diagnostic info | Linter command execution |
| `INFO` | General progress | Files processed, errors found |
| `WARNING` | Non-fatal issues | Skipped files, fallback usage |
| `ERROR` | Fatal errors | Configuration errors, API failures |

#### Log File Location
- Default: `aider-lint-fixer.log` in current directory
- Custom: Use `--log-file` option
- Rotation: Automatically rotates when exceeding size limits

## Error Code Reference Tables

### Exit Code Quick Reference
```bash
# Check exit code after running
aider-lint-fixer --check-only ./src
echo "Exit code: $?"

# 0 = No errors found
# 1 = Errors found (normal in check mode)
# 2 = System/configuration error
```

### Error Severity Levels
| Severity | Description | Action |
|----------|-------------|--------|
| `TRIVIAL` | Safe formatting fixes | Auto-fix without confirmation |
| `SIMPLE` | Low-risk logic fixes | Auto-fix with batch confirmation |
| `MODERATE` | Medium-risk changes | Individual confirmation |
| `COMPLEX` | High-risk structural changes | Architect mode required |

## Integration with CI/CD

### Recommended Exit Code Handling

```yaml
# GitHub Actions example
- name: Lint and Fix
  run: aider-lint-fixer --check-only ./src
  continue-on-error: true
  
- name: Check Results
  run: |
    if [ $? -eq 0 ]; then
      echo "✅ No lint errors found"
    elif [ $? -eq 1 ]; then
      echo "⚠️ Lint errors detected"
      exit 1
    else
      echo "❌ System error occurred"
      exit 2
    fi
```

### Error Reporting Integration

```bash
# Generate JSON report for CI systems
aider-lint-fixer --output-format json --check-only ./src > lint-report.json

# Parse results in CI
if [ $? -eq 1 ]; then
  echo "::error::Lint errors found. See lint-report.json for details"
fi
```

This comprehensive error codes reference helps you understand, diagnose, and resolve issues when using aider-lint-fixer across different linters and project configurations.
