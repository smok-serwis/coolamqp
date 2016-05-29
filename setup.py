#!/usr/bin/env python

from distutils.core import setup

setup(name='CoolAMQP',
      version='0.1',
      description='The AMQP client library',
      author=u'Piotr Maślanka',
      author_email='piotrm@smok.co',
      url='https://github.com/piotrmaslanka/coolamqp',
      packages=['coolamqp', 'coolamqp.backends'],
      install_requires=[
            "amqp"
      ]
     )