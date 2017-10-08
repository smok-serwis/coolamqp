#!/usr/bin/env python
# coding=UTF-8
from setuptools import setup, find_packages


setup(keywords=['amqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      packages=find_packages(include=['coolamqp', 'coolamqp.*']),
      long_description=u'''Pure Python AMQP client, but with dynamic class generation and memoryviews FOR THE GODSPEED.

Also, handles your reconnects and transactionality THE RIGHT WAY, though somewhat opinionated''',
      install_requires=['six', 'monotonic', 'futures'],
      tests_require=["nose", 'coverage'],
      test_suite='nose.collector'
     )


