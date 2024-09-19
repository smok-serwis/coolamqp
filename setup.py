from setuptools import setup, find_packages

from coolamqp import __version__

setup(keywords=['amqp', 'rabbitmq', 'client', 'network', 'ha', 'high availability'],
      version=__version__,
      packages=find_packages(include=['coolamqp', 'coolamqp.*']),
      install_requires=['six'],
      tests_require=["pytest", "coverage"],
      test_suite='nose2.collector.collector',
      python_requires='!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
      extras_require={
          ':python_version == "2.7"': ['futures', 'typing', 'monotonic'],
          'setproctitle': ['setproctitle'],
          'opentracing': ['opentracing'],
          'gevent': ['gevent'],
      },
      )
