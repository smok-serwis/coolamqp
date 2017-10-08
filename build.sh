#!/bin/bash

set -x
set -e

python setup.py bdist bdist_wheel

if [ $TRAVIS_BRANCH == "master" ]; then
    pip install wheel twine
    twine upload -u $PYPI_USER -p $PYPI_PWD dist/*
fi
