#!/usr/bin/env python3
"""
kotoba - Web testing tool using Japanese natural language
Setup script for pip installation
"""


from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="kotoba",
    version="0.0.1",
    author="kotoba Development Team",
    description="Web testing tool using Japanese natural language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0xkaz/kotoba",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "Natural Language :: Japanese",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.1.0",
        ],
        "gpu": [
            "torch>=2.0.0",
            "accelerate>=0.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kotoba=kotoba.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "kotoba": ["configs/*.yaml"],
    },
    project_urls={
        "Bug Reports": "https://github.com/0xkaz/kotoba/issues",
        "Source": "https://github.com/0xkaz/kotoba",
    },
    keywords="japanese nlp web testing playwright llm automation",
    zip_safe=False,
)