from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read()

from dm_cli import VERSION

setup(
    name="dm-cli",
    version=VERSION,
    author="",
    author_email="",
    license="MIT",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/equinor/dm-cli",
    packages=[
        "dm_cli",
        "dm_cli/utils",
        "dm_cli/command_group",
        "dm_cli/dmss_api",
        "dm_cli/dmss_api/api",
        "dm_cli/dmss_api/models",
        "dm_cli/dmss_api/model",
    ],
    install_requires=[requirements],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    scripts=[
        "dm_cli/bin/dm",
    ],
)
