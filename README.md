CoolAMQP
========
[![Build Status](https://travis-ci.org/smok-serwis/coolamqp.svg)](https://travis-ci.org/smok-serwis/coolamqp)
[![Test Coverage](https://codeclimate.com/github/smok-serwis/coolamqp/badges/coverage.svg)](https://codeclimate.com/github/smok-serwis/coolamqp/coverage)
[![Code Climate](https://codeclimate.com/github/smok-serwis/coolamqp/badges/gpa.svg)](https://codeclimate.com/github/smok-serwis/coolamqp)
[![Issue Count](https://codeclimate.com/github/smok-serwis/coolamqp/badges/issue_count.svg)](https://codeclimate.com/github/smok-serwis/coolamqp)
[![PyPI version](https://badge.fury.io/py/CoolAMQP.svg)](https://badge.fury.io/py/CoolAMQP)
[![PyPI](https://img.shields.io/pypi/pyversions/CoolAMQP.svg)]()
[![PyPI](https://img.shields.io/pypi/implementation/CoolAMQP.svg)]()
[![PyPI](https://img.shields.io/pypi/wheel/CoolAMQP.svg)]()
[![Documentation Status](https://readthedocs.org/projects/coolamqp/badge/?version=latest)](http://coolamqp.readthedocs.io/en/latest/?badge=develop)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)]()

A **magical** AMQP 0.9.1  client, that uses **heavy sorcery** to achieve speeds that other pure-Python AMQP clients cannot even hope to match.

Documentation (WIP) is available at [Read the Docs](http://coolamqp.readthedocs.io/).

CoolAMQP uses [semantic versioning 2.0](https://semver.org/spec/v2.0.0.html).

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


## Copyright holder change

Since SMOK sp. z o.o. was incorporated, it inherited all SMOK-related
IP of previous operator of the service, DMS Serwis s.c., which
continues to operate within it's designated company agreement.
From there stems the copyright holder name change.

## What is here

### [coolamqp](coolamqp/)

The core module

### [stress_tests](stress_tests/)

A series of stress tests to catch any race conditions

### [tests](tests/)

A series of unit tests that need an AMQP server listening.

### [compile_definitions](compile_definitions/)

A tool to generate [definitions.py](coolamqp/framing/definitions.py)
from [amqp-0-9-1.xml](resources/amqp0-9-1.xml)

In order to compile the definitions:

* Make sure that you have `yapf` installed
* then perform:
  ```python
  python -m compile_definitions
  ```
and you're all set. The only files modified is
[definitions.py](coolamqp/framing/definitions.py).

### [resources](resources/)

A downloaded from OASIS machine-readable AMQP 0.9.1 specification.

### [docs](docs/)

Sources for the documentation, available
[here](https://coolamqp.readthedocs.io/en/latest/).

## Running unit tests

Unit tests are powered by nose. They require an available AMQP broker.
If you host the broker other than localhost, set the env *AMQP_HOST* to correct value.
The default username used is guest, and password is guest.

You can also run unit tests from Docker, if you wish so. To launch the unit test suite:

```bash
docker-compose up tests
```

To launch the stress test suite

```bash
docker-compose up stress_tests
```
