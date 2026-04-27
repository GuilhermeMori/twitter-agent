from setuptools import setup, find_packages

setup(
    name="twitter-scraping-saas",
    version="0.1.0",
    description="Twitter Scraping SaaS Platform Backend",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "supabase>=2.3.0",
        "psycopg2-binary>=2.9.9",
        "celery>=5.3.4",
        "redis>=5.0.1",
        "apify-client>=1.6.3",
        "openai>=1.3.7",
        "python-docx>=1.1.0",
        "aiosmtplib>=3.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "hypothesis>=6.92.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "ipython>=8.18.1",
            "ipdb>=0.13.13",
        ],
    },
)
