# coding=UTF-8
"""
Core objects used in CoolAMQP
"""
import threading
import uuid
import six
import logging
import concurrent.futures

from coolamqp.framing.definitions import BasicContentPropertyList as MessageProperties

__all__ = ('Message', 'ReceivedMessage', 'MessageProperties', 'Queue', 'Exchange', 'Future')

logger = logging.getLogger(__name__)

EMPTY_PROPERTIES = MessageProperties()


class Message(object):
    """
    An AMQP message. Has a binary body, and some properties.

    Properties is a highly regularized class - see coolamqp.framing.definitions.BasicContentPropertyList
    for a list of possible properties.
    """

    Properties = MessageProperties  # an alias for easier use

    def __init__(self, body, properties=None):
        """
        Create a Message object.

        Please take care with passing empty bodies, as py-amqp has some failure on it.

        :param body: stream of octets
        :type body: str (py2) or bytes (py3)
        :param properties: AMQP properties to be sent along.
                           default is 'no properties at all'
                           You can pass a dict - it will be passed to MessageProperties,
                           but it's slow - don't do that.
        :type properties: MessageProperties instance, None or a dict
        """
        if isinstance(body, six.text_type):
            raise TypeError('body cannot be a text type!')
        self.body = six.binary_type(body)

        if isinstance(properties, dict):
            self.properties = MessageProperties(**properties)
        elif properties is None:
            self.properties = EMPTY_PROPERTIES
        else:
            self.properties = properties


LAMBDA_NONE = lambda: None

class ReceivedMessage(Message):
    """
    A message that was received from the AMQP broker.

    It additionally has an exchange name, routing key used, it's delivery tag,
    and methods for ack() or nack().

    Note that if the consumer that generated this message was no_ack, .ack() and .nack() are no-ops.
    """

    def __init__(self, body, exchange_name, routing_key,
                 properties=None,
                 delivery_tag=None,
                 ack=None,
                 nack=None):
        """
        :param body: message body. A stream of octets.
        :type body: str (py2) or bytes (py3)
        :param cht: parent ClusterHandlerThread that emitted this message
        :param connect_id: connection ID. ClusterHandlerThread will check this in order
            not to ack messages that were received from a dead connection
        :param exchange_name: name of exchange this message was submitted to
        :param routing_key: routing key with which this message was sent
        :param properties: a suitable BasicContentPropertyList subinstance

        :param delivery_tag: delivery tag assigned by AMQP broker to confirm this message
        :param ack: a callable to call when you want to ack (via basic.ack) this message. None if received
             by the no-ack mechanism
        :param nack: a callable to call when you want to nack (via basic.reject) this message. None if received
             by the no-ack mechanism
        """
        Message.__init__(self, body, properties=properties)

        self.delivery_tag = delivery_tag
        self.exchange_name = exchange_name
        self.routing_key = routing_key

        self.ack = ack or LAMBDA_NONE
        self.nack = nack or LAMBDA_NONE


class Exchange(object):
    """
    This represents an Exchange used in AMQP.
    This is hashable.
    """

    direct = None   # the direct exchange

    def __init__(self, name='', type='direct', durable=True, auto_delete=False):
        self.name = name
        self.type = type
        self.durable = durable
        self.auto_delete = auto_delete

    def __hash__(self):
        return self.name.__hash__()

    def __eq__(self, other):
        return self.name == other.name

Exchange.direct = Exchange()


class Queue(object):
    """
    This object represents a Queue that applications consume from or publish to.
    """

    def __init__(self, name=u'', durable=False, exchange=None, exclusive=False, auto_delete=False):
        """
        Create a queue definition.

        :param name: name of the queue.
            Take special care if this is empty. If empty, this will be filled-in by the broker
            upon declaration. If a disconnect happens, and connection to other node is
            reestablished, this name will CHANGE AGAIN, and be reflected in this object.
            This change will be done before CoolAMQP signals reconnection.
        :param durable: Is the queue durable?
        :param exchange: Exchange for this queue to bind to. None for no binding.
        :param exclusive: Is this queue exclusive?
        :param auto_delete: Is this queue auto_delete ?
        """
        self.name = name.encode('utf8')
        # if name is '', this will be filled in with broker-generated name upon declaration
        self.durable = durable
        self.exchange = exchange
        self.auto_delete = auto_delete
        self.exclusive = exclusive

        self.anonymous = name == ''  # if this queue is anonymous, it must be regenerated upon reconnect

        self.consumer_tag = name if name != '' else uuid.uuid4().hex    # consumer tag to use in AMQP comms

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Future(concurrent.futures.Future):
    """
    Future returned by asynchronous CoolAMQP methods.

    A strange future (only one thread may wait for it)
    """
    __slots__ = ('lock', 'completed', 'successfully', '_result', 'running', 'callables', 'cancelled')


    def __init__(self):
        self.lock = threading.Lock()
        self.lock.acquire()

        self.completed = False
        self.successfully = None
        self._result = None
        self.cancelled = False
        self.running = True

        self.callables = []

    def add_done_callback(self, fn):
        self.callables.append(fn)

    def result(self, timeout=None):
        assert timeout is None, u'Non-none timeouts not supported'
        self.lock.acquire()
        self.lock.release()

        if self.completed:
            if self.successfully:
                return self._result
            else:
                raise self._result
        else:
            if self.cancelled:
                raise concurrent.futures.CancelledError()
            else:
                # it's invalid to release the lock, not do the future if it's not cancelled
                raise RuntimeError(u'Invalid state!')

    def cancel(self):
        """
        When cancelled, future will attempt not to complete (completed=False).
        :return:
        """
        self.cancelled = True

    def __finish(self, result, successful):
        self.completed = True
        self.successfully = successful
        self._result = result
        self.lock.release()

        for callable in self.callables:
            try:
                callable(self)
            except Exception as e:
                logger.error('Exception in base order future: %s', repr(e))
            except BaseException as e:
                logger.critical('WILD NASAL DEMON APPEARED: %s', repr(e))

    def set_result(self, result=None):
        self.__finish(result, True)

    def set_exception(self, exception):
        self.__finish(exception, False)

    def set_cancel(self):
        """Executor has seen that this is cancelled, and discards it from list of things to do"""
        assert self.cancelled
        self.completed = False
        self.lock.release()


class NodeDefinition(object):
    """
    Definition of a reachable AMQP node.

    This object is hashable.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a cluster node definition.

            a = ClusterNode(host='192.168.0.1', user='admin', password='password',
                            virtual_host='vhost')

        or

            a = ClusterNode('192.168.0.1', 'admin', 'password')

        Additional keyword parameters that can be specified:
            heartbeat - heartbeat interval in seconds
            port - TCP port to use. Default is 5672
        """

        self.heartbeat = kwargs.pop('heartbeat', None)
        self.port = kwargs.pop('port', 5672)

        if len(kwargs) > 0:
            # Prepare arguments for amqp.connection.Connection
            self.host = kwargs['host']
            self.user = kwargs['user']
            self.password = kwargs['password']
            self.virtual_host = kwargs.get('virtual_host', '/')
        elif len(args) == 3:
            self.host, self.user, self.password = args
            self.virtual_host = '/'
        elif len(args) == 4:
            self.host, self.user, self.password, self.virtual_host = args
        else:
            raise NotImplementedError #todo implement this

    def __str__(self):
        return six.text_type(b'amqp://%s:%s@%s/%s'.encode('utf8') % (self.host, self.port, self.user, self.virtual_host))