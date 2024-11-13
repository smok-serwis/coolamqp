Streams
=======

RabbitMQ 4 added a new feature called `streams <https://www.rabbitmq.com/docs/streams>`_ , perhaps to look more like Kafka.
Anyway, we fully support this feature, but there are a few caveats you must watch out for:

If you specify argument :code:`x-stream-offset` and aim to provide a number, please don't provide it as a string.
This will cause your connection to RabbitMQ to crash.
You can naturally provide "first" or "next" or "last".

Also, streams must be consumed with no_ack=False, otherwise it will fail.

Basically everything works `as documented <https://www.rabbitmq.com/docs/streams#consuming>`_. Happy usage!
