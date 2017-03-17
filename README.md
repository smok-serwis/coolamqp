CoolAMQP
========
[![Documentation Status](https://readthedocs.org/projects/coolamqp/badge/?version=latest)](http://coolamqp.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/CoolAMQP.svg)](https://badge.fury.io/py/CoolAMQP)
[![Build Status](https://travis-ci.org/smok-serwis/coolamqp.svg)](https://travis-ci.org/smok-serwis/coolamqp)
[![Code Climate](https://codeclimate.com/github/smok-serwis/coolamqp/badges/gpa.svg)](https://codeclimate.com/github/smok-serwis/coolamqp)
[![Test Coverage](https://codeclimate.com/github/smok-serwis/coolamqp/badges/coverage.svg)](https://codeclimate.com/github/smok-serwis/coolamqp/coverage)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)]()
[![PyPI](https://img.shields.io/pypi/pyversions/CoolAMQP.svg)]()
[![PyPI](https://img.shields.io/pypi/implementation/CoolAMQP.svg)]()
[![Issue Count](https://codeclimate.com/github/smok-serwis/coolamqp/badges/issue_count.svg)](https://codeclimate.com/github/smok-serwis/coolamqp)

A **magical** AMQP client, that uses **heavy sorcery** to achieve speeds that other AMQP clients cannot even hope to match.

Documentation (WIP) is available at [Read the Docs](http://coolamqp.readthedocs.io/).

tl;dr - [this](coolamqp/framing/definitions.py) is **machine-generated** compile-time.
[this](coolamqp/framing/compilation/content_property.py) **generates classes run-time**,
and there are memoryviews **_everywhere_**. 

This is borderline absurd.

CoolAMQP is not a direct AMQP client - it also handles reconnections, transactional sending,
and so on, mostly via Futures. This means it has a certain opinion on how to 
handle AMQP, but you can feel the spirit of AMQP underneath. *API is stable*.


The project is actively maintained and used in a commercial project. Tests can run
either on Vagrant (Vagrantfile attached) or Travis CI, and run against RabbitMQ.

CoolAMQP won't touch your messages. It's your bags o'bytes, and your properties.

Enjoy!

_Watch out for memoryviews!_ They're here to stay.

[Short'n'sweet contributing guide](CONTRIBUTING.md)
[Change log](CHANGELOG.md)


## Notes
Assertions are sprinkled throughout the code. You may wish to run with optimizations enabled
if you need every CPU cycle you can get.

## Current limitations

* channel flow mechanism is not supported (#11)
* _confirm=True_ is not available if you're not RabbitMQ (#8)
* no Windows support (#9)
