"""
Setup script for Desktop Pony RSA Swarm.

Install in development mode:
    pip install -e .

Or regular install:
    pip install .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "desktop_pony_swarm" / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="desktop_pony_swarm",
    version="0.1.0",
    description="Recursive Self-Aggregation (RSA) Multi-Agent Coordination System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FLOSSI0ULLK",
    license="Compassion Clause",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.9.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
        "embeddings": [
            "sentence-transformers>=2.2.0",
            "torch>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pony-swarm=run_swarm:main",
            "pony-swarm-demo=run_swarm:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
