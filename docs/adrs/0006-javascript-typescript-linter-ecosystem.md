# JavaScript/TypeScript Linter Ecosystem Support

* Status: accepted
* Deciders: Development Team
* Date: 2025-08-24

Technical Story: Define comprehensive JavaScript and TypeScript linting support with ESLint, Prettier, and JSHint integration.

## Context and Problem Statement

JavaScript and TypeScript projects require specialized linting tools that understand the dynamic nature of JavaScript, modern ES features, and TypeScript's type system. Native integration with the Node.js ecosystem is essential for optimal results.

## Decision Drivers

* Native JavaScript/TypeScript ecosystem integration
* Support for modern ES features and TypeScript syntax
* Integration with existing Node.js development workflows
* Automatic configuration detection for seamless developer experience
* High-quality AI-assisted fixes for JavaScript-specific patterns

## Considered Options

* Python-based JavaScript parsing with subprocess calls
* Native Node.js integration with ESLint, Prettier, JSHint
* Hybrid approach with selective tool integration
* External service integration for JavaScript linting

## Decision Outcome

Chosen option: "Native Node.js integration with ESLint, Prettier, JSHint", because it provides the best JavaScript/TypeScript analysis quality and leverages the mature Node.js tooling ecosystem.

### Positive Consequences

* Native JavaScript/TypeScript syntax understanding
* Automatic configuration detection (.eslintrc.*, tsconfig.json, package.json)
* Integration with existing developer toolchains (npm scripts, npx)
* High fix success rates for JavaScript-specific issues
* Support for modern frameworks (React, Vue, Angular)

### Negative Consequences

* Requires Node.js runtime alongside Python
* Increased complexity in dependency management
* Version compatibility management across Node.js ecosystem
* Additional setup requirements for development environments

## JavaScript/TypeScript Linter Implementations

### ESLint (Primary JavaScript/TypeScript Linting)
- **Version Support**: 8.x, 9.x with backward compatibility
- **Extensions**: `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`
- **TypeScript Integration**: Full `@typescript-eslint` parser and plugin support
- **Configuration Detection**: Automatic `.eslintrc.*`, `eslint.config.js`, `package.json` detection
- **Execution**: npx/npm script integration with JSON output parsing
- **Fix Success Rate**: 90-95% for formatting rules, 70-85% for logic rules

### Prettier (Code Formatting)
- **Version Support**: 2.x, 3.x
- **Purpose**: Opinionated code formatting for consistency
- **Integration**: Works alongside ESLint with conflict resolution
- **Configuration**: Auto-detects `.prettierrc.*`, `prettier.config.js`
- **Fix Success Rate**: 98% for formatting issues

### JSHint (Legacy JavaScript Support)
- **Version Support**: 2.x
- **Purpose**: Support for older JavaScript projects and legacy codebases
- **Configuration**: `.jshintrc` file detection
- **Use Case**: Projects not yet migrated to ESLint
- **Fix Success Rate**: 75-85% for basic JavaScript issues

## Implementation Architecture

### ESLintLinter Class
```python
class ESLintLinter(BaseLinter):
    def is_available(self) -> bool:
        # Try npx first, then global eslint
        return self._check_npx_eslint() or self._check_global_eslint()
    
    def build_command(self, file_paths: List[str]) -> List[str]:
        command = ["npx", "eslint"] if self._has_npx() else ["eslint"]
        command.extend(["--format=json"])
        
        # Auto-detect configuration
        config_file = self._detect_eslint_config()
        if config_file:
            command.extend(["--config", config_file])
        
        return command + file_paths
```

### TypeScript Support Detection
- **tsconfig.json**: Automatic TypeScript project detection
- **Package Dependencies**: Detection of TypeScript-related packages
- **File Extensions**: Dynamic `.ts`, `.tsx` support based on project setup
- **Parser Integration**: Automatic `@typescript-eslint/parser` usage

### Configuration Auto-Detection
```python
def _detect_eslint_config(self) -> Optional[str]:
    config_files = [
        ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.yaml",
        ".eslintrc.yml", ".eslintrc.json", ".eslintrc"
    ]
    
    # Check for package.json eslintConfig
    if self._has_package_json_config():
        return "package.json"
    
    return self._find_first_existing(config_files)
```

## Integration Patterns

### npm Script Integration
- **Detection**: Automatic detection of `npm run lint` scripts
- **Execution**: Preference for project-defined lint scripts
- **Output Parsing**: JSON format extraction from npm script output

### Project Type Detection
- **React Projects**: Automatic React plugin detection and configuration
- **Node.js APIs**: Server-side JavaScript linting profiles
- **TypeScript Projects**: Enhanced type-aware linting rules
- **Monorepos**: Multi-package linting support

### AI Integration Points
- **Context Enrichment**: JavaScript-specific error context for AI prompts
- **Framework Awareness**: React, Vue, Angular-specific fix patterns
- **Modern Syntax**: ES6+, TypeScript syntax understanding for fixes
- **Configuration Respect**: AI fixes respect project ESLint configuration

## Pros and Cons of the Options

### Python-based JavaScript parsing

* Good, because single runtime environment
* Good, because consistent with Python core architecture
* Bad, because limited JavaScript ecosystem understanding
* Bad, because poor TypeScript support
* Bad, because misses modern JavaScript features

### Native Node.js integration

* Good, because best-in-class JavaScript/TypeScript analysis
* Good, because leverages existing developer toolchains
* Good, because automatic configuration detection
* Good, because high fix success rates
* Bad, because dual runtime complexity
* Bad, because Node.js dependency requirement

### Hybrid approach with selective tools

* Good, because flexibility to choose integration depth
* Good, because can optimize per use case
* Bad, because inconsistent developer experience
* Bad, because complex configuration management
* Bad, because partial ecosystem benefits

### External service integration

* Good, because no local Node.js requirement
* Good, because always up-to-date tooling
* Bad, because network dependency and latency
* Bad, because limited configuration control
* Bad, because potential privacy concerns

## Links

* [ADR-0002](0002-ai-integration-architecture.md) - AI integration supporting JavaScript linters
* [ADR-0003](0003-modular-plugin-system.md) - Plugin architecture for JavaScript linters
* [ADR-0004](0004-hybrid-python-javascript-architecture.md) - Hybrid architecture enabling Node.js integration
* [Node.js Linters Guide](../NODEJS_LINTERS_GUIDE.md) - Comprehensive implementation documentation
