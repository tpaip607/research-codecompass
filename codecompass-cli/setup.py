"""Setup script for CodeCompass CLI"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="codecompass-cli",
    version="0.1.0",
    description="Navigate codebases by structure, not just semantics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tarakanath Paipuru",
    url="https://github.com/[author]/research-codecompass",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "neo4j>=5.0.0",
        "rank-bm25>=0.2.2",
    ],
    entry_points={
        "console_scripts": [
            "codecompass=codecompass.cli:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
