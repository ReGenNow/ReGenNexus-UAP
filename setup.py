from setuptools import setup, find_packages

setup(
    name="regennexus-core",
    version="0.1.0",
    description="ReGenNexus Universal Agent Protocol (UAP) Core",
    author="ReGen Designs LLC",
    author_email="info@regendesigns.com",
    url="https://github.com/ReGenNow/ReGenNexus",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "asyncio",
        "pycryptodome",
        "uuid",
    ],
    keywords="protocol, agent, communication, uap",
)
