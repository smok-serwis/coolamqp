CoolAMQP
========

When you're tired of fucking with AMQP reconnects.

When a connection made by CoolAMQP to your broker fails, it will pick another
node, redeclare exchanges, queues, consumers and tell your application that
a disconnect happened.
