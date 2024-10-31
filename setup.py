# setup.py
from setuptools import setup, find_packages

setup(
    name="ipr-monitoring",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "prometheus_client>=0.16.0",
        "aiohttp>=3.8.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.18.0",
    ],
    author="Your Name",
    description="IP Rights Monitoring Package",
    python_requires=">=3.7",
)