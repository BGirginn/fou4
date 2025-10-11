#!/usr/bin/env python3
"""
FOU4 - Forensic Utility Tool
Setup script for installation
"""

from setuptools import setup, find_packages
import os

# Read the long description from README
def read_long_description():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "FOU4 - Forensic Utility Tool for security testing and penetration testing"

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return ["rich>=13.0.0"]

setup(
    name="fou4",
    version="1.4.1",
    author="FOU4 Development Team",
    author_email="fou4@example.com",
    description="A comprehensive forensic and security testing toolkit",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fou4",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "fou4=fou4:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md"],
    },
    zip_safe=False,
    keywords="security penetration-testing forensics network-scanning osint wifi",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/fou4/issues",
        "Source": "https://github.com/yourusername/fou4",
        "Documentation": "https://github.com/yourusername/fou4#readme",
    },
)
