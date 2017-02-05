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

It was considered whether to unserialize short fields, such as _routing_key_ or _exchange_, but it was decided against. 
Creating a new memoryview carries at least much overhead as an empty string, but there's no need to copy.
Plus, it's not known whether you will use these strings at all!

If you need to, you got memoryviews. Plus they support the \__eq__ protocol, which should cover most
use cases without even converting.
