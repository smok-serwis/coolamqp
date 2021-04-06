The changelog is kept as [release notes](https://github.com/smok-serwis/coolamqp/releases/)
on GitHub. This file serves to only note what changes
have been made so far, between releases.

# v1.2.14

* added __slots__ to `AMQPContentPropertyList`
    * without __slots__ in the base class the compiled classes
      gained no boost from __slots__ being specified for them whatsoever
* fixed __str__ in `AMQPContentPropertyList`
* added __slots__ to `AMQPFrame`
* removed redundant logging in `coolamqp.uplink.connection.connection`
