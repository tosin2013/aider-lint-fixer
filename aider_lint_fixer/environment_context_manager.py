"""
Environment Context Manager for Project-Specific Linting Configuration
======================================================================

This module provides intelligent environment detection and configuration
for different project types, ensuring proper linting context.

Key Features:
1. Dynamic environment detection (Node.js, Python, Mixed)
2. Project-specific global variable configuration
3. Smart linter environment setup
4. Risk assessment based on environment characteristics
"""

import copy
import json
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class ProjectDetector:
    """Minimal ProjectDetector implementation for environment detection."""
    ProjectInfo = namedtuple('ProjectInfo', ['languages'])

    def detect_project(self, project_path: str):
        # Dummy implementation: detect languages based on file extensions
        languages = set()
        for ext, lang in [('.js', 'javascript'), ('.ts', 'typescript'), ('.py', 'python')]:
            if any(Path(project_path).rglob(f'*{ext}')):
                languages.add(lang)
        return self.ProjectInfo(languages=languages)


class EnvironmentType(Enum):
    """Supported environment types."""
    NODEJS = "nodejs"
    PYTHON = "python"
    BROWSER = "browser"
    REACT_NATIVE = "react-native"
    ELECTRON = "electron"
    WEBWORKER = "webworker"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    env_type: EnvironmentType
    globals: Dict[str, bool]  # Global variables available
    linter_configs: Dict[str, Dict]  # Linter-specific configurations
    risk_factors: List[str]  # Environment-specific risk factors


