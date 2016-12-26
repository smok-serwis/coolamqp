#!/usr/bin/env python
# coding=UTF-8
from setuptools import setup

setup(name='CoolAMQP',
      version='0.12',
      description='AMQP client with sane reconnects',
      author='DMS Serwis s.c.',
      author_email='piotrm@smok.co',
      url='https://github.com/smok-serwis/coolamqp',
      download_url='https://github.com/smok-serwis/coolamqp/archive/v0.12.zip',
      keywords=['amqp', 'pyamqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      packages=[
          'coolamqp',
          'coolamqp.backends'
      ],
      license='MIT License',
      long_description=u'The AMQP client that handles reconnection madness for you',
      requires=['amqp', 'six', 'monotonic'],
      tests_require=["nose"],
      test_suite='nose.collector',
      classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Operating System :: OS Independent',
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: MIT License',
            'Topic :: Software Development :: Libraries'
      ]
     )


