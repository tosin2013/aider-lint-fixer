# Node.js Linters Guide

This guide covers comprehensive support for JavaScript and TypeScript linting with aider-lint-fixer, including ESLint, Prettier, and project-specific configurations.

## Supported Node.js Linters

### ESLint
- **Version Support**: 8.x, 9.x
- **Extensions**: `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`
- **Configuration Detection**: Automatic detection of `.eslintrc.*` files
- **TypeScript Support**: Full integration with `@typescript-eslint`

### Prettier
- **Version Support**: 2.x, 3.x
- **Integration**: Works alongside ESLint for formatting
- **Configuration**: Auto-detects `.prettierrc.*` files

### JSHint
- **Version Support**: 2.x
- **Legacy Support**: For older JavaScript projects
- **Configuration**: `.jshintrc` file detection

## Quick Start

### 1. Project Detection

aider-lint-fixer automatically detects Node.js projects by looking for:

```bash
# Package files
package.json
package-lock.json
yarn.lock

# TypeScript configuration
tsconfig.json

# ESLint configuration
.eslintrc.js
.eslintrc.json
.eslintrc.yml
eslint.config.js

# Prettier configuration
.prettierrc
.prettierrc.json
prettier.config.js
```

### 2. Basic Usage

```bash
# Automatic detection and fixing
aider-lint-fixer ./my-node-project

# Specific linter
aider-lint-fixer --linter eslint ./src

# TypeScript project
aider-lint-fixer --profile strict ./typescript-app
```

## ESLint Integration

### Automatic Configuration Detection

aider-lint-fixer detects and respects your existing ESLint setup:

```javascript
// .eslintrc.js - Automatically detected
module.exports = {
  extends: ['@typescript-eslint/recommended'],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  rules: {
    'prefer-const': 'error',
    'no-unused-vars': 'warn'
  }
};
```

### Supported ESLint Rules

Common rules with high fix success rates:

| Rule | Fix Rate | Complexity |
|------|----------|------------|
| `semi` | 98% | Trivial |
| `quotes` | 95% | Trivial |
| `indent` | 92% | Simple |
| `no-unused-vars` | 88% | Simple |
| `prefer-const` | 94% | Simple |
| `no-trailing-spaces` | 99% | Trivial |
| `max-len` | 75% | Moderate |

### TypeScript-Specific Rules

Enhanced support for TypeScript projects:

```typescript
// Example fixes for common TypeScript issues
// @typescript-eslint/no-unused-vars
const unusedVar = 'remove me'; // ❌ Removed automatically

// @typescript-eslint/prefer-const
let unchangedValue = 'hello'; // ❌ Changed to const

// @typescript-eslint/explicit-function-return-type
function getValue() { // ❌ Adds return type
  return 42;
}
```

## Project Profiles

### Basic Profile (Development)

Optimized for development environments:

```bash
aider-lint-fixer --profile basic ./src
```

**Includes:**
- Essential syntax errors
- Code style issues
- Basic TypeScript errors
- Performance suggestions

**Excludes:**
- Strict type checking
- Complex refactoring rules
- Deprecated APIs (warnings only)

### Strict Profile (Production)

Comprehensive checking for production code:

```bash
aider-lint-fixer --profile strict ./src
```

**Includes:**
- All basic profile rules
- Strict TypeScript checking
- Security vulnerability detection
- Performance optimizations
- Code complexity analysis

## Configuration Examples

### 1. React Project

```json
// package.json
{
  "scripts": {
    "lint": "aider-lint-fixer --profile basic ./src",
    "lint:fix": "aider-lint-fixer --auto-fix ./src",
    "lint:strict": "aider-lint-fixer --profile strict ./src"
  },
  "devDependencies": {
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.45.0"
  }
}
```

### 2. Node.js API Project

```javascript
// .eslintrc.js
module.exports = {
  env: {
    node: true,
    es2022: true
  },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended'
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  rules: {
    'no-console': 'warn', // Allow console in development
    'prefer-const': 'error'
  }
};
```

### 3. Monorepo Setup

```bash
# Root level - lint all packages
aider-lint-fixer --recursive ./packages

# Specific package
aider-lint-fixer ./packages/frontend

# Different profiles per package
aider-lint-fixer --profile basic ./packages/frontend
aider-lint-fixer --profile strict ./packages/api
```

