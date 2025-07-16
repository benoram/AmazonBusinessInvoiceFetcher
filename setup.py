from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="invoice-fetcher",
    version="0.1.0",
    author="Amazon Business Invoice Fetcher",
    description="A CLI tool for automatically downloading and organizing "
    "invoices from Amazon Business",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.1.0",
        "selenium>=4.15.0",
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.2",
        "keyring>=24.0.0",
        "rich>=13.0.0",
        "webdriver-manager>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "invoice-fetcher=invoice_fetcher.cli:main",
        ],
    },
)
