#!/usr/bin/env python3
"""
Check Learning Setup Script

This script helps users verify that the learning system is properly configured
and provides guidance on how to enable it if needed.
"""

import sys
from pathlib import Path


def check_sklearn_availability():
    """Check if scikit-learn is available."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB

        return True, "scikit-learn is available"
    except ImportError as e:
        return False, f"scikit-learn not available: {e}"


def check_web_scraping_dependencies():
    """Check if web scraping dependencies are available."""
    missing = []

    try:
        import requests
    except ImportError:
        missing.append("requests")

    try:
        import bs4
    except ImportError:
        missing.append("beautifulsoup4")

    if missing:
        return False, f"Missing dependencies: {', '.join(missing)}"
    else:
        return True, "Web scraping dependencies available"


def check_ahocorasick_availability():
    """Check if Aho-Corasick is available for high-performance pattern matching."""
    try:
        import ahocorasick

        return True, "Aho-Corasick available (high-performance pattern matching enabled)"
    except ImportError:
        return False, "Aho-Corasick not available (using fallback pattern matching)"


def check_cache_directory():
    """Check if cache directory exists and is writable."""
    cache_dir = Path(".aider-lint-cache")

    if not cache_dir.exists():
        try:
            cache_dir.mkdir()
            return True, f"Created cache directory: {cache_dir.absolute()}"
        except Exception as e:
            return False, f"Cannot create cache directory: {e}"

    if not cache_dir.is_dir():
        return False, f"Cache path exists but is not a directory: {cache_dir.absolute()}"

    # Test write permissions
    try:
        test_file = cache_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        return True, f"Cache directory is writable: {cache_dir.absolute()}"
    except Exception as e:
        return False, f"Cache directory is not writable: {e}"


def check_learning_files():
    """Check for existing learning files."""
    cache_dir = Path(".aider-lint-cache")
    if not cache_dir.exists():
        return False, "No cache directory found"

    learning_files = list(cache_dir.glob("*_training.json"))
    scraped_files = list(cache_dir.glob("scraped_*.json"))

    if learning_files or scraped_files:
        files_info = []
        if learning_files:
            files_info.append(f"{len(learning_files)} training files")
        if scraped_files:
            files_info.append(f"{len(scraped_files)} scraped rule files")

        return True, f"Found learning data: {', '.join(files_info)}"
    else:
        return False, "No learning files found (this is normal for new installations)"


def main():
    """Main function to check learning setup."""
    print("🧠 Aider-Lint-Fixer Learning Setup Check")
    print("=" * 50)

    checks = [
        ("📦 scikit-learn availability", check_sklearn_availability),
        ("🌐 Web scraping dependencies", check_web_scraping_dependencies),
        ("⚡ Aho-Corasick performance", check_ahocorasick_availability),
        ("📁 Cache directory", check_cache_directory),
        ("📊 Learning files", check_learning_files),
    ]

    all_passed = True

    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")

            # Learning files and Aho-Corasick checks are informational
            if not passed and check_name not in [
                "📊 Learning files",
                "⚡ Aho-Corasick performance",
            ]:
                all_passed = False

        except Exception as e:
            print(f"❌ {check_name}: Error during check - {e}")
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("🎉 Learning system is properly configured!")
        print("\n💡 Next steps:")
        print("   1. Run aider-lint-fixer on your project")
        print("   2. Learning will happen automatically during fix attempts")
        print("   3. Monitor progress with: aider-lint-fixer --stats")
    else:
        print("⚠️  Learning system needs setup")
        print("\n🔧 To enable learning features:")
        print("   pip install aider-lint-fixer[learning]")
        print("\n📖 Or install dependencies manually:")
        print(
            "   pip install scikit-learn>=1.0.0 requests>=2.25.0 beautifulsoup4>=4.9.0 pyahocorasick>=1.4.0"
        )
        print("\n📊 Check status after installation:")
        print("   aider-lint-fixer --stats")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
