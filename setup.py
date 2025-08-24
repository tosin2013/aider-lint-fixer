import os

from setuptools import find_packages, setup

# Get the directory containing this setup.py file
here = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Automated lint error detection and fixing powered by aider.chat and AI"

try:
    with open(os.path.join(here, "requirements.txt"), "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = [
        "aider-chat>=0.85.0",
        "click>=8.0.0",
        "colorama>=0.4.0",
        "PyYAML>=6.0.0",
        "python-dotenv>=1.0.0",
        "flake8>=7.0.0",
    ]

setup(
    name="aider-lint-fixer",
    author="Tosin Akinosho",
    author_email="tosin@decisioncrafters.com",
    description="Automated lint error detection and fixing powered by aider.chat and AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tosin2023/aider-lint-fixer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aider-lint-fixer=aider_lint_fixer.main:main",
        ],
    },
)