class EnvironmentContextManager:
    """Manages environment context for different project types."""

    def __init__(self):
        self.project_detector = ProjectDetector()
        self._environment_configs = self._initialize_environment_configs()
    
    def _initialize_environment_configs(self) -> Dict[EnvironmentType, EnvironmentConfig]:
        """Initialize environment configurations."""
        return {
            EnvironmentType.NODEJS: EnvironmentConfig(
                env_type=EnvironmentType.NODEJS,
                globals={
                    "process": True,
                    "global": True,
                    "Buffer": True,
                    "NodeJS": True,
                    "setInterval": True,
                    "setTimeout": True,
                    "clearInterval": True,
                    "clearTimeout": True,
                    "console": True,
                    "__dirname": True,
                    "__filename": True,
                    "require": True,
                    "module": True,
                    "exports": True,
                },
                linter_configs={
                    "eslint": {
                        "env": {
                            "node": True,
                            "es2022": True
                        },
                        "parserOptions": {
                            "ecmaVersion": 2022,
                            "sourceType": "module"
                        }
                    }
                },
                risk_factors=["server_environment", "file_system_access"]
            ),
            
            EnvironmentType.BROWSER: EnvironmentConfig(
                env_type=EnvironmentType.BROWSER,
                globals={
                    "window": True,
                    "document": True,
                    "navigator": True,
                    "location": True,
                    "history": True,
                    "localStorage": True,
                    "sessionStorage": True,
                    "fetch": True,
                    "XMLHttpRequest": True,
                    "URL": True,
                    "URLSearchParams": True,
                    "console": True,
                    "setInterval": True,
                    "setTimeout": True,
                    "clearInterval": True,
                    "clearTimeout": True,
                },
                linter_configs={
                    "eslint": {
                        "env": {
                            "browser": True,
                            "es2022": True
                        }
                    }
                },
                risk_factors=["client_side_security", "xss_potential"]
            ),
            
            EnvironmentType.PYTHON: EnvironmentConfig(
                env_type=EnvironmentType.PYTHON,
                globals={},  # Python doesn't need global config like JS
                linter_configs={
                    "flake8": {
                        "max-line-length": 88,
                        "extend-ignore": ["E203", "W503"]
                    },
                    "mypy": {
                        "python_version": "3.11",
                        "strict": True,
                        "ignore_missing_imports": True
                    }
                },
                risk_factors=["import_side_effects", "dynamic_execution"]
            )
        }
    
    def detect_environment(self, project_path: str) -> EnvironmentType:
        """Detect the primary environment type for a project."""
        project_info = self.project_detector.detect_project(project_path)
        
        # Check for Node.js environment
        if self._is_nodejs_environment(project_path, project_info):
            return EnvironmentType.NODEJS
        
        # Check for browser environment
        if self._is_browser_environment(project_path, project_info):
            return EnvironmentType.BROWSER
        
        # Check for Python environment
        if 'python' in project_info.languages:
            return EnvironmentType.PYTHON
        
        # Check for mixed environment
        if len(project_info.languages) > 1:
            return EnvironmentType.MIXED
        
        return EnvironmentType.UNKNOWN
    
    def _is_nodejs_environment(self, project_path: str, _project_info) -> bool:
        """Check if this is a Node.js environment."""
        # Check for Node.js indicators
        package_json_path = Path(project_path) / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                # Check for Node.js specific dependencies or scripts
                dependencies = {
                    **package_data.get('dependencies', {}),
                    **package_data.get('devDependencies', {})
                }
                
                node_indicators = {
                    '@types/node', 'express', 'fastify', 'koa',
                    'typescript', 'ts-node', 'nodemon'
                }
                
                if any(dep in dependencies for dep in node_indicators):
                    return True
                
                # Check for Node.js scripts
                scripts = package_data.get('scripts', {})
                if any('node' in script for script in scripts.values()):
                    return True
                    
            except (json.JSONDecodeError, IOError):
                pass
        
        # Check for TypeScript config with Node types
        tsconfig_path = Path(project_path) / "tsconfig.json"
        if tsconfig_path.exists():
            try:
                with open(tsconfig_path, 'r') as f:
                    ts_config = json.load(f)
                
                compiler_options = ts_config.get('compilerOptions', {})
                types = compiler_options.get('types', [])
                
                if 'node' in types:
                    return True
                    
            except (json.JSONDecodeError, IOError):
                pass
        
        return False
    
    def _is_browser_environment(self, project_path: str, _project_info) -> bool:
        """Check if this is a browser environment."""
        # Check for browser-specific indicators
        indicators = [
            'index.html', 'webpack.config.js', 'vite.config.js',
            'rollup.config.js', 'package.json'
        ]
        
        for indicator in indicators:
            file_path = Path(project_path) / indicator
            if file_path.exists():
                if indicator == 'package.json':
                    try:
                        with open(file_path, 'r') as f:
                            package_data = json.load(f)
                        
                        dependencies = {
                            **package_data.get('dependencies', {}),
                            **package_data.get('devDependencies', {})
                        }
                        
                        browser_indicators = {
                            'react', 'vue', 'angular', 'webpack',
                            'vite', 'rollup', 'parcel'
                        }
                        
                        if any(dep in dependencies for dep in browser_indicators):
                            return True
                            
                    except (json.JSONDecodeError, IOError):
                        pass
                else:
                    return True
        
        return False
    
    def get_environment_config(self, env_type: EnvironmentType) -> Optional[EnvironmentConfig]:
        """Get configuration for a specific environment type."""
        return self._environment_configs.get(env_type)
    
    def generate_eslint_config(self, project_path: str) -> Dict:
        """Generate ESLint configuration based on detected environment."""
        env_type = self.detect_environment(project_path)
        env_config = self.get_environment_config(env_type)
        
        if not env_config or 'eslint' not in env_config.linter_configs:
            # Default configuration
            return {
                "env": {"es2022": True},
                "parserOptions": {"ecmaVersion": 2022}
            }
        
        eslint_config = copy.deepcopy(env_config.linter_configs['eslint'])
        
        # Add global variables
        if env_config.globals:
            eslint_config['globals'] = env_config.globals
        
        return eslint_config
    
    def assess_environment_risks(self, project_path: str) -> List[str]:
        """Assess environment-specific risks."""
        env_type = self.detect_environment(project_path)
        env_config = self.get_environment_config(env_type)
        
        if not env_config:
            return ["unknown_environment"]
        
        risks = env_config.risk_factors.copy()
        
        # Add project-specific risk assessments
        if self._has_production_indicators(project_path):
            risks.append("production_deployment")
        
        if self._has_security_sensitive_code(project_path):
            risks.append("security_sensitive")
        
        return risks
    
    def _has_production_indicators(self, project_path: str) -> bool:
        """Check for production deployment indicators."""
        production_files = [
            'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
            'deployment', 'k8s', 'helm', '.github/workflows',
            'Procfile', 'app.yaml', 'serverless.yml'
        ]
        
        for indicator in production_files:
            if (Path(project_path) / indicator).exists():
                return True
        
        return False
    
    def _has_security_sensitive_code(self, project_path: str) -> bool:
        """Check for security-sensitive code patterns."""
        # This could be expanded with more sophisticated analysis
        sensitive_patterns = [
            'password', 'secret', 'token', 'api_key',
            'private_key', 'auth', 'crypto'
        ]
        
        # Check for security-sensitive code patterns with performance limits
        MAX_FILES = 1000  # Limit the number of files to process
        MAX_FILE_SIZE = 1024 * 1024  # 1 MB per file
        file_count = 0
        try:
            for file_path in Path(project_path).rglob('*.ts'):
                if file_count >= MAX_FILES:
                    break
                if file_path.is_file():
                    if file_path.stat().st_size > MAX_FILE_SIZE:
                        continue
                    try:
                        content = file_path.read_text().lower()
                    except (IOError, UnicodeDecodeError):
                        continue
                    if any(pattern in content for pattern in sensitive_patterns):
                        return True
                    file_count += 1
        except Exception:
            pass
        
        return False


# Factory function for easy integration
def create_environment_manager() -> EnvironmentContextManager:
    """Create and configure an environment context manager."""
    return EnvironmentContextManager()
