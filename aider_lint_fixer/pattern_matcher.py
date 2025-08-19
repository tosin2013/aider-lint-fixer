"""
Language-Specific Pattern Matching System

This module provides intelligent pattern matching for lint errors using
Aho-Corasick algorithm with language-specific automatons and machine learning
for adaptive pattern recognition.
"""

import json
import logging
import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import ahocorasick

    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False
    logging.warning("pyahocorasick not available, falling back to regex patterns")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, ML learning disabled")

logger = logging.getLogger(__name__)


@dataclass
class ErrorPattern:
    """Represents a pattern for matching lint errors."""

    pattern: str
    error_type: str
    language: str
    linter: str
    fixable: bool
    confidence: float = 1.0
    description: str = ""


@dataclass
class PatternMatchResult:
    """Result of pattern matching operation."""

    fixable: bool
    confidence: float
    method: str  # "pattern_match", "ml_prediction", "fallback"
    error_type: str
    matched_pattern: Optional[str] = None


class LanguagePatternMatcher:
    """Fast pattern matching using Aho-Corasick algorithm per language."""

    def __init__(self):
        self.matchers = {}  # One automaton per language
        self.patterns_by_language = {}
        self._build_language_patterns()

    def _build_language_patterns(self):
        """Build language-specific pattern automatons."""
        patterns = {
            "python": [
                ErrorPattern(
                    "line too long",
                    "formatting",
                    "python",
                    "flake8",
                    True,
                    0.95,
                    "Line length exceeds maximum allowed",
                ),
                ErrorPattern(
                    "undefined name",
                    "import",
                    "python",
                    "flake8",
                    False,
                    0.9,
                    "Variable or function not defined",
                ),
                ErrorPattern(
                    "imported but unused",
                    "unused",
                    "python",
                    "flake8",
                    True,
                    0.98,
                    "Import statement not used",
                ),
                ErrorPattern(
                    "missing docstring",
                    "style",
                    "python",
                    "pylint",
                    True,
                    0.8,
                    "Function/class missing documentation",
                ),
                ErrorPattern(
                    "would reformat",
                    "formatting",
                    "python",
                    "black",
                    True,
                    1.0,
                    "Code formatting required",
                ),
                ErrorPattern(
                    "Imports are incorrectly sorted",
                    "import",
                    "python",
                    "isort",
                    True,
                    0.95,
                    "Import statements need sorting",
                ),
                ErrorPattern(
                    "error: ",
                    "type",
                    "python",
                    "mypy",
                    False,
                    0.7,
                    "Type checking error",
                ),
            ],
            "javascript": [
                ErrorPattern(
                    "Missing semicolon",
                    "formatting",
                    "javascript",
                    "eslint",
                    True,
                    0.95,
                    "Semicolon required",
                ),
                ErrorPattern(
                    "is defined but never used",
                    "unused",
                    "javascript",
                    "eslint",
                    True,
                    0.9,
                    "Unused variable declaration",
                ),
                ErrorPattern(
                    "Unexpected token",
                    "syntax",
                    "javascript",
                    "eslint",
                    False,
                    0.7,
                    "Syntax error in code",
                ),
                ErrorPattern(
                    "Replace",
                    "formatting",
                    "javascript",
                    "prettier",
                    True,
                    1.0,
                    "Code formatting required",
                ),
                ErrorPattern(
                    "Expected",
                    "syntax",
                    "javascript",
                    "jshint",
                    False,
                    0.6,
                    "Syntax expectation not met",
                ),
            ],
            "typescript": [
                ErrorPattern(
                    "Missing semicolon",
                    "formatting",
                    "typescript",
                    "eslint",
                    True,
                    0.95,
                    "Semicolon required",
                ),
                ErrorPattern(
                    "is defined but never used",
                    "unused",
                    "typescript",
                    "eslint",
                    True,
                    0.9,
                    "Unused variable declaration",
                ),
                ErrorPattern(
                    "Type",
                    "type",
                    "typescript",
                    "eslint",
                    False,
                    0.8,
                    "TypeScript type error",
                ),
                ErrorPattern(
                    "Replace",
                    "formatting",
                    "typescript",
                    "prettier",
                    True,
                    1.0,
                    "Code formatting required",
                ),
            ],
            "ansible": [
                ErrorPattern(
                    "expected token ','",
                    "jinja_syntax",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.9,
                    "Jinja2 template syntax error",
                ),
                ErrorPattern(
                    "got '",
                    "jinja_variable",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.85,
                    "Jinja2 variable error",
                ),
                ErrorPattern(
                    "unexpected end of template",
                    "jinja_template",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.8,
                    "Jinja2 template incomplete",
                ),
                ErrorPattern(
                    "yaml[key-duplicates]",
                    "yaml_structure",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.95,
                    "Duplicate YAML keys",
                ),
                ErrorPattern(
                    "All plays should be named",
                    "style",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.9,
                    "Play naming convention",
                ),
                ErrorPattern(
                    "name[play]",
                    "style",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.9,
                    "Play should have a name",
                ),
                # YAML formatting patterns
                ErrorPattern(
                    "yaml[line-length]",
                    "formatting",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.95,
                    "YAML line too long",
                ),
                ErrorPattern(
                    "Line too long",
                    "formatting",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.95,
                    "Line length exceeds maximum",
                ),
                ErrorPattern(
                    "yaml[comments]",
                    "formatting",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.9,
                    "YAML comment formatting",
                ),
                ErrorPattern(
                    "Missing starting space in comment",
                    "formatting",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.9,
                    "Comment spacing issue",
                ),
                ErrorPattern(
                    "yaml[document-start]",
                    "formatting",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.8,
                    "YAML document start formatting",
                ),
                ErrorPattern(
                    "jinja[spacing]",
                    "formatting",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.95,
                    "Jinja2 template spacing",
                ),
                ErrorPattern(
                    "risky-file-permissions",
                    "security",
                    "ansible",
                    "ansible-lint",
                    True,
                    0.85,
                    "File permissions security issue",
                ),
            ],
            "go": [
                ErrorPattern(
                    "should have comment",
                    "style",
                    "go",
                    "golint",
                    True,
                    0.8,
                    "Missing comment for exported item",
                ),
                ErrorPattern(
                    "not formatted with gofmt",
                    "formatting",
                    "go",
                    "gofmt",
                    True,
                    1.0,
                    "Code formatting required",
                ),
                ErrorPattern(
                    "unreachable code",
                    "logic",
                    "go",
                    "govet",
                    False,
                    0.9,
                    "Dead code detected",
                ),
                ErrorPattern("print", "logic", "go", "govet", False, 0.8, "Printf format issue"),
            ],
            "rust": [
                ErrorPattern(
                    "not formatted",
                    "formatting",
                    "rust",
                    "rustfmt",
                    True,
                    1.0,
                    "Code formatting required",
                ),
                ErrorPattern(
                    "this could be written as",
                    "style",
                    "rust",
                    "clippy",
                    True,
                    0.85,
                    "Code style improvement suggestion",
                ),
                ErrorPattern(
                    "unused variable",
                    "unused",
                    "rust",
                    "clippy",
                    True,
                    0.9,
                    "Variable declared but not used",
                ),
                ErrorPattern(
                    "unnecessary",
                    "style",
                    "rust",
                    "clippy",
                    True,
                    0.8,
                    "Unnecessary code construct",
                ),
            ],
        }

        self.patterns_by_language = patterns

        if AHOCORASICK_AVAILABLE:
            self._build_ahocorasick_automatons(patterns)
        else:
            logger.warning("Aho-Corasick not available, using fallback pattern matching")

    def _build_ahocorasick_automatons(self, patterns: Dict[str, List[ErrorPattern]]):
        """Build Aho-Corasick automatons for each language."""
        for language, error_patterns in patterns.items():
            automaton = ahocorasick.Automaton()
            for pattern in error_patterns:
                automaton.add_word(pattern.pattern.lower(), pattern)
            automaton.make_automaton()
            self.matchers[language] = automaton
            logger.debug(f"Built automaton for {language} with {len(error_patterns)} patterns")

    def find_patterns(self, error_message: str, language: str) -> List[ErrorPattern]:
        """Find matching patterns for an error message."""
        if not error_message:
            return []

        error_lower = (error_message or "").lower()

        if AHOCORASICK_AVAILABLE and language in self.matchers:
            # Fast Aho-Corasick matching
            matches = []
            for _, pattern in self.matchers[language].iter(error_lower):
                matches.append(pattern)
            return matches
        else:
            # Fallback to simple string matching
            return self._fallback_pattern_matching(error_lower, language)

    def _fallback_pattern_matching(self, error_message: str, language: str) -> List[ErrorPattern]:
        """Fallback pattern matching when Aho-Corasick is not available."""
        matches = []
        if language in self.patterns_by_language:
            for pattern in self.patterns_by_language[language]:
                if pattern.pattern.lower() in error_message:
                    matches.append(pattern)
        return matches

    def get_best_match(self, error_message: str, language: str) -> Optional[ErrorPattern]:
        """Get the best matching pattern for an error message."""
        patterns = self.find_patterns(error_message, language)
        if not patterns:
            return None

        # Return pattern with highest confidence
        return max(patterns, key=lambda p: p.confidence)

    def add_learned_pattern(
        self,
        pattern: str,
        error_type: str,
        language: str,
        linter: str,
        fixable: bool,
        confidence: float = 0.7,
    ):
        """Add a new learned pattern to the matcher."""
        new_pattern = ErrorPattern(
            pattern=pattern,
            error_type=error_type,
            language=language,
            linter=linter,
            fixable=fixable,
            confidence=confidence,
            description="Learned pattern",
        )

        # Add to patterns list
        if language not in self.patterns_by_language:
            self.patterns_by_language[language] = []
        self.patterns_by_language[language].append(new_pattern)

        # Rebuild automaton for this language
        if AHOCORASICK_AVAILABLE:
            automaton = ahocorasick.Automaton()
            for p in self.patterns_by_language[language]:
                automaton.add_word(p.pattern.lower(), p)
            automaton.make_automaton()
            self.matchers[language] = automaton

        logger.info(f"Added learned pattern for {language}: {pattern}")


