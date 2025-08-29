# RHEL-based Container Image Support Research

**Date**: 2025-08-24
**Category**: Infrastructure & Enterprise Compatibility
**Status**: In Progress
**Priority**: High - Immediate Decision Needed

## Research Questions

### 1. RHEL Version Compatibility Matrix
**Question**: What are the specific ansible-lint version compatibility differences between RHEL 9 and RHEL 10 base images?

**Priority**: Critical
**Timeline**: Immediate
**Methodology**: 
- Compare ansible-lint versions available in RHEL 9 vs RHEL 10 repositories
- Test ansible-lint functionality across both RHEL versions
- Document version-specific feature differences

**Success Criteria**:
- [ ] Complete version matrix documented
- [ ] Functional testing results for both RHEL versions
- [ ] Performance comparison data

### 2. Enterprise Testing Requirements
**Question**: How should we structure manual testing workflows for ansible-lint across different RHEL versions in enterprise environments?

**Priority**: High
**Timeline**: 1-2 weeks
**Methodology**:
- Analyze current testing workflows in ADR 0007
- Design RHEL-specific testing scenarios
- Validate enterprise compliance requirements

**Success Criteria**:
- [ ] Testing workflow documentation
- [ ] RHEL-specific test cases defined
- [ ] Enterprise validation checklist

### 3. Container Base Image Strategy
**Question**: Should we maintain separate container images for RHEL 9 and RHEL 10, or use a unified approach?

**Priority**: High
**Timeline**: 1 week
**Methodology**:
- Evaluate current RHEL UBI 9 strategy from ADR 0008
- Assess multi-version container maintenance overhead
- Compare unified vs separate image approaches

**Success Criteria**:
- [ ] Container strategy recommendation
- [ ] Maintenance overhead analysis
- [ ] Implementation roadmap

### 4. Ansible-lint Version Management
**Question**: How should we handle ansible-lint version differences between RHEL 9 (older versions) and RHEL 10 (newer versions)?

**Priority**: High
**Timeline**: 1 week
**Methodology**:
- Document current ansible-lint version handling
- Test version-specific rule compatibility
- Design version-aware configuration system

**Success Criteria**:
- [ ] Version management strategy
- [ ] Backward compatibility testing
- [ ] Configuration system design

### 5. Enterprise Deployment Impact
**Question**: What are the implications of supporting both RHEL 9 and RHEL 10 for enterprise customers with mixed environments?

**Priority**: Medium
**Timeline**: 2 weeks
**Methodology**:
- Survey enterprise deployment patterns
- Analyze mixed-environment scenarios
- Document deployment complexity

**Success Criteria**:
- [ ] Enterprise impact assessment
- [ ] Mixed-environment support strategy
- [ ] Customer migration guidance

### 6. Performance and Resource Implications
**Question**: How do RHEL 9 vs RHEL 10 base images compare in terms of container size, startup time, and resource usage?

**Priority**: Medium
**Timeline**: 1 week
**Methodology**:
- Benchmark container metrics across RHEL versions
- Compare resource utilization patterns
- Analyze CI/CD pipeline impact

**Success Criteria**:
- [ ] Performance benchmark results
- [ ] Resource usage comparison
- [ ] CI/CD impact analysis

### 7. Security and Compliance Considerations
**Question**: Are there security or compliance differences between RHEL 9 and RHEL 10 that affect our container strategy?

**Priority**: Medium
**Timeline**: 2 weeks
**Methodology**:
- Review RHEL security feature differences
- Assess compliance requirement changes
- Validate security scanning compatibility

**Success Criteria**:
- [ ] Security feature comparison
- [ ] Compliance requirement analysis
- [ ] Security scanning validation

### 8. Migration and Transition Strategy
**Question**: If we decide to support both RHEL versions, what is the optimal migration path for existing users?

**Priority**: Low
**Timeline**: 3 weeks
**Methodology**:
- Design migration scenarios
- Plan backward compatibility approach
- Create transition documentation

**Success Criteria**:
- [ ] Migration strategy document
- [ ] Backward compatibility plan
- [ ] User transition guide

## Current Context

### Existing Architecture (from ADRs)
- **ADR 0008**: Currently uses RHEL UBI 9 base images for development containers
- **ADR 0007**: Defines ansible-lint integration with version management (enterprise/rhel10/latest)
- **Container Infrastructure**: Containerfile.dev uses RHEL UBI 9, production uses Python slim

### Key Constraints
- Enterprise customers may be on RHEL 9 or RHEL 10
- ansible-lint versions differ significantly between RHEL versions
- Manual testing requirements for enterprise validation
- Container image maintenance overhead considerations

### Research Dependencies
- Current container infrastructure analysis
- Enterprise customer environment survey
- ansible-lint version compatibility testing
- Performance benchmarking setup

## Expected Outcomes

1. **Clear RHEL Support Strategy**: Decision on single vs multi-version support
2. **Version Compatibility Matrix**: Detailed ansible-lint version mapping
3. **Testing Framework**: RHEL-specific testing procedures
4. **Implementation Plan**: Roadmap for RHEL support changes
5. **Enterprise Guidance**: Customer deployment recommendations

## Related ADRs

- [ADR-0007](../adrs/0007-infrastructure-devops-linter-ecosystem.md) - Infrastructure/DevOps Linter Ecosystem Support
- [ADR-0008](../adrs/0008-deployment-environments.md) - Deployment Environments and Runtime Requirements

## Next Steps

- [ ] Begin RHEL version compatibility testing
- [ ] Set up RHEL 9 and RHEL 10 test environments
- [ ] Document current ansible-lint version differences
- [ ] Create enterprise customer survey
- [ ] Benchmark container performance across RHEL versions

## References

- RHEL 9 ansible-lint package information
- RHEL 10 ansible-lint package information
- Enterprise container deployment best practices
- Current aider-lint-fixer container documentation
