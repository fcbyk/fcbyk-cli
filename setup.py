from setuptools import setup

setup(
    name="fcbyk",
    version="0.1.0",
    packages=["fcbyk"],
    install_requires=["click"],
    entry_points={
        "console_scripts": [
            "fcbyk = fcbyk.cli:hello",
        ],
    },
)