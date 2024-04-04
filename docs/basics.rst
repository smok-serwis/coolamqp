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
entire object (keys and values) and store it within non-GCable memory.

This is done in order to facilitate reuse and speed/memory consumption.
If you're looking forward to shipping each message with different properties,
please wait until #51_ is fixed.

.. _#51: https://github.com/smok-serwis/coolamqp/issues/51

