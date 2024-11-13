Tutorials
=========

Send and receive
----------------

In this tutorial we'll learn how to declare a named queue and send a message to it with acknowledgement:

First we need to connect to the server. Let's assume you have configured a virtual host called /vhost

.. code-block:: python

    from coolamqp.clustering import Cluster
    from coolamqp.objects import NodeDefinition

    nd = NodeDefinition('amqp://127.0.0.1:5672/vhost', user='test', password='test', heartbeat=30)
    c = Cluster(nd)
    c.start()

Then we'll need to declare a queue:


.. code-block:: python
    from coolamqp.objects import Queue

    queue = Queue('my-named-queue')
    c.declare(queue).result()

You'll be calling :code:`result()` on most of CoolAMQP's calls, as they return futures that complete when the task is done.
Now let's try subscribing to this queue:

.. code-block:: python

    def handle_message(msg):
        print(msg.body.tobytes().encode('utf-8'))
        msg.ack()

    cons, fut = c.consume(queue, no_ack=False, on_message=handle_message)
    fut.result()

Notice the :code:`tobytes()`. This is because CoolAMQP by default returns most of it's received bytes as memoryviews,
for speed's sake.

Also, your message handler is executed within the CoolAMQP's connection thread, so don't block for too long.

Now it's time to send a message:

.. code-block:: python

    from coolamqp.objects import Message
    c.publish(Message(b'my bag of bytes'), routing_key='my-named-queue', confirm=True).result()

Without the confirm flag, publish would not return the future.

Congratulations, you've just send and received a message! Now it's time to do some cleanup. First, we cancel the consumer,
and then disconnect from the server

.. code-block:: python

    cons.cancel().result()
    c.shutdown()

Fanout exchanges
----------------

Now let's try to do a fanout exchange:


.. code-block:: python

    from coolamqp.clustering import Cluster
    from coolamqp.objects import NodeDefinition, Exchange

    nd = NodeDefinition('amqp://127.0.0.1:5672/vhost', user='test', password='test', heartbeat=30)
    c = Cluster(nd)
    c.start()
    xchg = Exchange('my-exchange', type='fanout')

Now let's make two queues that will bind to this queue:


.. code-block:: python

    from coolamqp.objects import Queue

    q1 = Queue('my-queue-1', exchange=xchg)
    q2 = Queue('my-queue-2', exchange=xchg)

    def handle_message(msg):
        print(msg.body.tobytes().encode('utf-8'))
        msg.ack()

    c.consume(q1, on_message=handle_message, no_ack=False)
    c.consume(q2, on_message=handle_message, no_ack=False)

Note how you did not have to call :meth:`coolamqp.cluster.Cluster.declare`. Consume will declare constructs of arbitrary
complexity, if they can be derived from the queue objects you passed it.

And let's try to send something to this exchange:

.. code-block:: python

    from coolamqp.objects import Message
    c.publish(Message(b'my bag of bytes'), exchange=xchg, confirm=True).result()

And voila, we're done here!

Topic exchanges
---------------

Topic exchanges are a bit harder. Let's try them:

.. code-block:: python

    from coolamqp.clustering import Cluster
    from coolamqp.objects import NodeDefinition, Exchange

    nd = NodeDefinition('amqp://127.0.0.1:5672/vhost', user='test', password='test', heartbeat=30)
    c = Cluster(nd)
    c.start()
    xchg = Exchange('my-exchange', type='topic')

    def handle_message(msg):
        print(msg.body.tobytes().encode('utf-8'))
        msg.ack()

    queue = Queue(exchange=xchg, routing_key=b'test')
    cons, fut = self.c.consume(queue, no_ack=False, on_message=handle_message)
    fut.result()
    self.c.publish(Message(b'test'), xchg, routing_key=b'test', confirm=True).result()
    self.c.publish(Message(b'test'), xchg, routing_key=b'test2', confirm=True).result()

Note that the first message arrived, and the second did not. Also, notice how you didn't have to call
:meth:`~coolamqp.clustering.Cluster.declare` a single time, :meth:`~coolamqp.clustering.Cluster.consume` did all of that work for you

