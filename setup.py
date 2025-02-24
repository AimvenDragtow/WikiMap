from setuptools import setup, find_packages

setup(
    name="wikimap",
    version="0.1.0",
    author="Zakaria BELKHEIRI",
    author_email="cs.of.origins@gmail.com",
    description="A package to build and analyze Wikipedia article graphs from Wikimedia dumps.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AimvenDragtow/WikiMap",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
