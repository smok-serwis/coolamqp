CoolAMQP classes reference
==========================

Cluster-related things
----------------------

.. autoclass:: coolamqp.clustering.Cluster
    :members:

.. note:: If environment variable :code:`COOLAMQP_FORCE_SELECT_LISTENER` is defined, select will be used instead of epoll.
          This will automatically use select if epoll is not available (eg. Windows).

.. autoclass:: coolamqp.attaches.consumer.BodyReceiveMode
    :members:

.. autoclass:: coolamqp.attaches.consumer.Consumer
    :members:

Please note that :meth:`coolamqp.clustering.Cluster.consume` passes lot of it's
args and kwargs directly to the :class:`coolamqp.attaches.consumer.Consumer`.

Extra objects
-------------

.. autoclass:: coolamqp.objects.Message
    :members:

.. autoclass:: coolamqp.objects.ReceivedMessage
    :members:

.. autoclass:: coolamqp.objects.MessageProperties
    :members:

.. autoclass:: coolamqp.objects.Queue
    :members:

.. autoclass:: coolamqp.objects.Exchange
    :members:


