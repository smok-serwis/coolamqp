CoolAMQP
========

**A Python client for RabbitMQ**

Why CoolAMQP?
-------------
* it supports all types of exchanges
* it works on Python 2 and on Windows
* tested against all versions of RabbitMQ 3.x and RabbitMQ 4.0
* AMQP 0.9.1 client that's native Python
* heavily optimized for speed
* geared towards interfacing with [RabbitMQ](https://www.rabbitmq.com/)
  * supports custom RabbitMQ commands, such as
    * [Connection blocking](https://www.rabbitmq.com/docs/connection-blocked)
    * [Publisher confirms](https://www.rabbitmq.com/docs/confirms#publisher-confirms)
    * [Negative Acknowledgements](https://www.rabbitmq.com/docs/nack)
* traceable using [opentracing](https://opentracing.io/)
* high coverage
* tested in production conditions
* full support for [streams](https://www.rabbitmq.com/docs/streams)
* 120 second stress tests are part of each release


**Warning!!** Since v1.3.1 development has been moved 
from [GitHub](https://github.com/smok-serwis/coolamqp) to this [GitLab](https://git.dms-serwis.com.pl/smokserwis/coolamqp).
To install the most latest CoolAMQP please use

```bash
pip install --index-url https://git.dms-serwis.com.pl/api/v4/groups/330/-/packages/pypi/simple coolamqp
```

Documentation (WIP) is available at [our site](http://smokserwis.docs.smok.co/coolamqp).

CoolAMQP uses [semantic versioning 2.0](https://semver.org/spec/v2.0.0.html).

tl;dr - [this](coolamqp/framing/definitions.py) is **machine-generated** compile-time.
[this](coolamqp/framing/compilation/content_property.py) **generates classes run-time**,
and there are memoryviews **_everywhere_**. 

This is borderline absurd.


The project is actively maintained and used in a commercial project. Tests can run
either on Vagrant (Vagrantfile attached) or Travis CI, and run against RabbitMQ.

CoolAMQP won't touch your messages. It's your bags o'bytes, and your properties.

Enjoy!

_Watch out for memoryviews!_ They're here to stay.

* [Short'n'sweet contributing guide](CONTRIBUTING.md)
* [Change log for past historical versions](https://github.com/smok-serwis/coolamqp/releases/)
* [Change log for recent versions, unreleased version](CHANGELOG.md)


## Notes
Assertions are sprinkled throughout the code. You may wish to run with optimizations enabled
if you need every CPU cycle you can get.

Note that if you define the environment variable of `COOLAMQP_FORCE_SELECT_LISTENER`, 
CoolAMQP will use select-based networking instead of epoll based.

## Current limitations

* channel flow mechanism is not supported (#11)
* _confirm=True_ is not available if you're not RabbitMQ (#8)


## Copyright holder change

Since SMOK sp. z o.o. was incorporated, it inherited all SMOK-related
IP of previous operator of the service, DMS Serwis s.c., which
continues to operate within it's designated company agreement.
From there stems the copyright holder name change.

And because I haven't been paid a penny for this work, I've assumed copyright personally.

## What is here

### [coolamqp](coolamqp/)

The core module

### [stress_tests](stress_tests/)

A series of stress tests to catch any race conditions

### [tests](tests/)

A series of unit tests that need an AMQP server listening.

### [compile_definitions](compile_definitions/)

A tool to generate [definitions.py](coolamqp/framing/definitions.py) from the AMQP specification 
[XML](https://www.rabbitmq.com/resources/specs/amqp0-9-1.extended.xml).

In order to compile the definitions:

* Make sure that you have `yapf` and `requests` installed
* then perform:
```python
python -m compile_definitions
```

and you're all set. The only files modified is
[definitions.py](coolamqp/framing/definitions.py).

### [docs](docs/)

Sources for the documentation, available
[here](http://smokserwis.docs.smok.co/coolamqp).

## Running unit tests

Unit tests are powered by nose. They require an available AMQP broker.
If you host the broker other than localhost, set the env *AMQP_HOST* to correct value.
The default username used is guest, and password is guest.

You can also run unit tests from Docker, if you wish so. To launch the unit test suite:

```bash
docker-compose up --build unittest
```

To launch the stress test suite

```bash
docker-compose up stress_tests
```
