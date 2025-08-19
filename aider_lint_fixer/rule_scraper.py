"""
Web scraper to build comprehensive rule knowledge base from official documentation.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

try:
    import requests
    from bs4 import BeautifulSoup

    SCRAPING_AVAILABLE = True
except ImportError:
    requests = None
    BeautifulSoup = None
    SCRAPING_AVAILABLE = False
logger = logging.getLogger(__name__)


@dataclass
class RuleInfo:
    """Information about a linter rule."""

    rule_id: str
    category: str
    auto_fixable: bool
    complexity: str
    description: str
    fix_strategy: str
    source_url: str


class RuleScraper:
    """Scrapes linter documentation to build rule knowledge base."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session() if SCRAPING_AVAILABLE else None
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        # URLs to scrape with enhanced coverage
        self.documentation_urls = {
            "ansible-lint": [
                "https://ansible-lint.readthedocs.io/rules/",
                "https://ansible-lint.readthedocs.io/rules/yaml/",
                "https://ansible-lint.readthedocs.io/rules/jinja/",
                "https://ansible-lint.readthedocs.io/rules/name/",
                "https://ansible-lint.readthedocs.io/rules/syntax-check/",
            ],
            "eslint": [
                "https://eslint.org/docs/latest/rules/",
            ],
            "flake8": [
                "https://flake8.pycqa.org/en/latest/user/error-codes.html",
            ],
            "pylint": [
                "https://pylint.pycqa.org/en/latest/user_guide/messages/index.html",
            ],
            "black": [
                "https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html",
            ],
        }

    def scrape_all_rules(self) -> Dict[str, Dict[str, RuleInfo]]:
        """Scrape all linter documentation and return rule database."""
        if not SCRAPING_AVAILABLE:
            logger.warning("requests and beautifulsoup4 not available, cannot scrape rules")
            return {}
        all_rules = {}
        for linter, urls in self.documentation_urls.items():
            logger.info(f"Scraping {linter} documentation...")
            linter_rules = {}
            for url in urls:
                try:
                    rules = self._scrape_url(url, linter)
                    linter_rules.update(rules)
                    logger.info(f"Scraped {len(rules)} rules from {url}")
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
            all_rules[linter] = linter_rules
            logger.info(f"Total {linter} rules: {len(linter_rules)}")
        # Cache the results
        self._save_scraped_rules(all_rules)
        return all_rules

    def _scrape_url(self, url: str, linter: str) -> Dict[str, RuleInfo]:
        """Scrape a specific URL for rules."""
        self._rate_limit()
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        if linter == "ansible-lint":
            return self._parse_ansible_lint_rules(soup, url)
        elif linter == "eslint":
            return self._parse_eslint_rules(soup, url)
        elif linter == "flake8":
            return self._parse_flake8_rules(soup, url)
        return {}

    def _parse_ansible_lint_rules(self, soup: "BeautifulSoup", url: str) -> Dict[str, RuleInfo]:
        """Parse ansible-lint documentation with enhanced rule detection."""
        rules = {}
        # Method 1: Extract from YAML rule page (most comprehensive)
        if "yaml" in url:
            rules.update(self._parse_yaml_rules(soup, url))
        # Method 2: Extract from main rules index
        elif "rules/" in url and not any(x in url for x in ["yaml", "jinja", "name"]):
            rules.update(self._parse_rules_index(soup, url))
        # Method 3: Extract from specific rule pages
        else:
            rule_id = self._extract_rule_from_url(url)
            if rule_id:
                description = self._extract_text(soup, ["p", "div", "h1"])
                category = self._categorize_ansible_rule(rule_id, description)
                auto_fixable = self._is_ansible_rule_fixable(rule_id, description)
                rules[rule_id] = RuleInfo(
                    rule_id=rule_id,
                    category=category,
                    auto_fixable=auto_fixable,
                    complexity="trivial" if auto_fixable else "manual",
                    description=description,
                    fix_strategy=self._get_fix_strategy(category, auto_fixable),
                    source_url=url,
                )
        return rules

    def _parse_yaml_rules(self, soup: "BeautifulSoup", url: str) -> Dict[str, RuleInfo]:
        """Parse YAML-specific rules from ansible-lint documentation."""
        rules = {}
        # Look for bullet points with yaml[rule] format
        for li in soup.find_all("li"):
            text = li.text.strip()
            # Match patterns like "yaml[line-length] - Line too long"
            match = re.search(r"`?yaml\[([^\]]+)\]`?\s*[-–]\s*(.+)", text)
            if match:
                rule_name = match.group(1)
                description = match.group(2).strip()
                rule_id = f"yaml[{rule_name}]"
                rules[rule_id] = RuleInfo(
                    rule_id=rule_id,
                    category="formatting",
                    auto_fixable=self._is_yaml_rule_fixable(rule_name, description),
                    complexity="trivial",
                    description=description,
                    fix_strategy="formatting_fix",
                    source_url=url,
                )
        return rules

    def _parse_rules_index(self, soup: "BeautifulSoup", url: str) -> Dict[str, RuleInfo]:
        """Parse rules from the main index page."""
        rules = {}
        # Look for links to rule pages
        for link in soup.find_all("a", href=True):
            href = link.get("hre", "")
            if href and not href.startswith("http"):
                rule_name = href.strip("/")
                if rule_name and not any(x in rule_name for x in ["..", "#", "http"]):
                    description = link.text.strip() or f"Rule: {rule_name}"
                    category = self._categorize_ansible_rule(rule_name, description)
                    auto_fixable = self._is_ansible_rule_fixable(rule_name, description)
                    rules[rule_name] = RuleInfo(
                        rule_id=rule_name,
                        category=category,
                        auto_fixable=auto_fixable,
                        complexity="simple" if auto_fixable else "manual",
                        description=description,
                        fix_strategy=self._get_fix_strategy(category, auto_fixable),
                        source_url=f"{url.rstrip('/')}/{rule_name}/",
                    )
        return rules

    def _extract_rule_from_url(self, url: str) -> Optional[str]:
        """Extract rule name from URL path."""
        parts = url.rstrip("/").split("/")
        if len(parts) > 0:
            return parts[-1]
        return None

    def _is_yaml_rule_fixable(self, rule_name: str, description: str) -> bool:
        """Determine if a YAML rule is auto-fixable."""
        fixable_yaml_rules = [
            "line-length",
            "trailing-spaces",
            "indentation",
            "comments",
            "document-start",
            "empty-lines",
            "new-line-at-end-of-file",
            "brackets",
            "colons",
            "commas",
            "braces",
        ]
        return rule_name in fixable_yaml_rules

    def _parse_eslint_rules(self, soup: "BeautifulSoup", url: str) -> Dict[str, RuleInfo]:
        """Parse ESLint documentation with enhanced rule detection."""
        rules = {}
        # Method 1: Look for rule links in the new ESLint format
        for link in soup.find_all("a", href=True):
            href = link.get("hre", "")
            # Match rule links like "/docs/latest/rules/rule-name"
            if "/rules/" in href and not href.endswith("/rules/"):
                rule_id = href.split("/rules/")[-1].strip("/")
                if rule_id and not any(x in rule_id for x in ["#", "?", "deprecated", "removed"]):
                    # Get the description from the link text or nearby text
                    description = link.text.strip()
                    # Look for the description and fixable indicators
                    auto_fixable = False
                    # Check the immediate parent for fixable indicators (more precise)
                    if link.parent:
                        parent_text = (
                            link.parent.get_text()
                            if hasattr(link.parent, "get_text")
                            else str(link.parent)
                        )
                        # Only consider it fixable if the wrench emoji is in the same line/element as the rule
                        if (
                            "🔧" in parent_text and len(parent_text) < 300
                        ):  # Reasonable length limit
                            auto_fixable = True
                        # Try to get better description from parent text
                        if len(parent_text) > len(description) and len(parent_text) < 200:
                            description = parent_text.strip()
                    category = self._categorize_eslint_rule(rule_id, description)
                    rules[rule_id] = RuleInfo(
                        rule_id=rule_id,
                        category=category,
                        auto_fixable=auto_fixable,
                        complexity="trivial" if auto_fixable else "simple",
                        description=description or f"ESLint rule: {rule_id}",
                        fix_strategy=self._get_fix_strategy(category, auto_fixable),
                        source_url=f"https://eslint.org/docs/latest/rules/{rule_id}",
                    )
        # Method 2: Fallback - look for table rows (old format)
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            rule_link = cells[0].find("a")
            if not rule_link:
                continue
            rule_id = rule_link.text.strip()
            if rule_id and rule_id not in rules:  # Don't override Method 1 results
                description = cells[1].text.strip() if len(cells) > 1 else ""
                # Check for fixable indicator (wrench icon or "fixable" text)
                auto_fixable = any(
                    "wrench" in str(cell) or "fixable" in cell.text.lower() for cell in cells
                )
                category = self._categorize_eslint_rule(rule_id, description)
                rules[rule_id] = RuleInfo(
                    rule_id=rule_id,
                    category=category,
                    auto_fixable=auto_fixable,
                    complexity="trivial" if auto_fixable else "manual",
                    description=description,
                    fix_strategy=self._get_fix_strategy(category, auto_fixable),
                    source_url=f"https://eslint.org/docs/latest/rules/{rule_id}",
                )
        return rules

    def _parse_flake8_rules(self, soup: "BeautifulSoup", url: str) -> Dict[str, RuleInfo]:
        """Parse Flake8 documentation."""
        rules = {}
        # Flake8 typically has error codes in a list or table
        for element in soup.find_all(["li", "tr", "dt"]):
            text = element.text.strip()
            # Look for error codes like E501, W503, etc.
            match = re.search(r"\b([EFWC]\d{3})\b", text)
            if not match:
                continue
            rule_id = match.group(1)
            description = text.replace(rule_id, "").strip(" :-")
            category = self._categorize_flake8_rule(rule_id, description)
            auto_fixable = self._is_flake8_rule_fixable(rule_id, description)
            rules[rule_id] = RuleInfo(
                rule_id=rule_id,
                category=category,
                auto_fixable=auto_fixable,
                complexity="trivial" if auto_fixable else "manual",
                description=description,
                fix_strategy=self._get_fix_strategy(category, auto_fixable),
                source_url=url,
            )
        return rules

    def _extract_ansible_rule_id(self, section) -> Optional[str]:
        """Extract ansible-lint rule ID from section."""
        # Look for patterns like "yaml[line-length]", "name[play]", etc.
        text = section.text
        match = re.search(r"\b(\w+\[[^\]]+\]|\w+\[\w+\])\b", text)
        return match.group(1) if match else None

    def _categorize_ansible_rule(self, rule_id: str, description: str) -> str:
        """Categorize ansible-lint rule."""
        if rule_id.startswith("yaml"):
            return "formatting"
        elif rule_id.startswith("jinja"):
            return "formatting"
        elif rule_id.startswith("name"):
            return "style"
        elif "syntax" in description.lower():
            return "syntax"
        else:
            return "style"

    def _is_ansible_rule_fixable(self, rule_id: str, description: str) -> bool:
        """Determine if ansible-lint rule is auto-fixable."""
        fixable_patterns = [
            "line-length",
            "spacing",
            "comments",
            "document-start",
            "trailing",
            "whitespace",
            "indent",
        ]
        return any(pattern in rule_id.lower() for pattern in fixable_patterns)

    def _categorize_eslint_rule(self, rule_id: str, description: str) -> str:
        """Categorize ESLint rule."""
        if any(word in description.lower() for word in ["format", "style", "spacing"]):
            return "formatting"
        elif any(word in description.lower() for word in ["unused", "import"]):
            return "unused"
        elif any(word in description.lower() for word in ["syntax", "parse"]):
            return "syntax"
        else:
            return "style"

    def _categorize_flake8_rule(self, rule_id: str, description: str) -> str:
        """Categorize Flake8 rule."""
        if rule_id.startswith("E"):
            return "formatting"
        elif rule_id.startswith("W"):
            return "style"
        elif rule_id.startswith("F"):
            return "unused" if "unused" in description.lower() else "syntax"
        else:
            return "style"

    def _is_flake8_rule_fixable(self, rule_id: str, description: str) -> bool:
        """Determine if Flake8 rule is auto-fixable."""
        # Many formatting and import rules are fixable
        fixable_rules = ["E501", "F401", "E302", "E303", "W291", "W292", "W293"]
        return rule_id in fixable_rules

    def _get_fix_strategy(self, category: str, auto_fixable: bool) -> str:
        """Get fix strategy based on category and fixability."""
        if not auto_fixable:
            return "requires_human_input"
        strategy_map = {
            "formatting": "whitespace_cleanup",
            "unused": "removal",
            "style": "style_adjustment",
            "syntax": "syntax_correction",
        }
        return strategy_map.get(category, "automatic_fix")

    def _extract_text(self, element, tags: List[str]) -> str:
        """Extract text from specific tags within an element."""
        texts = []
        for tag in tags:
            for elem in element.find_all(tag):
                text = elem.text.strip()
                if text and len(text) > 10:  # Avoid short/empty text
                    texts.append(text)
                    break
        return " ".join(texts[:2])  # Limit to first 2 meaningful texts

    def _rate_limit(self):
        """Implement rate limiting for requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()

    def _save_scraped_rules(self, rules: Dict[str, Dict[str, RuleInfo]]):
        """Save scraped rules to cache."""
        cache_file = self.cache_dir / "scraped_rules.json"
        # Convert RuleInfo objects to dictionaries
        serializable_rules = {}
        for linter, linter_rules in rules.items():
            serializable_rules[linter] = {}
            for rule_id, rule_info in linter_rules.items():
                serializable_rules[linter][rule_id] = {
                    "rule_id": rule_info.rule_id,
                    "category": rule_info.category,
                    "auto_fixable": rule_info.auto_fixable,
                    "complexity": rule_info.complexity,
                    "description": rule_info.description,
                    "fix_strategy": rule_info.fix_strategy,
                    "source_url": rule_info.source_url,
                    "scraped_at": time.time(),
                }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(serializable_rules, f, indent=2)
        logger.info(f"Saved scraped rules to {cache_file}")


def scrape_and_update_knowledge_base(cache_dir: Path = None) -> Dict[str, Dict]:
    """Scrape all linter documentation and return updated knowledge base."""
    if cache_dir is None:
        cache_dir = Path(".aider-lint-cache")
    scraper = RuleScraper(cache_dir)
    return scraper.scrape_all_rules()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape linter documentation for rules")
    parser.add_argument(
        "--linter",
        choices=["ansible-lint", "eslint", "flake8", "all"],
        default="all",
        help="Which linter to scrape",
    )
    parser.add_argument("--output", help="Output file for scraped rules")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scraped")
    args = parser.parse_args()
    if not SCRAPING_AVAILABLE:
        print("❌ Scraping dependencies not available. Install with:")
        print("   pip install requests beautifulsoup4")
        exit(1)
    scraper = RuleScraper(Path(".aider-lint-cache"))
    if args.dry_run:
        print("🔍 Would scrape the following URLs:")
        if args.linter == "all":
            for linter, urls in scraper.documentation_urls.items():
                print(f"\n{linter}:")
                for url in urls:
                    print(f"  - {url}")
        else:
            urls = scraper.documentation_urls.get(args.linter, [])
            print(f"\n{args.linter}:")
            for url in urls:
                print(f"  - {url}")
        exit(0)
    print("🚀 Starting rule scraping...")
    if args.linter == "all":
        rules = scraper.scrape_all_rules()
    else:
        rules = {}
        urls = scraper.documentation_urls.get(args.linter, [])
        if urls:
            print(f"📡 Scraping {args.linter}...")
            linter_rules = {}
            for url in urls:
                try:
                    url_rules = scraper._scrape_url(url, args.linter)
                    linter_rules.update(url_rules)
                    print(f"  ✅ {url}: {len(url_rules)} rules")
                except Exception as e:
                    print(f"  ❌ {url}: {e}")
            rules[args.linter] = linter_rules
    print("\n📊 Scraping Results:")
    total_rules = 0
    for linter, linter_rules in rules.items():
        count = len(linter_rules)
        total_rules += count
        print(f"  {linter}: {count} rules")
        # Show sample rules
        if count > 0:
            sample_rules = list(linter_rules.items())[:3]
            for rule_id, rule_info in sample_rules:
                fixable = "✅" if rule_info.auto_fixable else "❌"
                print(f"    {fixable} {rule_id}: {rule_info.description[:60]}...")
    print(f"\n🎯 Total: {total_rules} rules scraped")
    if args.output:
        import json

        with open(args.output, "w") as f:
            # Convert RuleInfo objects to dicts for JSON serialization
            serializable_rules = {}
            for linter, linter_rules in rules.items():
                serializable_rules[linter] = {}
                for rule_id, rule_info in linter_rules.items():
                    serializable_rules[linter][rule_id] = {
                        "rule_id": rule_info.rule_id,
                        "category": rule_info.category,
                        "auto_fixable": rule_info.auto_fixable,
                        "complexity": rule_info.complexity,
                        "description": rule_info.description,
                        "fix_strategy": rule_info.fix_strategy,
                        "source_url": rule_info.source_url,
                    }
            json.dump(serializable_rules, f, indent=2)
        print(f"💾 Saved to {args.output}")
