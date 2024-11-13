What's new?
===========

CoolAMQP 2.0.0 marks a slight philosophy shift. Whereas 1.x used auto-generated UUID names, 2.0 will let the server
pick their names for themselves.

It also forbids some combinations of Queue arguments, and makes the default values more palatable, so for example
a naked :class:`coolamqp.objects.Queue` will be anonymous, non-durable, exclusive and auto-delete.

Cluster.publish
---------------

:meth:`coolamqp.clustering.Cluster.publish` has no longer the tx param, which has been deprecated.

Queues
------

Following queues will fail now:

* auto_delete and durable
* anonymous and durables
* anonymous and not exclusives
* anonymous and not auto_delete
* auto_delete and not exclusive and not anonymous

Following will emit a warning:

* exclusive and auto_delete - DeprecationWarning, since they're removing it in RabbitMQ 4.0
* not anonymous, auto_delete and not exclusive - UserWarning, since this makes little sense

Anonymous queues
----------------

They are back. Besides, anything that you will pass to :meth:`coolamqp.clustering.Cluster.consume` will be declared, be
it an exchange, a queue or such shit. This allows you to declare anonymous queues. Refer to :ref:`anonymq` on how to do it.
