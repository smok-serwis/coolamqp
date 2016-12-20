#!/usr/bin/env python
#coding=UTF-8
from distutils.core import setup

setup(name='CoolAMQP',
      version='0.6',
      description='The AMQP client library',
      author=u'DMS Serwis s.c.',
      author_email='piotrm@smok.co',
      url='https://github.com/smok-serwis/coolamqp',
      download_url='https://github.com/smok-serwis/coolamqp/archive/master.zip',
      keywords=['amqp', 'pyamqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      packages=['coolamqp', 'coolamqp.backends'],
      license='MIT License',
      long_description='''The Python AMQP client library that makes you forget about all the nasty corner cases about AMQP reconnection''',
      requires=[
            "amqp",
            "six"
      ],
      classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Operating System :: OS Independent'
      ]
     )