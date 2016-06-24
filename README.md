CoolAMQP
========

When you're tired of fucking with AMQP reconnects.

When a connection made by CoolAMQP to your broker fails, it will pick another
node, redeclare exchanges, queues, consumers and tell your application that
a disconnect happened.

CoolAMQP makes you forget about all the nasty corner cases about AMQP reconnection.

You only need to remember that:

1. Reconnects and redefinitions take a while.
 * Things will happen during that time. It is your responsibility to ensure that your distributed system is built to handle this
2. CoolAMQP will tell you when it senses losing broker connection.
 * It will also tell you when it regains the connection (that means that everything is redefined).
3. Delivering messages multiple times may happen.
 * Ensure you know when it happens. Keywords: message acknowledgement, amqp specification

As the project is in it's infancy stages, but actively maintained and used in a commercial project,
if you need a feature - just drop me a note or create a new issue here.


Now compatible with Python 3!

todo
----
* Allow binding queues with exchanges with a routing_key