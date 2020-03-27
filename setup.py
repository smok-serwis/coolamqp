#!/usr/bin/env python
# coding=UTF-8
from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
from coolamqp import __version__

ext_modules = [
      Extension('coolamqp.utils', ['coolamqp/utils.pyx'])
]

setup(keywords=['amqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      version=__version__,
      packages=find_packages(include=['coolamqp', 'coolamqp.*']),
      install_requires=['six', 'monotonic', 'futures', 'typing'],
      # per coverage version for codeclimate-reporter
      tests_require=["nose2", "coverage", "nose2[coverage_plugin]"],
      test_suite='nose2.collector.collector',
      ext_modules=ext_modules
      )


