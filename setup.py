# https://medium.com/nerd-for-tech/how-to-build-and-distribute-a-cli-tool-with-python-537ae41d9d78

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read()

setup(
    name="dm-cli",
    version="0.1.5",
    author="",
    author_email="",
    license="MIT",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/equinor/dm-cli",
    packages=["dm_cli"],
    install_requires=[requirements],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points="""
        [console_scripts]
        dm=dm:cli
    """,
    scripts=[
        "dm_cli/bin/dm",
    ],
)