@dataclass
class ErrorFeatures:
    """Comprehensive feature extraction for error messages."""

    # Rule-based features
    rule_category: str = ""  # "yaml", "jinja", "style", "syntax"
    rule_subcategory: str = ""  # "line-length", "spacing", "naming"
    rule_id: str = ""  # Full rule ID like "yaml[line-length]"

    # Message features
    contains_suggestion: bool = False  # Does message suggest a fix?
    has_before_after: bool = False  # Shows before/after examples?
    mentions_formatting: bool = False  # Contains formatting keywords?
    has_line_numbers: bool = False  # Contains line/column references

    # Context features
    file_type: str = ""  # .yml, .py, .js
    linter_name: str = ""  # ansible-lint, eslint, flake8
    project_context: str = ""  # ansible, react, django, etc.

    # Complexity indicators
    requires_logic_change: bool = False  # vs simple formatting
    affects_multiple_lines: bool = False  # Single vs multi-line fix
    needs_domain_knowledge: bool = False  # Business logic understanding

    # Fixability hints
    auto_fixable_keywords: List[str] = field(default_factory=list)
    manual_only_keywords: List[str] = field(default_factory=list)


class RuleKnowledgeBase:
    """Pre-loaded knowledge about linter rules and their fixability."""

    def __init__(self):
        self.rule_database = self._build_rule_database()
        self._load_scraped_rules()  # Load web-scraped data if available

    def _build_rule_database(self) -> Dict[str, Dict]:
        """Build comprehensive rule database from known linter documentation."""
        return {
            # Ansible-lint rules
            "ansible-lint": {
                "yaml[line-length]": {
                    "category": "formatting",
                    "auto_fixable": True,
                    "complexity": "trivial",
                    "description": "Line exceeds maximum length",
                    "fix_strategy": "line_wrapping",
                },
                "yaml[comments]": {
                    "category": "formatting",
                    "auto_fixable": True,
                    "complexity": "trivial",
                    "description": "Comment formatting issues",
                    "fix_strategy": "spacing_adjustment",
                },
                "yaml[document-start]": {
                    "category": "formatting",
                    "auto_fixable": True,
                    "complexity": "simple",
                    "description": "Document start marker issues",
                    "fix_strategy": "marker_adjustment",
                },
                "jinja[spacing]": {
                    "category": "formatting",
                    "auto_fixable": True,
                    "complexity": "trivial",
                    "description": "Jinja2 template spacing",
                    "fix_strategy": "whitespace_cleanup",
                },
                "name[play]": {
                    "category": "style",
                    "auto_fixable": False,
                    "complexity": "manual",
                    "description": "Play should have a name",
                    "fix_strategy": "requires_human_input",
                },
            },
            # ESLint rules
            "eslint": {
                "semi": {
                    "category": "formatting",
                    "auto_fixable": True,
                    "complexity": "trivial",
                    "description": "Missing semicolon",
                    "fix_strategy": "punctuation_addition",
                },
                "no-unused-vars": {
                    "category": "unused",
                    "auto_fixable": True,
                    "complexity": "simple",
                    "description": "Unused variable",
                    "fix_strategy": "removal",
                },
            },
            # Flake8 rules
            "flake8": {
                "E501": {
                    "category": "formatting",
                    "auto_fixable": True,
                    "complexity": "simple",
                    "description": "Line too long",
                    "fix_strategy": "line_wrapping",
                },
                "F401": {
                    "category": "unused",
                    "auto_fixable": True,
                    "complexity": "trivial",
                    "description": "Unused import",
                    "fix_strategy": "removal",
                },
            },
        }

    def get_rule_info(self, linter: str, rule_id: str) -> Optional[Dict]:
        """Get information about a specific rule."""
        return self.rule_database.get(linter, {}).get(rule_id)

    def is_known_auto_fixable(self, linter: str, rule_id: str) -> Optional[bool]:
        """Check if a rule is known to be auto-fixable."""
        rule_info = self.get_rule_info(linter, rule_id)
        return rule_info.get("auto_fixable") if rule_info else None

    def _load_scraped_rules(self):
        """Load web-scraped rules from cache if available."""
        try:
            import json
            from pathlib import Path

            # Check for scraped rules in multiple locations
            cache_locations = [
                Path(".aider-lint-cache") / "scraped_rules.json",
                Path("scraped_ansible_rules.json"),  # Our test file
                Path(".") / "scraped_rules.json",
            ]

            scraped_file = None
            for cache_file in cache_locations:
                if cache_file.exists():
                    scraped_file = cache_file
                    break

            if scraped_file:
                with open(scraped_file, "r", encoding="utf-8") as f:
                    scraped_rules = json.load(f)

                # Merge scraped rules with hardcoded rules
                rules_added = 0
                for linter, rules in scraped_rules.items():
                    if linter not in self.rule_database:
                        self.rule_database[linter] = {}

                    # Add scraped rules, prioritizing scraped data over hardcoded
                    for rule_id, rule_info in rules.items():
                        # Skip invalid rules (like javascript:void(0))
                        if rule_id.startswith(("javascript:", ".", "#")):
                            continue

                        self.rule_database[linter][rule_id] = rule_info
                        rules_added += 1

                logger.info(f"Loaded {rules_added} scraped rules from {scraped_file}")
            else:
                logger.debug("No scraped rules file found")
                # Try to create scraped rules automatically if dependencies are available
                self._auto_create_scraped_rules()
        except Exception as e:
            logger.debug(f"Could not load scraped rules: {e}")

    def _auto_create_scraped_rules(self):
        """Automatically create scraped rules if dependencies are available."""
        try:
            # Check if web scraping dependencies are available
            import bs4  # noqa: F401
            import requests  # noqa: F401

            logger.info("Creating scraped rules automatically...")

            # Import and run rule scraper
            from .rule_scraper import scrape_and_update_knowledge_base

            # Create scraped rules in background
            scraped_rules = scrape_and_update_knowledge_base()

            if scraped_rules:
                # Reload the rules we just created
                scraped_file = self.cache_dir / "scraped_rules.json"
                if scraped_file.exists():
                    self._load_scraped_rules()
                    logger.info(
                        f"Successfully created and loaded {len(scraped_rules)} scraped rules"
                    )

        except ImportError:
            logger.debug("Web scraping dependencies not available, skipping auto-creation")
        except Exception as e:
            logger.debug(f"Could not auto-create scraped rules: {e}")