## Advanced Features

### 1. Custom Rule Configuration

Override fixability for specific rules:

```json
// .aider-lint-fixer.json
{
  "linters": {
    "eslint": {
      "force_fix_rules": [
        "semi",
        "quotes",
        "prefer-const"
      ],
      "skip_rules": [
        "no-any" // Too complex for auto-fix
      ]
    }
  }
}
```

### 2. TypeScript Integration

Enhanced TypeScript support:

```bash
# Respect tsconfig.json settings
aider-lint-fixer --typescript-project ./tsconfig.json ./src

# Multiple TypeScript projects
aider-lint-fixer \
  --typescript-project ./frontend/tsconfig.json ./frontend/src \
  --typescript-project ./backend/tsconfig.json ./backend/src
```

### 3. Performance Optimization

For large Node.js projects:

```bash
# Parallel processing
aider-lint-fixer --parallel 4 ./large-project

# Incremental fixing (only changed files)
aider-lint-fixer --incremental ./src

# Focus on specific file types
aider-lint-fixer --include "*.ts,*.tsx" ./src
```

## Common Use Cases

### 1. Legacy JavaScript Migration

Converting old JavaScript to modern standards:

```bash
# Step 1: Basic cleanup
aider-lint-fixer --profile basic ./legacy-js

# Step 2: Modern JavaScript features
aider-lint-fixer --profile strict --rules "prefer-const,arrow-functions" ./legacy-js

# Step 3: TypeScript migration prep
aider-lint-fixer --typescript-prep ./legacy-js
```

### 2. CI/CD Integration

```yaml
# .github/workflows/lint.yml
name: Lint Check
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npx aider-lint-fixer --strict --dry-run ./src
```

### 3. Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: aider-lint-fixer
        name: Aider Lint Fixer
        entry: aider-lint-fixer
        language: system
        files: '\.(js|jsx|ts|tsx)$'
        args: ['--auto-fix']
```

## Troubleshooting

### Common Issues

#### 1. ESLint Configuration Not Found

```bash
# Check configuration detection
aider-lint-fixer --debug --dry-run ./src

# Manually specify configuration
aider-lint-fixer --eslint-config ./.eslintrc.js ./src
```

#### 2. TypeScript Parsing Errors

```bash
# Verify TypeScript setup
npx tsc --noEmit

# Use TypeScript-aware mode
aider-lint-fixer --typescript ./src
```

#### 3. Large Project Performance

```bash
# Use incremental mode
aider-lint-fixer --incremental ./large-project

# Exclude node_modules and build directories
aider-lint-fixer --exclude "**/node_modules/**,**/dist/**" ./project
```

### Performance Tips

1. **Use .eslintignore**: Exclude unnecessary files
2. **Incremental mode**: Only process changed files
3. **Parallel processing**: Use `--parallel` for large projects
4. **Targeted fixing**: Focus on specific rule categories

## Rule Categories

### High Success Rate (>90%)

- Formatting rules (`semi`, `quotes`, `indent`)
- Simple style rules (`prefer-const`, `arrow-spacing`)
- Basic cleanup (`no-trailing-spaces`, `no-multiple-empty-lines`)

### Medium Success Rate (70-90%)

- Variable usage (`no-unused-vars`, `no-undef`)
- Import/export organization
- Basic TypeScript annotations

### Complex Rules (<70%)

- Logic changes (`no-implicit-any`, `strict-boolean-expressions`)
- Architectural refactoring
- Complex type inference

## Integration with Other Tools

### Prettier Integration

```bash
# Run Prettier first, then ESLint
prettier --write ./src && aider-lint-fixer ./src

# Or use combined profile
aider-lint-fixer --profile prettier-eslint ./src
```

### Webpack/Vite Integration

Works seamlessly with build tools:

```javascript
// webpack.config.js - No special configuration needed
// Vite.config.js - Standard ESLint plugin integration
```

## Resources

- [ESLint Official Rules](https://eslint.org/docs/rules/)
- [TypeScript ESLint Rules](https://typescript-eslint.io/rules/)
- [Installation Guide](./INSTALLATION_GUIDE.md)
- [Linter Testing Guide](./LINTER_TESTING_GUIDE.md)