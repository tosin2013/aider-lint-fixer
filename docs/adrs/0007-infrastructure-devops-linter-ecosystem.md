# Infrastructure/DevOps Linter Ecosystem Support

* Status: accepted
* Deciders: Development Team
* Date: 2025-08-24

Technical Story: Define comprehensive infrastructure and DevOps linting support with ansible-lint and related tooling.

## Context and Problem Statement

Infrastructure-as-Code and DevOps workflows require specialized linting tools that understand configuration management syntax, deployment patterns, and infrastructure best practices. Ansible is a primary focus given its widespread adoption.

## Decision Drivers

* Infrastructure-as-Code quality and security validation
* DevOps workflow integration and automation support
* Configuration management best practices enforcement
* Security vulnerability detection in infrastructure code
* AI-assisted fixes for infrastructure configuration issues

## Considered Options

* Ansible-only linting support
* Multi-tool infrastructure linting (ansible-lint + terraform + kubernetes)
* Generic YAML/configuration file linting
* External service integration for infrastructure validation

## Decision Outcome

Chosen option: "Ansible-only linting support with extensible architecture", because Ansible is the most commonly used configuration management tool, while maintaining plugin architecture for future expansion.

### Positive Consequences

* Comprehensive Ansible playbook and role validation
* Security best practices enforcement for infrastructure code
* Integration with existing Ansible development workflows
* High-quality AI fixes for common Ansible patterns
* Foundation for expanding to other infrastructure tools

### Negative Consequences

* Limited to Ansible ecosystem initially
* Requires Ansible knowledge for optimal configuration
* May not cover all infrastructure-as-code scenarios
* Additional tool dependency in development environment

## Infrastructure Linter Implementation

### ansible-lint (Ansible Configuration Validation)
- **Version Support**: 24.x, 25.x with backward compatibility
- **File Types**: Playbooks (`.yml`, `.yaml`), roles, inventory files
- **Rule Categories**: Security, best practices, deprecated features, syntax
- **Configuration**: `.ansible-lint`, `ansible-lint.yml` detection
- **Integration**: JSON output format for structured error parsing
- **Fix Success Rate**: 80-90% for syntax and style issues, 60-75% for logic issues

## Implementation Architecture

### AnsibleLintLinter Class
```python
class AnsibleLintLinter(BaseLinter):
    def is_available(self) -> bool:
        try:
            result = self.run_command(["ansible-lint", "--version"])
            return result.returncode == 0
        except Exception:
            return False
    
    def build_command(self, file_paths: List[str]) -> List[str]:
        command = ["ansible-lint", "--format=json", "--parseable"]
        
        # Auto-detect configuration
        config_file = self._detect_ansible_lint_config()
        if config_file:
            command.extend(["-c", config_file])
        
        return command + file_paths
```

### Ansible Project Detection
- **Playbook Detection**: Presence of `*.yml` files with Ansible syntax
- **Role Structure**: Standard Ansible role directory structure
- **Inventory Files**: Ansible inventory file patterns
- **Configuration Files**: `ansible.cfg`, `.ansible-lint` presence

### Rule Categories and Fix Patterns

#### Security Rules (High Priority)
- **no-log-passwords**: Sensitive data exposure prevention
- **risky-file-permissions**: File permission security validation
- **command-instead-of-module**: Security-focused module usage
- **Fix Success Rate**: 85-95%

#### Best Practices Rules
- **yaml-indentation**: YAML formatting consistency
- **name-templating**: Task naming conventions
- **package-latest**: Version pinning recommendations
- **Fix Success Rate**: 90-95%

#### Deprecated Features
- **deprecated-module**: Module migration suggestions
- **deprecated-command-syntax**: Syntax modernization
- **Fix Success Rate**: 70-85%

## AI Integration Patterns

### Context-Aware Fixes
- **Ansible Module Knowledge**: Understanding of module parameters and usage
- **Playbook Structure**: Awareness of Ansible playbook organization
- **Role Dependencies**: Understanding of role relationships and variables
- **Security Context**: Infrastructure security best practices

### Fix Validation
- **Syntax Validation**: Post-fix Ansible syntax checking
- **Idempotency Checks**: Ensuring fixes maintain Ansible idempotency
- **Security Review**: Automated security impact assessment of fixes

## Configuration Management

### Project-Specific Configuration
```yaml
# .ansible-lint
exclude_paths:
  - .cache/
  - .github/
  - molecule/
  
skip_list:
  - yaml[line-length]  # Allow longer lines in specific contexts
  - name[casing]       # Project-specific naming conventions

rules:
  command-instead-of-module:
    severity: error
  package-latest:
    severity: warning
```

### Profile Support
- **Basic Profile**: Essential security and syntax checks
- **Strict Profile**: Comprehensive best practices enforcement
- **Security Profile**: Focus on security-related rules only

## Future Extensibility

### Planned Infrastructure Tools
- **Terraform**: HashiCorp Configuration Language (HCL) linting
- **Kubernetes**: YAML manifest validation and best practices
- **Docker**: Dockerfile linting and security scanning
- **CloudFormation**: AWS template validation

### Plugin Architecture Extension
```python
class TerraformLinter(BaseLinter):
    # Future implementation for Terraform support
    pass

class KubernetesLinter(BaseLinter):
    # Future implementation for Kubernetes manifest linting
    pass
```

## Pros and Cons of the Options

### Ansible-only linting support

* Good, because focused implementation with high quality
* Good, because covers most common infrastructure automation use cases
* Good, because mature tooling with established best practices
* Good, because strong AI fix success rates for Ansible patterns
* Bad, because limited to Ansible ecosystem
* Bad, because doesn't cover other infrastructure tools

### Multi-tool infrastructure linting

* Good, because comprehensive infrastructure coverage
* Good, because supports diverse DevOps toolchains
* Bad, because significant implementation complexity
* Bad, because maintenance burden across multiple tools
* Bad, because potential quality dilution across tools

### Generic YAML/configuration linting

* Good, because broad applicability across tools
* Good, because simple implementation
* Bad, because lacks domain-specific knowledge
* Bad, because poor fix quality for infrastructure patterns
* Bad, because misses security and best practice validation

### External service integration

* Good, because no local tool dependencies
* Good, because always up-to-date rule sets
* Bad, because network dependency and latency
* Bad, because limited customization options
* Bad, because potential security concerns with infrastructure code

## Links

* [ADR-0002](0002-ai-integration-architecture.md) - AI integration supporting infrastructure linters
* [ADR-0003](0003-modular-plugin-system.md) - Plugin architecture for infrastructure tools
* [ADR-0004](0004-hybrid-python-javascript-architecture.md) - Architecture supporting diverse tooling
