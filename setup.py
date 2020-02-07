#!/usr/bin/env python
# coding=UTF-8
from setuptools import setup, find_packages

from coolamqp import __version__

setup(keywords=['amqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      version=__version__,
      packages=find_packages(include=['coolamqp', 'coolamqp.*']),
      long_description=u'''Pure Python AMQP client, but with dynamic class generation and memoryviews FOR THE GODSPEED.

Also, handles your reconnects and transactionality THE RIGHT WAY, though somewhat opinionated''',
      install_requires=['six', 'monotonic', 'futures', 'typing'],
      # per coverage version for codeclimate-reporter
      tests_require=["nose2", "coverage", "nose2[coverage_plugin]"],
      test_suite='nose2.collector.collector'
      )


