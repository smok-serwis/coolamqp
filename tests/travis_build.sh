#!/bin/bash

set -x
set -e

pip install wheel twine yapf

python -m compile_definitions
python setup.py bdist bdist_wheel

twine upload -u $PYPI_USER -p $PYPI_PWD dist/*
