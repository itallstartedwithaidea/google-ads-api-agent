"""Google Ads API Agent — PyPI package setup."""
from setuptools import setup, find_packages
from pathlib import Path

long_description = Path("README.md").read_text(encoding="utf-8")

setup(
    name="google-ads-agent",
    version="2.0.0",
    author="It All Started With AI Idea",
    author_email="john@itallstartedwithaidea.com",
    description="Enterprise-grade AI Google Ads management agent powered by Claude",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itallstartedwithaidea/google-ads-api-agent",
    project_urls={
        "Homepage": "https://googleadsagent.ai",
        "Bug Tracker": "https://github.com/itallstartedwithaidea/google-ads-api-agent/issues",
        "Documentation": "https://github.com/itallstartedwithaidea/google-ads-api-agent#readme",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={
        "": ["prompts/**/*.md", "actions/**/*.py", "configs/*.json"],
    },
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.43.0",
        "google-ads>=28.1.0",
        "google-auth>=2.23.0",
        "google-auth-oauthlib>=1.1.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.27.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "server": [
            "fastapi>=0.115.0",
            "uvicorn[standard]>=0.30.0",
            "pydantic>=2.0.0",
        ],
        "creative": [
            "cloudinary>=1.40.0",
        ],
        "cli": [
            "rich>=13.7.0",
        ],
        "all": [
            "fastapi>=0.115.0",
            "uvicorn[standard]>=0.30.0",
            "pydantic>=2.0.0",
            "cloudinary>=1.40.0",
            "rich>=13.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gads-agent=scripts.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    keywords="google-ads ai agent claude anthropic advertising ppc",
)
