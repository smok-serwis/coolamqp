#!/usr/bin/env python
# coding=UTF-8
from setuptools import setup


setup(name=u'CoolAMQP',
      version='0.87',
      description=u'The fastest AMQP client',
      author=u'DMS Serwis s.c.',
      author_email=u'piotrm@smok.co',
      url=u'https://github.com/smok-serwis/coolamqp',
      download_url='https://github.com/smok-serwis/coolamqp/archive/v0.87.zip',
      keywords=['amqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      packages=[
          'coolamqp',
          'coolamqp.uplink',
          'coolamqp.uplink.connection',
          'coolamqp.uplink.listener',
          'coolamqp.clustering',
          'coolamqp.attaches',
          'coolamqp.framing',
          'coolamqp.framing.compilation',
      ],
      license=u'MIT License',
      long_description=u'''Pure Python AMQP client, but with dynamic class generation and memoryviews FOR THE GODSPEED.

Also, handles your reconnects and transactionality THE RIGHT WAY''',
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
#            'Operating System :: OS Independent',      epoll :'(
            'Operating System :: POSIX :: Linux',
#            'Development Status :: 5 - Production/Stable',
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: MIT License',
            'Topic :: Software Development :: Libraries',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Libraries :: Python Modules'  # obvi

      ]
     )


