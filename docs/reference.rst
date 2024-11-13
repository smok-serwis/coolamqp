CoolAMQP classes reference
==========================

Cluster-related things
----------------------

.. autoclass:: coolamqp.clustering.Cluster
    :members:

.. note:: If environment variable :code:`COOLAMQP_FORCE_SELECT_LISTENER` is defined, select will be used instead of epoll.


.. autoclass:: coolamqp.attaches.consumer.BodyReceiveMode
    :members:

.. autoclass:: coolamqp.attaches.consumer.Consumer
    :members:
    :undoc-members:

Please note that :meth:`coolamqp.clustering.Cluster.consume` passes lot of it's
args and kwargs directly to the :class:`coolamqp.attaches.consumer.Consumer`.

Extra objects
-------------

.. class:: coolamqp.objects.Message
    :members:

.. class:: coolamqp.objects.ReceivedMessage
    :members:

.. class:: coolamqp.objects.MessageProperties
    :members:

.. class:: coolamqp.objects.Queue
    :members:

.. class:: coolamqp.objects.Exchange
    :members:


