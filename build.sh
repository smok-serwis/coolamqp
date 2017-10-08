#!/bin/bash

set -x
set -e

python compile_definitions.py
python setup.py bdist bdist_wheel

if [ $TRAVIS_BRANCH == "master" ]; then

    if [ $TRAVIS_PYTHON_VERSION == "2.7" ]; then
        pip install wheel twine
        twine upload -u $PYPI_USER -p $PYPI_PWD dist/*
    fi
fi
