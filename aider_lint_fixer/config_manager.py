"""
Configuration Manager Module

This module handles loading and managing configuration files for the aider lint fixer.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""

    provider: str = "deepseek"
    model: str = "deepseek/deepseek-chat"
    fallback_providers: List[str] = field(default_factory=lambda: ["openrouter", "ollama"])
    api_key: Optional[str] = None
    api_base: Optional[str] = None


@dataclass
class LinterConfig:
    """Configuration for linters."""

    auto_detect: bool = True
    enabled: List[str] = field(
        default_factory=lambda: [
            "flake8",
            "pylint",
            "black",
            "isort",
            "mypy",
            "eslint",
            "prettier",
            "tslint",
            "golint",
            "gofmt",
            "govet",
            "rustfmt",
            "clippy",
        ]
    )


@dataclass
class AiderConfig:
    """Configuration for aider integration."""

    auto_commit: bool = False
    backup_files: bool = True
    max_retries: int = 3
    context_window: int = 8192


@dataclass
class ProjectConfig:
    """Configuration for project settings."""

    exclude_patterns: List[str] = field(
        default_factory=lambda: [
            "*.min.js",
            "*.min.css",
            "node_modules/",
            "__pycache__/",
            ".git/",
            ".venv/",
            "venv/",
            "build/",
            "dist/",
            "target/",
        ]
    )
    include_patterns: List[str] = field(
        default_factory=lambda: [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.go",
            "*.rs",
            "*.java",
            "*.c",
            "*.cpp",
            "*.h",
            "*.hpp",
        ]
    )


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    file: str = "aider-lint-fixer.log"
    max_size: str = "10MB"
    backup_count: int = 5


@dataclass
class Config:
    """Main configuration class."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    linters: LinterConfig = field(default_factory=LinterConfig)
    aider: AiderConfig = field(default_factory=AiderConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigManager:
    """Manages configuration loading and merging."""

    CONFIG_FILENAMES = [
        ".aider-lint-fixer.yml",
        ".aider-lint-fixer.yaml",
        "aider-lint-fixer.yml",
        "aider-lint-fixer.yaml",
    ]

    def __init__(self):
        """Initialize the configuration manager."""
        self.config = Config()

    def load_config(self, project_path: Optional[str] = None) -> Config:
        """Load configuration from various sources.

        Args:
            project_path: Path to the project directory

        Returns:
            Merged configuration object
        """
        # Start with default configuration
        config_dict = self._config_to_dict(self.config)

        # Load global configuration from home directory
        home_config = self._load_config_file(Path.home())
        if home_config:
            config_dict = self._merge_configs(config_dict, home_config)
            logger.debug("Loaded global configuration from home directory")

        # Load project-specific configuration
        if project_path:
            project_config = self._load_config_file(Path(project_path))
            if project_config:
                config_dict = self._merge_configs(config_dict, project_config)
                logger.debug(f"Loaded project configuration from {project_path}")

        # Override with environment variables
        env_config = self._load_env_config()
        if env_config:
            config_dict = self._merge_configs(config_dict, env_config)
            logger.debug("Applied environment variable overrides")

        # Convert back to Config object
        self.config = self._dict_to_config(config_dict)

        return self.config

    def _load_config_file(self, directory: Path) -> Optional[Dict[str, Any]]:
        """Load configuration file from a directory.

        Args:
            directory: Directory to search for configuration files

        Returns:
            Configuration dictionary or None if no file found
        """
        for filename in self.CONFIG_FILENAMES:
            config_path = directory / filename
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = yaml.safe_load(f)
                        if config_data:
                            logger.info(f"Loaded configuration from: {config_path}")
                            return config_data
                except Exception as e:
                    logger.warning(f"Failed to load config file {config_path}: {e}")

        return None

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Configuration dictionary with environment overrides
        """
        env_config = {}

        # LLM configuration
        if os.getenv("AIDER_LLM_PROVIDER"):
            env_config.setdefault("llm", {})["provider"] = os.getenv("AIDER_LLM_PROVIDER")

        if os.getenv("AIDER_LLM_MODEL"):
            env_config.setdefault("llm", {})["model"] = os.getenv("AIDER_LLM_MODEL")

        # API base URLs (but not API keys - those are handled by get_api_key_for_provider)
        if os.getenv("OLLAMA_API_BASE"):
            env_config.setdefault("llm", {})["api_base"] = os.getenv("OLLAMA_API_BASE")

        # Aider configuration
        if os.getenv("AIDER_AUTO_COMMIT"):
            env_config.setdefault("aider", {})["auto_commit"] = (
                os.getenv("AIDER_AUTO_COMMIT").lower() == "true"
            )

        if os.getenv("AIDER_MAX_RETRIES"):
            try:
                env_config.setdefault("aider", {})["max_retries"] = int(
                    os.getenv("AIDER_MAX_RETRIES")
                )
            except ValueError:
                logger.warning("Invalid AIDER_MAX_RETRIES value, using default")

        # Logging configuration
        if os.getenv("AIDER_LOG_LEVEL"):
            env_config.setdefault("logging", {})["level"] = os.getenv("AIDER_LOG_LEVEL")

        return env_config

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config object to dictionary.

        Args:
            config: Config object

        Returns:
            Configuration dictionary
        """
        return {
            "llm": {
                "provider": config.llm.provider,
                "model": config.llm.model,
                "fallback_providers": config.llm.fallback_providers,
                "api_key": config.llm.api_key,
                "api_base": config.llm.api_base,
            },
            "linters": {
                "auto_detect": config.linters.auto_detect,
                "enabled": config.linters.enabled,
            },
            "aider": {
                "auto_commit": config.aider.auto_commit,
                "backup_files": config.aider.backup_files,
                "max_retries": config.aider.max_retries,
                "context_window": config.aider.context_window,
            },
            "project": {
                "exclude_patterns": config.project.exclude_patterns,
                "include_patterns": config.project.include_patterns,
            },
            "logging": {
                "level": config.logging.level,
                "file": config.logging.file,
                "max_size": config.logging.max_size,
                "backup_count": config.logging.backup_count,
            },
        }

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> Config:
        """Convert dictionary to Config object.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Config object
        """
        config = Config()

        # LLM configuration
        if "llm" in config_dict:
            llm_dict = config_dict["llm"]
            config.llm = LLMConfig(
                provider=llm_dict.get("provider", config.llm.provider),
                model=llm_dict.get("model", config.llm.model),
                fallback_providers=llm_dict.get(
                    "fallback_providers", config.llm.fallback_providers
                ),
                api_key=llm_dict.get("api_key", config.llm.api_key),
                api_base=llm_dict.get("api_base", config.llm.api_base),
            )

        # Linter configuration
        if "linters" in config_dict:
            linters_dict = config_dict["linters"]
            config.linters = LinterConfig(
                auto_detect=linters_dict.get("auto_detect", config.linters.auto_detect),
                enabled=linters_dict.get("enabled", config.linters.enabled),
            )

        # Aider configuration
        if "aider" in config_dict:
            aider_dict = config_dict["aider"]
            config.aider = AiderConfig(
                auto_commit=aider_dict.get("auto_commit", config.aider.auto_commit),
                backup_files=aider_dict.get("backup_files", config.aider.backup_files),
                max_retries=aider_dict.get("max_retries", config.aider.max_retries),
                context_window=aider_dict.get("context_window", config.aider.context_window),
            )

        # Project configuration
        if "project" in config_dict:
            project_dict = config_dict["project"]
            config.project = ProjectConfig(
                exclude_patterns=project_dict.get(
                    "exclude_patterns", config.project.exclude_patterns
                ),
                include_patterns=project_dict.get(
                    "include_patterns", config.project.include_patterns
                ),
            )

        # Logging configuration
        if "logging" in config_dict:
            logging_dict = config_dict["logging"]
            config.logging = LoggingConfig(
                level=logging_dict.get("level", config.logging.level),
                file=logging_dict.get("file", config.logging.file),
                max_size=logging_dict.get("max_size", config.logging.max_size),
                backup_count=logging_dict.get("backup_count", config.logging.backup_count),
            )

        return config

    def save_config(self, config_path: str, config: Optional[Config] = None) -> None:
        """Save configuration to a file.

        Args:
            config_path: Path to save the configuration file
            config: Configuration object to save (uses current config if None)
        """
        if config is None:
            config = self.config

        config_dict = self._config_to_dict(config)

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to: {config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            raise

    def get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider.

        Args:
            provider: LLM provider name

        Returns:
            API key or None if not found
        """
        # Check configuration first
        if self.config.llm.api_key:
            return self.config.llm.api_key

        # Check environment variables
        env_vars = {
            "deepseek": "DEEPSEEK_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "ollama": "OLLAMA_API_KEY",
            "openai": "OPENAI_API_KEY",
        }

        if provider in env_vars:
            env_var = env_vars[provider]
            api_key = os.getenv(env_var)
            if not api_key:
                logger.warning(
                    f"No API key found for {provider}. Please set {env_var} environment variable."
                )
            return api_key

        logger.warning(f"Unsupported provider: {provider}")
        return None
