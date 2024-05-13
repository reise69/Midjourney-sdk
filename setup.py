import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="midjourney-sdk-py",
    version="1.0.0",
    description="Midjourney SDK for interacting with Midjourney Discord. Get imagine. All options possible.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/reise69/Midjourney-sdk",
    author="Alban Lamberet",
    author_email="contact@refbax.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "midjourney-sdk-py=midjourney_sdk_py.__main__:main",
        ]
    },
)