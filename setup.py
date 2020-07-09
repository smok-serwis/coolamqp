#!/usr/bin/env python
# coding=UTF-8
from setuptools import setup, find_packages

from coolamqp import __version__

setup(keywords=['amqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      version=__version__,
      packages=find_packages(include=['coolamqp', 'coolamqp.*']),
      install_requires=['six'],
      # per coverage version for codeclimate-reporter
      tests_require=["nose2", "coverage", "nose2[coverage_plugin]"],
      test_suite='nose2.collector.collector',
      python_requires='!=2.7.*,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
      extras_require={
          ':python_version == "2.7"': ['futures', 'typing', 'monotonic'],
          'prctl': ['prctl'],
          'opentracing': ['opentracing'],
          'gevent': ['gevent']
      }
      )
