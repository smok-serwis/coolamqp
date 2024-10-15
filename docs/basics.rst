Usage basics
============

First off, you need a Cluster object:

.. autoclass:: coolamqp.clustering.Cluster
    :members:

You will need to initialize it with NodeDefinitions:

.. autoclass:: coolamqp.objects.NodeDefinition

You can send messages:

.. autoclass:: coolamqp.objects.Message

and receive them

.. autoclass:: coolamqp.objects.ReceivedMessage
    :members:

MessageProperties
-----------------

.. autoclass:: coolamqp.objects.MessageProperties
    :members:

.. autoclass:: coolamqp.framing.definitions.BasicContentPropertyList
    :members:
    :undoc-members:


Take care, as :class:`~coolamqp.objects.MessageProperties` will hash the
keys found and store it within non-GCable memory. So each "variant" of message
properties encountered will be compiled as a separate class.

Who am I talking to?
--------------------

:class:`coolamqp.clustering.Cluster` has a nice property, that will return None until the connection is established.
If it is, it will return something like this:

.. autoclass:: coolamqp.objects.ServerProperties
    :members:
