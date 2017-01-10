CoolAMQP
========
[![PyPI version](https://badge.fury.io/py/CoolAMQP.svg)](https://badge.fury.io/py/CoolAMQP)
[![Build Status](https://travis-ci.org/smok-serwis/coolamqp.svg)](https://travis-ci.org/smok-serwis/coolamqp)
[![Code Climate](https://codeclimate.com/github/smok-serwis/coolamqp/badges/gpa.svg)](https://codeclimate.com/github/smok-serwis/coolamqp)
[![Test Coverage](https://codeclimate.com/github/smok-serwis/coolamqp/badges/coverage.svg)](https://codeclimate.com/github/smok-serwis/coolamqp/coverage)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)]()
[![PyPI](https://img.shields.io/pypi/pyversions/CoolAMQP.svg)]()
[![PyPI](https://img.shields.io/pypi/implementation/CoolAMQP.svg)]()

A **magical** AMQP client, that uses **heavy sorcery** to achieve speeds that other AMQP clients cannot even hope to match.

tl;dr - [this](coolamqp/framing/definitions.py) is **machine-generated** compile-time.
[this](coolamqp/framing/compilation/content_property.py) **generates classes run-time**,
and there are memoryviews **_everywhere_**. 

This is borderline absurd.


The project is actively maintained and used in a commercial project. Tests can run
either on Vagrant (Vagrantfile attached) or Travis CI, and run against RabbitMQ.

Enjoy!


## Notes
Assertions are sprinkled throughout the code. You may wish to run with optimizations enabled
if you need every CPU cycle you can get.

**v0.8** series has unstable API.

**v0.9** series will have a stable API.