class SmartErrorClassifier:
    """Intelligent error classification using pattern matching, ML, and rule knowledge."""

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path(".aider-lint-cache")

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

        # Core components
        self.pattern_matcher = LanguagePatternMatcher()
        self.cache_manager = PatternCacheManager(self.cache_dir)
        self.rule_knowledge = RuleKnowledgeBase()

        # ML components (if available)
        self.classifiers = {}
        self.vectorizers = {}

        if SKLEARN_AVAILABLE:
            self._load_models()
            # Perform periodic cleanup
            self._periodic_cleanup()
        else:
            logger.warning(
                "scikit-learn not available, ML learning disabled. "
                "Install with: pip install aider-lint-fixer[learning]"
            )

    def extract_features(
        self, error_message: str, language: str, linter: str, rule_id: str = ""
    ) -> ErrorFeatures:
        """Extract comprehensive features from an error message."""
        features = ErrorFeatures()

        # Basic info
        features.linter_name = linter
        features.rule_id = rule_id

        # Parse rule category from rule_id
        if rule_id:
            if "[" in rule_id and "]" in rule_id:
                # Format like "yaml[line-length]"
                parts = rule_id.split("[")
                features.rule_category = parts[0]
                if len(parts) > 1:
                    features.rule_subcategory = parts[1].rstrip("]")
            else:
                # Simple rule ID
                features.rule_category = rule_id

        # Message analysis
        message_lower = error_message.lower()

        # Check for suggestions and examples
        features.contains_suggestion = any(
            word in message_lower for word in ["should", "try", "use", "consider", "->", "replace"]
        )
        features.has_before_after = "->" in error_message or "expected" in message_lower
        features.has_line_numbers = any(
            word in message_lower for word in ["line", "column", "position"]
        )

        # Formatting indicators
        formatting_keywords = [
            "spacing",
            "indent",
            "format",
            "length",
            "comment",
            "style",
        ]
        features.mentions_formatting = any(word in message_lower for word in formatting_keywords)

        # Complexity analysis
        manual_keywords = ["logic", "business", "design", "architecture"]
        # For Ansible, "name" in naming rules is not domain knowledge - it's style
        if linter == "ansible-lint":
            # Don't treat Ansible naming rules as requiring domain knowledge
            if not ("should be named" in message_lower or "tasks should be named" in message_lower):
                manual_keywords.append("name")
            # Module parameter errors require domain knowledge
            if "unsupported parameters" in message_lower or "args[module]" in message_lower:
                features.needs_domain_knowledge = True
                return features
        else:
            manual_keywords.append("name")
        features.needs_domain_knowledge = any(word in message_lower for word in manual_keywords)

        syntax_keywords = ["syntax", "parse", "invalid", "unexpected", "missing"]
        features.requires_logic_change = any(word in message_lower for word in syntax_keywords)

        # Auto-fixable hints
        auto_fixable_hints = [
            "too long",
            "missing space",
            "extra space",
            "semicolon",
            "unused",
            "import",
            "trailing",
            "whitespace",
        ]

        # Add Ansible-specific auto-fixable patterns
        if linter == "ansible-lint":
            auto_fixable_hints.extend(
                [
                    "should be named",
                    "tasks should be named",
                    "plays should be named",
                    "use command module",
                    "use structured parameters",
                    "start task names",
                    "indentation",
                    "wrong indentation",
                    "use true/false",
                    "instead of yes/no",
                    "boolean values",
                    "trailing spaces",  # Real ansible-lint message
                    "trailing whitespace",
                    "forbidden document start",  # Real ansible-lint message
                    "duplication of key",  # Real ansible-lint message
                    "duplicate key",
                ]
            )

        features.auto_fixable_keywords = [
            hint for hint in auto_fixable_hints if hint in message_lower
        ]

        # Manual-only hints (but exclude common Ansible naming rules)
        manual_hints = ["add description", "complex logic", "business rule"]
        # Don't treat Ansible naming rules as manual-only
        if linter != "ansible-lint":
            manual_hints.extend(["should be named", "missing name"])
        features.manual_only_keywords = [hint for hint in manual_hints if hint in message_lower]

        return features

    def classify_error(
        self, error_message: str, language: str, linter: str, rule_id: str = ""
    ) -> PatternMatchResult:
        """Classify an error message to determine if it's fixable using comprehensive analysis."""
        if not error_message or not language:
            return PatternMatchResult(
                fixable=False, confidence=0.1, method="fallback", error_type="unknown"
            )

        # Extract comprehensive features
        features = self.extract_features(error_message, language, linter, rule_id)

        # Priority 1: Rule knowledge base (highest confidence)
        if rule_id:
            known_fixable = self.rule_knowledge.is_known_auto_fixable(linter, rule_id)
            if known_fixable is not None:
                return PatternMatchResult(
                    fixable=known_fixable,
                    confidence=0.95,
                    method="rule_knowledge",
                    error_type=features.rule_category or "known_rule",
                    matched_pattern=rule_id,
                )

        # Priority 2: Pattern matching (high confidence)
        best_pattern = self.pattern_matcher.get_best_match(error_message, language)
        if best_pattern and best_pattern.confidence > 0.7:
            return PatternMatchResult(
                fixable=best_pattern.fixable,
                confidence=best_pattern.confidence,
                method="pattern_match",
                error_type=best_pattern.error_type,
                matched_pattern=best_pattern.pattern,
            )

        # Priority 3: Feature-based analysis (medium confidence)
        feature_result = self._classify_by_features(features)
        if feature_result.confidence > 0.6:
            return feature_result

        # ML path: Learned patterns (if available)
        if SKLEARN_AVAILABLE and language in self.classifiers:
            try:
                X = self.vectorizers[language].transform([error_message])
                prediction = self.classifiers[language].predict(X)[0]
                probabilities = self.classifiers[language].predict_proba(X)[0]
                confidence = probabilities.max()

                return PatternMatchResult(
                    fixable=prediction == "fixable",
                    confidence=confidence,
                    method="ml_prediction",
                    error_type="learned",
                )
            except Exception as e:
                logger.debug(f"ML prediction failed for {language}: {e}")

        # Fallback: Conservative approach based on linter
        fallback_fixable = self._get_fallback_fixability(linter, error_message)
        return PatternMatchResult(
            fixable=fallback_fixable,
            confidence=0.3,
            method="fallback",
            error_type="unknown",
        )

    def _get_fallback_fixability(self, linter: str, error_message: str) -> bool:
        """Conservative fallback for determining fixability."""
        # Formatters are usually always fixable
        formatting_linters = {"black", "prettier", "rustfmt", "gofmt", "isort"}
        if linter in formatting_linters:
            return True

        # Syntax errors are usually not fixable
        syntax_keywords = [
            "syntax error",
            "unexpected token",
            "parse error",
            "invalid syntax",
        ]
        error_lower = (error_message or "").lower()
        if any(keyword in error_lower for keyword in syntax_keywords):
            return False

        # Ansible-lint specific patterns
        if linter == "ansible-lint":
            ansible_fixable = [
                "should be named",
                "all tasks should be named",
                "all plays should be named",
                "use command module instead",
                "use structured parameters",
                "start task names with",
                "line too long",
                "trailing whitespace",
                "trailing spaces",  # Real ansible-lint message
                "wrong indentation",
                "use true/false instead",
                "missing document start",
                "forbidden document start",  # Real ansible-lint message
                "duplication of key",  # Real ansible-lint message
                "duplicate key",
            ]
            if any(pattern in error_lower for pattern in ansible_fixable):
                return True

        # Style issues are often fixable
        style_keywords = ["should", "missing", "unused", "line too long", "comment"]
        if any(keyword in error_lower for keyword in style_keywords):
            return True

        # Default to not fixable for unknown patterns
        return False

    def _classify_by_features(self, features: ErrorFeatures) -> PatternMatchResult:
        """Classify error based on extracted features."""
        confidence = 0.5
        fixable = False

        # Strong indicators for fixability
        if features.auto_fixable_keywords:
            fixable = True
            confidence += 0.2

        if features.mentions_formatting:
            fixable = True
            confidence += 0.15

        if features.rule_category in ["formatting", "style", "unused"]:
            fixable = True
            confidence += 0.1

        # Strong indicators against fixability
        if features.manual_only_keywords:
            fixable = False
            confidence += 0.2

        if features.needs_domain_knowledge:
            fixable = False
            confidence += 0.15

        if features.rule_category in ["syntax", "logic", "security"]:
            fixable = False
            confidence += 0.1

        # Adjust confidence based on suggestion quality
        if features.contains_suggestion and features.has_before_after:
            confidence += 0.1

        return PatternMatchResult(
            fixable=fixable,
            confidence=min(confidence, 0.9),  # Cap at 0.9
            method="feature_analysis",
            error_type=features.rule_category or "feature_based",
        )

    def learn_from_fix(self, error_message: str, language: str, linter: str, fix_successful: bool):
        """Learn from fix attempts to improve future predictions."""
        if not SKLEARN_AVAILABLE:
            return

        # Store training data
        training_file = self.cache_dir / f"{language}_training.json"

        training_data = []
        if training_file.exists():
            try:
                with open(training_file, "r", encoding="utf-8") as f:
                    training_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load training data for {language}: {e}")
                training_data = []

        training_data.append(
            {
                "message": error_message,
                "language": language,
                "linter": linter,
                "fixable": fix_successful,
                "timestamp": time.time(),
            }
        )

        # Keep only recent data (last 1000 examples per language)
        training_data = training_data[-1000:]

        try:
            with open(training_file, "w", encoding="utf-8") as f:
                json.dump(training_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save training data for {language}: {e}")
            return

        # Retrain if we have enough data (lowered threshold for faster learning)
        if len(training_data) >= 5:  # Minimum for meaningful training (reduced from 20)
            self._retrain_language_model(language, training_data)

        # Also try to extract patterns for fast matching
        if fix_successful:
            self._extract_and_add_pattern(error_message, language, linter)

        # Immediate learning: update confidence for similar patterns
        self._update_pattern_confidence(error_message, language, linter, fix_successful)

    def _extract_and_add_pattern(self, error_message: str, language: str, linter: str):
        """Extract key phrases from successful fixes and add as patterns."""
        # Simple pattern extraction - look for common error phrases
        message_lower = error_message.lower()

        # Extract meaningful phrases (3+ words that might be reusable)
        words = message_lower.split()
        if len(words) >= 3:
            # Try different phrase lengths
            for length in [3, 4, 5]:
                if len(words) >= length:
                    phrase = " ".join(words[:length])
                    # Only add if it looks like a reusable pattern
                    if self._is_good_pattern(phrase):
                        self.pattern_matcher.add_learned_pattern(
                            pattern=phrase,
                            error_type="learned",
                            language=language,
                            linter=linter,
                            fixable=True,
                            confidence=0.7,
                        )
                        break

    def _is_good_pattern(self, phrase: str) -> bool:
        """Check if a phrase is likely to be a good reusable pattern."""
        # Avoid overly specific patterns
        specific_indicators = ["line ", "column ", "file ", "path "]
        if any(indicator in phrase for indicator in specific_indicators):
            return False

        # Look for error-like patterns
        error_indicators = [
            "error",
            "warning",
            "should",
            "expected",
            "missing",
            "unused",
        ]
        return any(indicator in phrase for indicator in error_indicators)

    def _update_pattern_confidence(
        self, error_message: str, language: str, linter: str, fix_successful: bool
    ):
        """Immediately update confidence for similar patterns."""
        # Find existing patterns that match this error
        if language in self.pattern_matcher.patterns_by_language:
            for pattern in self.pattern_matcher.patterns_by_language[language]:
                if pattern.linter == linter and pattern.pattern.lower() in error_message.lower():
                    # Adjust confidence based on fix success
                    if fix_successful:
                        pattern.confidence = min(1.0, pattern.confidence + 0.1)
                    else:
                        pattern.confidence = max(0.1, pattern.confidence - 0.1)

                    logger.debug(
                        f"Updated pattern confidence: {pattern.pattern} -> {pattern.confidence:.2f}"
                    )
                    break

    def _retrain_language_model(self, language: str, training_data: List[Dict]):
        """Retrain the ML model for a specific language."""
        if not SKLEARN_AVAILABLE:
            return

        try:
            messages = [item["message"] for item in training_data]
            labels = ["fixable" if item["fixable"] else "manual" for item in training_data]

            # Create or update vectorizer
            if language not in self.vectorizers:
                self.vectorizers[language] = TfidfVectorizer(
                    max_features=500,  # Keep it lightweight
                    ngram_range=(1, 2),  # Unigrams and bigrams
                    stop_words="english",
                    lowercase=True,
                    strip_accents="ascii",
                )

            # Train vectorizer and transform data
            X = self.vectorizers[language].fit_transform(messages)

            # Create or update classifier
            if language not in self.classifiers:
                self.classifiers[language] = MultinomialNB(alpha=1.0)

            # Train classifier
            self.classifiers[language].fit(X, labels)

            # Save models
            self._save_models()

            logger.info(f"🧠 Retrained {language} model with {len(training_data)} examples")

            # Log learning progress
            fixable_count = sum(1 for item in training_data if item["fixable"])
            success_rate = fixable_count / len(training_data) * 100
            logger.info(
                f"   📊 Success rate: {success_rate:.1f}% ({fixable_count}/{len(training_data)})"
            )

        except Exception as e:
            logger.error(f"Failed to retrain {language} model: {e}")

    def _save_models(self):
        """Save trained models to disk."""
        if not SKLEARN_AVAILABLE:
            return

        for language in self.classifiers:
            try:
                model_file = self.cache_dir / f"{language}_classifier.pkl"
                vectorizer_file = self.cache_dir / f"{language}_vectorizer.pkl"

                with open(model_file, "wb") as f:
                    pickle.dump(self.classifiers[language], f)

                with open(vectorizer_file, "wb") as f:
                    pickle.dump(self.vectorizers[language], f)

            except Exception as e:
                logger.error(f"Failed to save {language} model: {e}")

    def _load_models(self):
        """Load trained models from disk."""
        if not SKLEARN_AVAILABLE:
            return

        supported_languages = [
            "python",
            "javascript",
            "typescript",
            "go",
            "rust",
            "ansible",
        ]

        for language in supported_languages:
            model_file = self.cache_dir / f"{language}_classifier.pkl"
            vectorizer_file = self.cache_dir / f"{language}_vectorizer.pkl"

            if model_file.exists() and vectorizer_file.exists():
                try:
                    with open(model_file, "rb") as f:
                        self.classifiers[language] = pickle.load(f)

                    with open(vectorizer_file, "rb") as f:
                        self.vectorizers[language] = pickle.load(f)

                    logger.debug(f"Loaded {language} model from cache")

                except Exception as e:
                    logger.warning(f"Failed to load {language} model: {e}")

    def get_statistics(self) -> Dict:
        """Get statistics about the pattern matching system."""
        stats = {
            "pattern_matcher": {
                "languages": list(self.pattern_matcher.patterns_by_language.keys()),
                "total_patterns": sum(
                    len(patterns) for patterns in self.pattern_matcher.patterns_by_language.values()
                ),
                "ahocorasick_available": AHOCORASICK_AVAILABLE,
            },
            "ml_classifier": {
                "sklearn_available": SKLEARN_AVAILABLE,
                "learning_enabled": SKLEARN_AVAILABLE,
                "trained_languages": (list(self.classifiers.keys()) if SKLEARN_AVAILABLE else []),
                "cache_dir": str(self.cache_dir),
                "setup_command": (
                    "pip install aider-lint-fixer[learning]" if not SKLEARN_AVAILABLE else None
                ),
            },
        }

        # Add training data statistics
        if SKLEARN_AVAILABLE:
            for language in [
                "python",
                "javascript",
                "typescript",
                "go",
                "rust",
                "ansible",
            ]:
                training_file = self.cache_dir / f"{language}_training.json"
                if training_file.exists():
                    try:
                        with open(training_file, "r", encoding="utf-8") as f:
                            training_data = json.load(f)
                        stats["ml_classifier"][f"{language}_training_examples"] = len(training_data)

                        # Add learning progress info
                        if len(training_data) >= 5:
                            stats["ml_classifier"][f"{language}_model_trained"] = True
                        else:
                            stats["ml_classifier"][f"{language}_needs_examples"] = 5 - len(
                                training_data
                            )
                    except Exception:
                        pass

        # Add cache information
        stats["cache"] = {
            "cache_dir": str(self.cache_dir),
            "cache_sizes": self.cache_manager.get_cache_size(),
        }

        return stats

    def _periodic_cleanup(self):
        """Perform periodic cleanup of old data."""
        try:
            # Check if cleanup is needed (once per day)
            cleanup_marker = self.cache_dir / ".last_cleanup"
            current_time = time.time()

            should_cleanup = True
            if cleanup_marker.exists():
                try:
                    last_cleanup = cleanup_marker.stat().st_mtime
                    # Cleanup once per day
                    if current_time - last_cleanup < 24 * 60 * 60:
                        should_cleanup = False
                except Exception:
                    pass

            if should_cleanup:
                self.cache_manager.cleanup_old_data(max_age_days=30)
                # Update cleanup marker
                cleanup_marker.touch()
                logger.debug("Performed periodic cache cleanup")

        except Exception as e:
            logger.warning(f"Periodic cleanup failed: {e}")

    def export_learned_patterns(self, output_file: str):
        """Export learned patterns for backup or sharing."""
        self.cache_manager.export_patterns(Path(output_file))

    def import_learned_patterns(self, import_file: str):
        """Import patterns from a backup file."""
        self.cache_manager.import_patterns(Path(import_file))
        # Reload models after import
        if SKLEARN_AVAILABLE:
            self._load_models()


def detect_language_from_file_path(file_path: str) -> str:
    """Detect programming language from file path."""
    path = Path(file_path)
    extension = path.suffix.lower()

    # Map extensions to languages
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".d.ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".yml": "ansible",
        ".yaml": "ansible",
    }

    detected = ext_to_lang.get(extension, "unknown")

    # Special case for Ansible - check if it's actually Ansible YAML
    if detected == "ansible":
        # Look for Ansible-specific indicators in the path
        path_str = str(path).lower()
        ansible_indicators = [
            "playbook",
            "role",
            "task",
            "handler",
            "var",
            "inventory",
            "group_vars",
            "host_vars",
        ]
        if not any(indicator in path_str for indicator in ansible_indicators):
            # Might just be regular YAML
            detected = "yaml"

    return detected


