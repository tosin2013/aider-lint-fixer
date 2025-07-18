"""
Cache Management CLI

Command-line interface for managing the pattern matching cache.
"""

import click
from pathlib import Path
from typing import Optional

from colorama import Fore, Style

from .pattern_matcher import SmartErrorClassifier


@click.command()
@click.option("--project-path", default=".", help="Project path")
@click.option("--action", 
              type=click.Choice(["stats", "cleanup", "export", "import"]),
              required=True,
              help="Cache management action")
@click.option("--file", "file_path", help="File path for export/import operations")
@click.option("--max-age-days", default=30, help="Maximum age in days for cleanup")
def cache_manager(project_path: str, action: str, file_path: Optional[str], max_age_days: int):
    """Manage pattern matching cache.
    
    Examples:
        # Show cache statistics
        python -m aider_lint_fixer.cache_cli --action stats
        
        # Clean up old data
        python -m aider_lint_fixer.cache_cli --action cleanup --max-age-days 30
        
        # Export patterns
        python -m aider_lint_fixer.cache_cli --action export --file patterns.json
        
        # Import patterns
        python -m aider_lint_fixer.cache_cli --action import --file patterns.json
    """
    cache_dir = Path(project_path) / ".aider-lint-cache"
    classifier = SmartErrorClassifier(cache_dir)
    
    if action == "stats":
        stats = classifier.get_statistics()
        print(f"\n{Fore.CYAN}📊 Pattern Cache Statistics{Style.RESET_ALL}")
        print(f"   Cache directory: {stats['cache']['cache_dir']}")
        
        cache_sizes = stats['cache']['cache_sizes']
        print(f"   Training files: {cache_sizes['training_files']:,} bytes")
        print(f"   Model files: {cache_sizes['model_files']:,} bytes")
        print(f"   Total size: {cache_sizes['total_files']:,} bytes")
        
        print(f"\n{Fore.CYAN}🧠 Pattern Matching{Style.RESET_ALL}")
        print(f"   Languages: {', '.join(stats['pattern_matcher']['languages'])}")
        print(f"   Total patterns: {stats['pattern_matcher']['total_patterns']}")
        print(f"   Aho-Corasick available: {stats['pattern_matcher']['ahocorasick_available']}")
        
        print(f"\n{Fore.CYAN}🤖 Machine Learning{Style.RESET_ALL}")
        print(f"   scikit-learn available: {stats['ml_classifier']['sklearn_available']}")
        print(f"   Trained languages: {', '.join(stats['ml_classifier']['trained_languages'])}")
        
        # Show training data counts
        for key, value in stats['ml_classifier'].items():
            if key.endswith('_training_examples'):
                language = key.replace('_training_examples', '')
                print(f"   {language}: {value} training examples")
    
    elif action == "cleanup":
        print(f"\n{Fore.YELLOW}🧹 Cleaning up cache (max age: {max_age_days} days)...{Style.RESET_ALL}")
        classifier.cache_manager.cleanup_old_data(max_age_days)
        print(f"{Fore.GREEN}✅ Cache cleanup complete{Style.RESET_ALL}")
    
    elif action == "export":
        if not file_path:
            print(f"{Fore.RED}❌ Export requires --file parameter{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.BLUE}📤 Exporting patterns to {file_path}...{Style.RESET_ALL}")
        classifier.export_learned_patterns(file_path)
        print(f"{Fore.GREEN}✅ Export complete{Style.RESET_ALL}")
    
    elif action == "import":
        if not file_path:
            print(f"{Fore.RED}❌ Import requires --file parameter{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.BLUE}📥 Importing patterns from {file_path}...{Style.RESET_ALL}")
        classifier.import_learned_patterns(file_path)
        print(f"{Fore.GREEN}✅ Import complete{Style.RESET_ALL}")


if __name__ == "__main__":
    cache_manager()
