Previous release notes are hosted on [GitHub](https://github.com/smok-serwis/coolamqp/releases).
Since v1.3.2 they'll be put here and in release description.

v2.1.0
======

* removed extra logging from argumentify
* user will be notified upon declaring an auto-delete durable exchange
* deprecated Consumer(fail_on_first_time_resource_locked)
* we now support [streams](https://www.rabbitmq.com/docs/streams)

v2.0.0
======

* **CoolAMQP switches now primarily to support RabbitMQ.** If it by accident supports your server, then that is a 
  pure coincidence and nothing is guaranteed.
* changes to Queues:
  * anonymous queues are back, for usage refer [here](https://smokserwis.docs.smok.co/coolamqp/advanced.html)
  * changed some default arguments for Queues for them to better make sense
  * some argument combinations just raise ValueError
  * PendingDeprecationWarning changed into a DeprecationWarning
  * added support for headers and topic exchanges
* changes to Cluster:
  * declare will refuse to declare an anonymous queue
  * renamed publish(tx) to publish(confirm)
  * declare will expect qos to be given as an integer, and will be set as prefetch_count, since RabbitMQ no longer
    supports prefetch_size
    * same can be said of Consumer.set_qos(prefetch_count)


* fixed a bug wherein bad invocation of NodeDefinition would result in an exception

v1.5.0
======

* added properties to identify the server

v1.4.4
======

* added unit tests for RabbitMQ 4.0

v1.4.3
======

* bugfix regarding deadlettering queues
* prefetch_size will be forced to 0 to better comply with [RabbitMQ](https://www.rabbitmq.com/docs/specification#method-status-basic.qos)
    * and a DeprecationWarning will be shown to people who try to set something else. 0 will be forced upon them anyway.

v1.4.2
======

* fixed and unit tested the topic exchanges
* fixed declare documentation
* added docs regarding consume method.
* added testing topic exchanges
* bugfix regarding deadlettering queues
* prefetch_size will be forced to 0 to better comply with [RabbitMQ](https://www.rabbitmq.com/docs/specification#method-status-basic.qos)
    * and a DeprecationWarning will be shown to people who try to set something else. 0 will be forced upon them anyway.

v1.4.1
======

* fixed a bug while setting up connection

v1.2.16
=======

* removed the requirement for a Queue that for it to be equal to other Queue if their types do match
* compile_definitions will now depend on requests
* added support for infinite (None) timeouts during start
* stress tests will run for 120 seconds now
* stress tests will be harder, and use more queues
* added arguments to queues, queue binds and exchanges
* creating auto_delete non-exclusive queues will be met with a [PendingDeprecationWarning](https://www.rabbitmq.com/blog/2021/08/21/4.0-deprecation-announcements)
* added unit tests for Python 2.7
