#!/usr/bin/env python3
"""
Kali Tool - Penetration Testing Toolkit
Setup script for package installation
"""

from setuptools import setup, find_packages

setup(
    name="kali_tool",
    version="1.0.0",
    description="Penetration Testing Toolkit",
    author="Kali Tool Team",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "kali-tool=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

