coolamqp
========

The one library to rule them all.

This is a fault-tolerant-able AMQP library.

What other libraries don't, is reconnect to another node 
in the cluster if one goes down, restore all queues that were
listened to, and inform the user explicitly when connection goes down
or up to orchestrate itself properly and prepare for eg. missing messages.

tl;dr
-----
This spawns a thread in the background for every AMQP cluster you connect to. That
thread performs all actions associated with it.