# Caveats

Things to look out for

## memoryviews

Since CoolAMQP tries to be fast, it uses memoryviews everywhere. _ReceivedMessage_ properties, and message
properties therefore, are memoryviews. So, it you wanted to read the routing key a message was sent with,
or message's encoding, you should do:

```python
received_msg.routing_key.to_bytes()
received_msg.properties.content_encoding.to_bytes()
```

Only the _body_ property of the message will be a byte object (and not even that it you set an option
in Cluster.consume).

Note that YOU, when sending messages, should not use memoryviews. Pass proper byte objects and text objects
as required.

_AMQPError_'s returned to you via futures will also have memoryviews as _reply_text_!
