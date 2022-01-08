from pathlib import Path

from setuptools import find_packages, setup

long_description = Path("README.md").read_text()

version = Path("version").read_text().strip()

setup(
    name="dbtrunner",
    version=version,
    description="one line description of your project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests"]),
    package_data={
        '': ['py.typed'],
    },
    include_package_data=True,
    install_requires=[
        "boto3~=1.20.30",
        "numpy~=1.22.0",
        "pydantic~=1.9",
        "typer~=0.4.0",
    ],
    extras_require={
        "dev": [
            "autopep8==1.6.0",
            "isort==5.8.0",
            "flake8==4.0.1",
            "flake8-annotations==2.7.0",
            "flake8-colors==0.1.9",
            "pre-commit==2.15.0",
            "pytest==6.2.5",
            "twine==3.6.0",
            "moto[all]==2.2.16",
            "PyYAML==5.4.1",
            "snowflake-connector-python~=2.4.6",
            "pygit2~=1.7.0",
            "boto3~=1.20.30",
        ]
    },
    entry_points={
        "console_scripts": ["runner = src.runner:main"],
    }
)
