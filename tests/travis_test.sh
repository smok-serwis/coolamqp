#!/bin/bash
set -e
set -x

curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter
chmod +x ./cc-test-reporter
./cc-test-reporter before-build
pip install nose2 coverage

python setup.py install
pip install -r stress_tests/requirements.txt
pip install yapf nose2 mock coverage nose2[coverage_plugin]

coverage run --append -m compile_definitions
coverage run --append -m nose2 -vv
COOLAMQP_FORCE_SELECT_LISTENER=1 coverage run --append -m nose2 -vv
coverage run --append -m stress_tests
COOLAMQP_FORCE_SELECT_LISTENER=1 coverage run --append -m stress_tests
