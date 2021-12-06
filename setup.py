#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = [
    "docker",
    "pytest",
    "PyGithub",
    "requests",
    "ruamel.yaml",
    "ruamel.yaml.clib",
    "pandas",
    "spython",
    "kipoi",
    "pre-commit",
]
setup_requirements = []

test_requirements = []

setup(
    author="Haimasree Bhattacharya",
    author_email="haimasree.de@gmail.com",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.9",
    ],
    description="Python Boilerplate contains all the \
        boilerplate you need to create a Python package.",
    entry_points={
        "console_scripts": [
            "update_all_singularity=kipoi_containers.update_all_singularity_containers:run_update",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords="kipoi_containers",
    name="kipoi_containers",
    packages=find_packages(include=["kipoi_containers", "kipoi_containers.*"]),
    setup_requires=setup_requirements,
    url="https://github.com/kipoi/kipoi-containers",
    version="0.1.0",
    zip_safe=False,
)
