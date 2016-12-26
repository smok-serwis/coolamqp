# coding=UTF-8
import threading
from six.moves import queue
import six
import logging
import collections
import time
from .backends import ConnectionFailedError, RemoteAMQPError, Cancelled
from .messages import Exchange
from .events import ConnectionUp, ConnectionDown, ConsumerCancelled, MessageReceived
from .orders import SendMessage, DeclareExchange, ConsumeQueue, CancelQueue, \
                    AcknowledgeMessage, NAcknowledgeMessage, DeleteQueue, \
                    DeleteExchange, SetQoS, DeclareQueue

logger = logging.getLogger(__name__)


class _ImOuttaHere(Exception):
    """Thrown upon thread terminating.
    Thrown only if complete_remaining_upon_termination is False"""


class ClusterHandlerThread(threading.Thread):
    """
    Thread that does bookkeeping for a Cluster.
    """
    def __init__(self, cluster):
        """
        :param cluster: coolamqp.Cluster
        """
        threading.Thread.__init__(self)

        self.cluster = cluster
        self.daemon = True      # if you don't explicitly wait for me, that means you don't need to
        self.is_terminating = False
        self.complete_remaining_upon_termination = False
        self.order_queue = collections.deque()    # queue for inbound orders
        self.event_queue = queue.Queue()    # queue for tasks done
        self.connect_id = -1                # connectID of current connection

        self.declared_exchanges = {}        # declared exchanges, by their names
        self.queues_by_consumer_tags = {}   # tuple of (subbed queue, no_ack::bool), by consumer tags

        self.backend = None
        self.first_connect = True

        self.qos = None # or tuple (prefetch_size, prefetch_count) if QoS set

    def _reconnect_attempt(self):
        """Single attempt to regain connectivity. May raise ConnectionFailedError"""
        self.backend = None
        if self.backend is not None:
            self.backend.shutdown()
            self.backend = None

        self.connect_id += 1
        node = six.next(self.cluster.node_to_connect_to)
        logger.info('Connecting to %s', node)

        self.backend = self.cluster.backend(node, self)

        if self.qos is not None:
            pre_siz, pre_cou, glob = self.qos
            self.backend.basic_qos(pre_siz, pre_cou, glob)

        for exchange in self.declared_exchanges.values():
            self.backend.exchange_declare(exchange)

        failed_queues = []
        for queue, no_ack in self.queues_by_consumer_tags.values():
            while True:
                try:
                    self.backend.queue_declare(queue)
                    if queue.exchange is not None:
                        self.backend.queue_bind(queue, queue.exchange)
                    self.backend.basic_consume(queue, no_ack=no_ack)
                    logger.info('Consuming from %s no_ack=%s', queue, no_ack)
                except RemoteAMQPError as e:
                    if e.code in (403, 405):  # access refused, resource locked
                        # Ok, queue, what should we do?
                        if queue.locked_after_reconnect == 'retry':
                            time.sleep(0.1)
                            continue    # retry until works
                        elif queue.locked_after_reconnect == 'cancel':
                            self.event_queue.put(ConsumerCancelled(queue, ConsumerCancelled.REFUSED_ON_RECONNECT))
                            failed_queues.append(queue)
                        elif queue.locked_after_reconnect == 'defer':
                            self.order_queue.append(ConsumeQueue(queue, no_ack=no_ack))
                            failed_queues.append(queue)
                        else:
                            raise Exception('wtf')
                    else:
                        raise  # idk
                break

        for failed_queue in failed_queues:
            del self.queues_by_consumer_tags[failed_queue.consumer_tag]

    def _reconnect(self):
        """Regain connectivity to cluster. May block for a very long time,
        as it will not """
        exponential_backoff_delay = 1

        while not self.cluster.connected:
            try:
                self._reconnect_attempt()
            except ConnectionFailedError as e:
                # a connection failure happened :(
                logger.warning('Connecting failed due to %s while connecting and initial setup', repr(e))
                self.cluster.connected = False
                if self.backend is not None:
                    self.backend.shutdown()
                    self.backend = None # good policy to release resources before you sleep
                time.sleep(exponential_backoff_delay)

                if self.is_terminating and (not self.complete_remaining_upon_termination):
                    raise _ImOuttaHere()

                exponential_backoff_delay = min(60, exponential_backoff_delay * 2)
            else:
                logger.info('Connected to AMQP broker via %s', self.backend)
                self.cluster.connected = True
                self.event_queue.put(ConnectionUp(initial=self.first_connect))
                self.first_connect = False


    def perform_order(self):
        order = self.order_queue.popleft()

        try:
            if order.cancelled:
                logger.debug('Order %s was cancelled', order)
                order._failed(Cancelled())
                return

            if isinstance(order, SendMessage):
                self.backend.basic_publish(order.message, order.exchange, order.routing_key)
            elif isinstance(order, SetQoS):
                self.qos = order.qos
                pre_siz, pre_cou, glob = order.qos
                self.backend.basic_qos(pre_siz, pre_cou, glob)
            elif isinstance(order, DeclareExchange):
                self.backend.exchange_declare(order.exchange)
                self.declared_exchanges[order.exchange.name] = order.exchange
            elif isinstance(order, DeleteExchange):
                self.backend.exchange_delete(order.exchange)
                if order.exchange.name in self.declared_exchanges:
                    del self.declared_exchanges[order.exchange.name]
            elif isinstance(order, DeclareQueue):
                self.backend.queue_declare(order.queue)
            elif isinstance(order, DeleteQueue):
                self.backend.queue_delete(order.queue)
            elif isinstance(order, ConsumeQueue):
                if order.queue.consumer_tag in self.queues_by_consumer_tags:
                    order._completed()
                    return    # already consuming, belay that

                self.backend.queue_declare(order.queue)

                if order.queue.exchange is not None:
                    self.backend.queue_bind(order.queue, order.queue.exchange)

                self.backend.basic_consume(order.queue, no_ack=order.no_ack)
                self.queues_by_consumer_tags[order.queue.consumer_tag] = order.queue, order.no_ack
            elif isinstance(order, CancelQueue):
                try:
                    q, no_ack = self.queues_by_consumer_tags.pop(order.queue.consumer_tag)
                except KeyError:
                    pass  # wat?
                else:
                    self.backend.basic_cancel(order.queue.consumer_tag)
                    self.event_queue.put(ConsumerCancelled(order.queue, ConsumerCancelled.USER_CANCEL))
            elif isinstance(order, AcknowledgeMessage):
                if order.connect_id == self.connect_id:
                    self.backend.basic_ack(order.delivery_tag)
            elif isinstance(order, NAcknowledgeMessage):
                if order.connect_id == self.connect_id:
                    self.backend.basic_reject(order.delivery_tag)
        except RemoteAMQPError as e:
            logger.error('Remote AMQP error: %s', e)
            order._failed(e)  # we are allowed to go on
        except ConnectionFailedError as e:
            logger.error('Connection failed while %s: %s', order, e)
            self.order_queue.appendleft(order)
            raise
        else:
            order._completed()

    def __run_wrap(self):   # throws _ImOuttaHere
        # Loop while there are things to do
        while (not self.is_terminating) or (len(self.order_queue) > 0):
            try:
                while len(self.order_queue) > 0:
                    self.perform_order()

                # just drain shit
                self.backend.process(max_time=0.05)
            except ConnectionFailedError as e:
                logger.warning('Connection to broker lost: %s', e)
                self.cluster.connected = False
                self.event_queue.put(ConnectionDown())

                # =========================== remove SendMessagees with discard_on_fail
                my_orders = []      # because order_queue is used by many threads
                while len(self.order_queue) > 0:
                    order = self.order_queue.popleft()
                    if isinstance(order, SendMessage):
                        if order.message.discard_on_fail:
                            order._discard()
                            continue

                    my_orders.append(order)

                # Ok, we have them in order of execution. Append-left in reverse order
                # to preserve previous order
                for order in reversed(my_orders):
                    my_orders.appendleft(order)

            self._reconnect()

    def run(self):
        try:
            self._reconnect()
            self.__run_wrap()
        except _ImOuttaHere:
            pass

        assert self.is_terminating
        if self.cluster.connected or (self.backend is not None):
            if self.backend is not None:
                self.backend.shutdown()
                self.backend = None

            self.cluster.connected = False

    def terminate(self):
        """
        Called by Cluster. Tells to finish all jobs and quit.
        Unacked messages will not be acked. If this is called, connection may die at any time.
        """
        self.is_terminating = True

    ## events called
    def _on_recvmessage(self, body, exchange_name, routing_key, delivery_tag, properties):
        """
        Upon receiving a message
        """
        from .messages import ReceivedMessage

        self.event_queue.put(MessageReceived(ReceivedMessage(body, self,
                                                             self.connect_id,
                                                             exchange_name,
                                                             routing_key,
                                                             properties,
                                                             delivery_tag=delivery_tag)))

    def _on_consumercancelled(self, consumer_tag):
        """
        A consumer has been cancelled
        """
        try:
            queue, no_ack = self.queues_by_consumer_tags.pop(consumer_tag)
        except KeyError:
            return  # what?

        self.event_queue.put(ConsumerCancelled(queue, ConsumerCancelled.BROKER_CANCEL))

    ## methods to enqueue something into CHT to execute

    def _do_ackmessage(self, receivedMessage, on_completed=None):
        """
        Order acknowledging a message.
        :param receivedMessage: a ReceivedMessage object to ack
        :param on_completed: callable/0 to call when acknowledgemenet succeeded
        :return: an AcknowledgeMess
        """
        a = AcknowledgeMessage(receivedMessage.connect_id,
                                                   receivedMessage.delivery_tag,
                                                   on_completed=on_completed)
        self.order_queue.append(a)
        return a


    def _do_nackmessage(self, receivedMessage, on_completed=None):
        """
        Order acknowledging a message.
        :param receivedMessage: a ReceivedMessage object to ack
        :param on_completed: callable/0 to call when acknowledgemenet succeeded
        """
        a = NAcknowledgeMessage(receivedMessage.connect_id,
                                receivedMessage.delivery_tag,
                                on_completed=on_completed)
        self.order_queue.append(a)
        return a
