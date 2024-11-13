How to guide
============

Connecting to a broker
----------------------

If you want to connect to an AMQP broker, you need:
* its address (and port)
* login and password
* name of the virtual host

An idea of a heartbeat interval would be good, but you can do without. Since CoolAMQP will support clusters
in the future, you should define the nodes first. You can do it using _NodeDefinition_.
See NodeDefinition's documentation for alternative ways to do this, but here we will use
the AMQP connection string.

.. autoclass:: coolamqp.objects.NodeDefinition
    :members:

.. code-block:: python

    from coolamqp.objects import NodeDefinition

    node = NodeDefinition('amqp://user@password:host/vhost')

Cluster instances are used to interface with the cluster (or a single broker). It
accepts a list of nodes:

.. code-block:: python

    from coolamqp.clustering import Cluster
    cluster = Cluster(node, name='My Cluster')
    cluster.start(wait=True)

*wait=True* will block until connection is completed. After this, you can use other methods.

*name* is optional. If you specify it, and have setproctitle_ installed, the thread will
receive a provided label, postfixed by **AMQP listener thread**.

.. _setproctitle: https://pypi.org/project/setproctitle/

Publishing and consuming
------------------------

Connecting is boring. After we do, we want to do something! Let's try sending a message, and receiving it. To do that,
you must first define a queue, and register a consumer.

.. code-block:: python

    from coolamqp.objects import Queue

    queue = Queue(u'my_queue', auto_delete=True, exclusive=True)

    consumer, consume_confirm = cluster.consume(queue, no_ack=False)
    consume_confirm.result()    # wait for consuming to start

This will create an auto-delete and exclusive queue. After than, a consumer will be registered for this queue.
_no_ack=False_ will mean that we have to manually confirm messages.

You should specify a callback. It will be executed in receiving thread's context, so it can't block for long.
If you're looking for receiving messages yourself, familiarize yourself with :meth:`coolamqp.clustering.Cluster.drain`.

_consumer_ is a _Consumer_ object. This allows us to do some things with the consumer (such as setting QoS),
but most importantly it allows us to cancel it later. _consume_confirm_ is a _Future_, that will succeed
when AMQP _basic.consume-ok_ is received.

To send a message we need to construct it first, and later publish:

.. code-block:: python

    from coolamqp.objects import Message, MessageProperties

    msg = Message(b'hello world', properties=MessageProperties())
    cluster.publish(msg, routing_key=u'my_queue')

The default exchange is the direct exchange, which will target the queue whose name is equal to routing_key.

This creates a message with no properties, and sends it through default (direct) exchange to our queue.
Note that CoolAMQP simply considers your messages to be bags of bytes + properties. It will not modify them,
nor decode, and will always expect and return bytes.

To actually get our message, we need to start a consumer first. To do that, just invoke:

.. code-block:: python

    cons, fut = cluster.consume(Queue('name of the queue'), **kwargs)

Where kwargs are passed directly to Consumer class.
**cons** is a Consumer object, and **fut** is a Future that will happen when listening has been registered on target
server. However, not providing a

.. autoclass:: coolamqp.attaches.Consumer
    :members:

Declaring anonymous queue
-------------------------

.. _anonymq:

In order to make use of an anonymous queue, you must first :meth:`coolamqp.clustering.Cluster.consume` it, since
:meth:`coolamqp.clustering.Cluster.declare` will use a separate channel, in which the queue will be invalid. It will
raise ValueError if you try to do that, anyway.

Anonymous queues must be auto_delete and exclusive, ValueError will be raised otherwise.
