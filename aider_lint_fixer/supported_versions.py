"""
Supported linter versions for aider-lint-fixer.

This module contains the definitive list of supported linter versions
for all integrated linters. Use this for version checking, testing,
and documentation generation.
"""

from typing import Dict, List, NamedTuple


class LinterVersion(NamedTuple):
    """Linter version information."""
    name: str
    tested_version: str
    supported_versions: List[str]
    profile_support: bool
    file_extensions: List[str]
    installation_command: str


# Ansible Linters
ANSIBLE_LINTERS = {
    'ansible-lint': LinterVersion(
        name='ansible-lint',
        tested_version='25.6.1',
        supported_versions=['25.6.1', '25.6', '25.'],
        profile_support=True,
        file_extensions=['.yml', '.yaml'],
        installation_command='pip install ansible-lint==25.6.1'
    )
}

# Python Linters
PYTHON_LINTERS = {
    'flake8': LinterVersion(
        name='flake8',
        tested_version='7.3.0',
        supported_versions=['7.3.0', '7.2', '7.1', '7.0', '6.'],
        profile_support=True,
        file_extensions=['.py'],
        installation_command='pip install flake8==7.3.0'
    ),
    'pylint': LinterVersion(
        name='pylint',
        tested_version='3.3.7',
        supported_versions=['3.3.7', '3.3', '3.2', '3.1', '3.0', '2.'],
        profile_support=True,
        file_extensions=['.py'],
        installation_command='pip install pylint==3.3.7'
    )
}

# Node.js Linters
NODEJS_LINTERS = {
    'eslint': LinterVersion(
        name='ESLint',
        tested_version='8.57.1',
        supported_versions=['8.57.1', '8.57', '8.5', '8.', '7.'],
        profile_support=True,
        file_extensions=['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'],
        installation_command='npm install -g eslint@8.57.1'
    ),
    'jshint': LinterVersion(
        name='JSHint',
        tested_version='2.13.6',
        supported_versions=['2.13.6', '2.13', '2.1', '2.'],
        profile_support=True,
        file_extensions=['.js', '.mjs', '.cjs'],
        installation_command='npm install -g jshint@2.13.6'
    ),
    'prettier': LinterVersion(
        name='Prettier',
        tested_version='3.6.2',
        supported_versions=['3.6.2', '3.6', '3.', '2.'],
        profile_support=True,
        file_extensions=['.js', '.jsx', '.ts', '.tsx', '.json', '.css', '.scss', '.html', '.md', '.yaml', '.yml'],
        installation_command='npm install -g prettier@3.6.2'
    )
}

# All linters combined
ALL_LINTERS = {
    **ANSIBLE_LINTERS,
    **PYTHON_LINTERS,
    **NODEJS_LINTERS
}

# Profile information
PROFILES = {
    'basic': {
        'description': 'Essential checks for development environments',
        'recommended_for': 'Development, CI/CD pipelines',
        'characteristics': 'Fewer warnings, focus on errors'
    },
    'default': {
        'description': 'Balanced checking for most use cases',
        'recommended_for': 'General development, code reviews',
        'characteristics': 'Moderate strictness, good balance'
    },
    'strict': {
        'description': 'Comprehensive checks for production code',
        'recommended_for': 'Production deployments, code quality audits',
        'characteristics': 'All checks enabled, maximum strictness'
    },
    'production': {
        'description': 'Production-ready checks (Ansible-specific)',
        'recommended_for': 'Ansible production deployments',
        'characteristics': 'Comprehensive Ansible best practices'
    }
}


def get_linter_info(linter_name: str) -> LinterVersion:
    """Get version information for a specific linter.
    
    Args:
        linter_name: Name of the linter
        
    Returns:
        LinterVersion object with version information
        
    Raises:
        KeyError: If linter is not supported
    """
    if linter_name not in ALL_LINTERS:
        raise KeyError(f"Linter '{linter_name}' is not supported. "
                      f"Supported linters: {list(ALL_LINTERS.keys())}")
    
    return ALL_LINTERS[linter_name]


def get_supported_linters() -> List[str]:
    """Get list of all supported linter names.
    
    Returns:
        List of supported linter names
    """
    return list(ALL_LINTERS.keys())


def get_linters_by_language(language: str) -> Dict[str, LinterVersion]:
    """Get linters for a specific language.
    
    Args:
        language: Language name ('ansible', 'python', 'nodejs')
        
    Returns:
        Dictionary of linters for the specified language
    """
    language_map = {
        'ansible': ANSIBLE_LINTERS,
        'python': PYTHON_LINTERS,
        'nodejs': NODEJS_LINTERS,
        'javascript': NODEJS_LINTERS,  # Alias
        'typescript': NODEJS_LINTERS   # Alias
    }
    
    return language_map.get(language.lower(), {})


def is_version_supported(linter_name: str, version: str) -> bool:
    """Check if a version is supported for a linter.
    
    Args:
        linter_name: Name of the linter
        version: Version string to check
        
    Returns:
        True if version is supported, False otherwise
    """
    try:
        linter_info = get_linter_info(linter_name)
        
        # Check if version matches any supported pattern
        for pattern in linter_info.supported_versions:
            if version.startswith(pattern):
                return True
        
        return False
    except KeyError:
        return False


def get_installation_commands() -> Dict[str, List[str]]:
    """Get installation commands grouped by language.
    
    Returns:
        Dictionary with installation commands for each language
    """
    return {
        'ansible': [linter.installation_command for linter in ANSIBLE_LINTERS.values()],
        'python': [linter.installation_command for linter in PYTHON_LINTERS.values()],
        'nodejs': [linter.installation_command for linter in NODEJS_LINTERS.values()]
    }


def generate_version_table() -> str:
    """Generate a markdown table of supported versions.
    
    Returns:
        Markdown table string
    """
    table = "| Linter | Tested Version | Supported Versions | Profile Support |\n"
    table += "|--------|----------------|-------------------|------------------|\n"
    
    for linter_name, info in ALL_LINTERS.items():
        profile_support = "✅" if info.profile_support else "❌"
        supported_str = ", ".join(f"`{v}`" for v in info.supported_versions)
        table += f"| **{info.name}** | `{info.tested_version}` | {supported_str} | {profile_support} |\n"
    
    return table


if __name__ == "__main__":
    # Print version information when run directly
    print("🔍 Aider Lint Fixer - Supported Versions")
    print("=" * 50)
    print()
    
    for language, linters in [
        ("Ansible", ANSIBLE_LINTERS),
        ("Python", PYTHON_LINTERS),
        ("Node.js", NODEJS_LINTERS)
    ]:
        print(f"📋 {language} Linters:")
        for linter_name, info in linters.items():
            print(f"  • {info.name}: {info.tested_version} (supports: {', '.join(info.supported_versions)})")
        print()
    
    print("📚 Installation Commands:")
    commands = get_installation_commands()
    for language, cmds in commands.items():
        print(f"  {language.title()}:")
        for cmd in cmds:
            print(f"    {cmd}")
        print()
