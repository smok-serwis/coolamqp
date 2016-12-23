CoolAMQP
========
[![PyPI version](https://badge.fury.io/py/CoolAMQP.svg)](https://badge.fury.io/py/CoolAMQP)
[![Build Status](https://travis-ci.org/smok-serwis/coolamqp.svg)](https://travis-ci.org/smok-serwis/coolamqp)
[![Code Climate](https://codeclimate.com/github/smok-serwis/coolamqp/badges/gpa.svg)](https://codeclimate.com/github/smok-serwis/coolamqp)
[![Test Coverage](https://codeclimate.com/github/smok-serwis/coolamqp/badges/coverage.svg)](https://codeclimate.com/github/smok-serwis/coolamqp/coverage)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)]()
[![PyPI](https://img.shields.io/pypi/pyversions/CoolAMQP.svg)]()
[![PyPI](https://img.shields.io/pypi/implementation/CoolAMQP.svg)]()

When you're tired of fucking with AMQP reconnects.

When a connection made by CoolAMQP to your broker fails, it will pick another
node, redeclare exchanges, queues, consumers, QoS and all the other shit, and tell
your application that a disconnect happened.

You only need to remember that:

1. Reconnects and redefinitions take a while.
 * Things will happen during that time. It is your responsibility to ensure that your distributed system is built to handle this
2. CoolAMQP will tell you when it senses losing broker connection.
 * It will also tell you when it regains the connection (that means that everything is redefined and ready to go)
3. Delivering messages multiple times may happen.
 * Ensure you know when it happens. Keywords: message acknowledgement, amqp specification

The project is actively maintained and used in a commercial project. Tests can run
either on Vagrant (Vagrantfile attached) or Travis CI, and run against RabbitMQ.

Enjoy!
