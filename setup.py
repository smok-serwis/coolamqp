#!/usr/bin/env python
# coding=UTF-8
from setuptools import setup, find_packages

from coolamqp import __version__

setup(keywords=['amqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      version=__version__,
      packages=find_packages(include=['coolamqp', 'coolamqp.*']),
      install_requires=['six', 'monotonic'],
      # per coverage version for codeclimate-reporter
      tests_require=["nose2", "coverage", "nose2[coverage_plugin]"],
      test_suite='nose2.collector.collector',
      extras_require={
          ':python_version == "2.7"': ['futures', 'typing'],
          'prctl': ['prctl']
      }
      )
