Advanced things
===============

.. autoclass:: coolamqp.uplink.connection.Connection
    :members:


Declaring anonymous queues
--------------------------

.. _anonymq:

In order to make use of an anonymous queue, you must first :meth:`coolamqp.clustering.Cluster.consume` it, since
:meth:`coolamqp.clustering.Cluster.declare` will use a separate channel, in which the queue will be invalid. It will
raise ValueError if you try to do that, anyway.

Anonymous queues must be auto_delete and exclusive, ValueError will be raised otherwise.
