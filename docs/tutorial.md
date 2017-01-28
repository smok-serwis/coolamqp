# Tutorial

If you want to connect to an AMQP broker, you need:
* it's address (and port)
* login and password
* name of the virtual host

An idea of a heartbeat interval would be good, but you can do without. Since CoolAMQP will support clusters
in the future, you should define the nodes first. You can do it using _NodeDefinition_.
See NodeDefinition's documentation for alternative ways to do this, but here we will use
the AMQP connection string.

```python
from coolamqp.objects import NodeDefinition

node = NodeDefinition('amqp://user@password:host/vhost')
```

_Cluster_ instances are used to interface with the cluster (or a single broker). It
accepts a list of nodes:

```python
from coolamqp.clustering import Cluster
cluster = Cluster([node])
cluster.start(wait=True)
```

_wait=True_ will block until connection is completed. After this, you can use other methods.