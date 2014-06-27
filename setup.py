import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pymongo-newrelic",
    version = "1.0.0",
    author = "Nino Walker",
    author_email = "nino@livefyre.com",
    description = ("Enable query/op-level inspection of pymongo in your newrelic dashboard."),
    license = "MIT",
    keywords = "mongo mongodb newrelic",
    url = "https://github.com/Livefyre/pymongo-newrelic",
    packages=find_packages(exclude=['tests']),
    install_requires=["pymongo>=2.7", "newrelic>=1.11.0.55"],
    long_description=read('README.md'),
    setup_requires=['nose>=1.0', 'coverage', 'nosexcover', 'mock'],
    test_suite='nose.collector',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