class PatternCacheManager:
    """Manages pattern cache cleanup and maintenance."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def cleanup_old_data(self, max_age_days: int = 30):
        """Clean up old training data and models.

        Args:
            max_age_days: Maximum age in days for keeping data
        """
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        # Clean up old training data
        for training_file in self.cache_dir.glob("*_training.json"):
            try:
                with open(training_file, "r", encoding="utf-8") as f:
                    training_data = json.load(f)

                # Filter out old entries
                fresh_data = [
                    entry for entry in training_data if entry.get("timestamp", 0) > cutoff_time
                ]

                if len(fresh_data) != len(training_data):
                    with open(training_file, "w", encoding="utf-8") as f:
                        json.dump(fresh_data, f, indent=2)

                    logger.info(
                        f"Cleaned up {len(training_data) - len(fresh_data)} "
                        f"old entries from {training_file.name}"
                    )

            except Exception as e:
                logger.warning(f"Failed to clean up {training_file}: {e}")

        # Clean up orphaned model files
        self._cleanup_orphaned_models()

    def _cleanup_orphaned_models(self):
        """Remove model files that don't have corresponding training data."""
        training_languages = set()

        # Find languages with training data
        for training_file in self.cache_dir.glob("*_training.json"):
            language = training_file.stem.replace("_training", "")
            try:
                with open(training_file, "r", encoding="utf-8") as f:
                    training_data = json.load(f)
                if training_data:  # Only count if there's actual data
                    training_languages.add(language)
            except Exception:
                pass

        # Remove model files for languages without training data
        for model_file in self.cache_dir.glob("*_classifier.pkl"):
            language = model_file.stem.replace("_classifier", "")
            if language not in training_languages:
                try:
                    model_file.unlink()
                    vectorizer_file = self.cache_dir / f"{language}_vectorizer.pkl"
                    if vectorizer_file.exists():
                        vectorizer_file.unlink()
                    logger.info(f"Removed orphaned model files for {language}")
                except Exception as e:
                    logger.warning(f"Failed to remove orphaned model {model_file}: {e}")

    def get_cache_size(self) -> Dict[str, int]:
        """Get cache directory size information."""
        sizes = {"training_files": 0, "model_files": 0, "total_files": 0}

        try:
            for file_path in self.cache_dir.iterdir():
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    sizes["total_files"] += file_size

                    if file_path.name.endswith("_training.json"):
                        sizes["training_files"] += file_size
                    elif file_path.name.endswith((".pkl", ".joblib")):
                        sizes["model_files"] += file_size
        except Exception as e:
            logger.warning(f"Failed to calculate cache size: {e}")

        return sizes

    def export_patterns(self, output_file: Path):
        """Export learned patterns to a file for backup or sharing.

        Args:
            output_file: Path to export file
        """
        export_data = {"export_timestamp": time.time(), "languages": {}}

        for training_file in self.cache_dir.glob("*_training.json"):
            language = training_file.stem.replace("_training", "")
            try:
                with open(training_file, "r", encoding="utf-8") as f:
                    training_data = json.load(f)

                # Extract successful patterns
                successful_patterns = [
                    entry["message"] for entry in training_data if entry.get("fixable", False)
                ]

                export_data["languages"][language] = {
                    "total_examples": len(training_data),
                    "successful_patterns": successful_patterns[:100],  # Limit for size
                    "last_updated": (
                        max(entry.get("timestamp", 0) for entry in training_data)
                        if training_data
                        else 0
                    ),
                }

            except Exception as e:
                logger.warning(f"Failed to export patterns for {language}: {e}")

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Exported patterns to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export patterns: {e}")

    def import_patterns(self, import_file: Path):
        """Import patterns from a backup file.

        Args:
            import_file: Path to import file
        """
        try:
            with open(import_file, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            for language, data in import_data.get("languages", {}).items():
                training_file = self.cache_dir / f"{language}_training.json"

                # Load existing data
                existing_data = []
                if training_file.exists():
                    try:
                        with open(training_file, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                    except Exception:
                        pass

                # Add imported patterns as training examples
                for pattern in data.get("successful_patterns", []):
                    existing_data.append(
                        {
                            "message": pattern,
                            "language": language,
                            "linter": "imported",
                            "fixable": True,
                            "timestamp": time.time(),
                        }
                    )

                # Save updated data
                with open(training_file, "w", encoding="utf-8") as f:
                    json.dump(existing_data[-1000:], f, indent=2)  # Keep last 1000

                logger.info(
                    f"Imported {len(data.get('successful_patterns', []))} patterns for {language}"
                )

        except Exception as e:
            logger.error(f"Failed to import patterns: {e}")
