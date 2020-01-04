#!/bin/bash

set -x
set -e

pip install yapf
python -m compile_definitions
python setup.py bdist bdist_wheel

if [ $TRAVIS_BRANCH == "master" ]; then

    if [ $TRAVIS_PYTHON_VERSION == "2.7" ]; then
        pip install wheel twine
        twine upload -u $PYPI_USER -p $PYPI_PWD dist/*
    fi
fi
