import threading
import Queue
import logging
import collections
import time
from .backends import ConnectionFailedError, RemoteAMQPError
from .messages import Exchange
from .events import ConnectionUp, ConnectionDown, ConsumerCancelled, MessageReceived
from .orders import SendMessage, DeclareExchange, ConsumeQueue, CancelQueue, \
                    AcknowledgeMessage, NAcknowledgeMessage, DeleteQueue, \
                    DeleteExchange

logger = logging.getLogger(__name__)


class ClusterHandlerThread(threading.Thread):
    """
    Thread that does bookkeeping for a Cluster
    """
    def __init__(self, cluster):
        """
        :param cluster: coolamqp.Cluster
        """
        threading.Thread.__init__(self)

        self.cluster = cluster
        self.is_terminating = False
        self.order_queue = collections.deque()    # queue for inbound orders
        self.event_queue = Queue.Queue()    # queue for tasks done
        self.connect_id = -1                # connectID of current connection

        self.declared_exchanges = {}        # declared exchanges, by their names
        self.queues_by_consumer_tags = {}   # listened queues, by their consumer tags

        self.backend = None

    def _reconnect(self):
        exponential_backoff_delay = 1

        while True:
            if self.backend is not None:
                self.backend.shutdown()
                self.backend = None

            self.connect_id += 1
            node = self.cluster.node_to_connect_to.next()
            logger.info('Connecting to %s', node)

            try:
                self.backend = self.cluster.backend(node, self)

                for exchange in self.declared_exchanges.itervalues():
                    self.backend.exchange_declare(exchange)

                for queue in self.queues_by_consumer_tags.itervalues():
                    self.backend.queue_declare(queue)
                    if queue.exchange is not None:
                        if isinstance(queue.exchange, Exchange):
                            self.backend.queue_bind(queue, queue.exchange)
                        else:
                            for exchange in queue.exchange:
                                self.backend.queue_bind(queue, queue.exchange)
                    self.backend.basic_consume(queue)

            except ConnectionFailedError as e:
                # a connection failure happened :(
                logger.warning('Connecting to %s failed due to %s', node, repr(e))
                self.cluster.connected = False
                if self.backend is not None:
                    self.backend.shutdown()
                    self.backend = None # good policy to release resources before you sleep
                time.sleep(exponential_backoff_delay)

                if self.is_terminating:
                    raise SystemError('Thread was requested to terminate')

                if exponential_backoff_delay < 60:
                    exponential_backoff_delay *= 2
                else:
                    exponential_backoff_delay = 60
            else:
                self.cluster.connected = True
                self.event_queue.put(ConnectionUp())
                break   # we connected :)


    def perform_order(self):
        order = self.order_queue.popleft()

        try:
            if isinstance(order, SendMessage):
                self.backend.basic_publish(order.message, order.exchange, order.routing_key)
            elif isinstance(order, DeclareExchange):
                self.backend.exchange_declare(order.exchange)
                self.declared_exchanges[order.exchange.name] = order.exchange
            elif isinstance(order, DeleteExchange):
                self.backend.exchange_delete(order.exchange)
                if order.exchange.name in self.declared_exchanges:
                    del self.declared_exchanges[order.exchange.name]
            elif isinstance(order, DeleteQueue):
                self.backend.queue_delete(order.queue)
            elif isinstance(order, ConsumeQueue):
                self.backend.queue_declare(order.queue)

                if order.queue.exchange is not None:
                    if isinstance(order.queue.exchange, Exchange):
                        self.backend.queue_bind(order.queue, order.queue.exchange)
                    else:
                        for exchange in order.queue.exchange:
                            self.backend.queue_bind(order.queue, order.queue.exchange)

                self.backend.basic_consume(order.queue)
                self.queues_by_consumer_tags[order.queue.consumer_tag] = order.queue
            elif isinstance(order, CancelQueue):
                try:
                    q = self.queues_by_consumer_tags.pop(order.queue.consumer_tag)
                except KeyError:
                    pass  # wat?
                else:
                    self.backend.basic_cancel(order.queue.consumer_tag)
                    self.event_queue.put(ConsumerCancelled(order.queue))
            elif isinstance(order, AcknowledgeMessage):
                if order.connect_id == self.connect_id:
                    self.backend.basic_ack(order.delivery_tag)
            elif isinstance(order, NAcknowledgeMessage):
                if order.connect_id == self.connect_id:
                    self.backend.basic_nack(order.delivery_tag)
        except RemoteAMQPError as e:
            logger.error('Remote AMQP error: %s', e)
            order.failed(e)  # we are allowed to go on
        except ConnectionFailedError:
            self.order_queue.appendleft(order)
            raise
        else:
            order.completed()

    def run(self):
        self._reconnect()

        while (not self.is_terminating) or len(self.order_queue) > 0:
            try:
                while len(self.order_queue) > 0:
                    self.perform_order()

                # just drain shit
                self.backend.process(max_time=2)

            except ConnectionFailedError as e:
                logger.warning('Connection to broker lost')
                self.cluster.connected = True
                self.event_queue.put(ConnectionDown())
                self._reconnect()

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
            queue = self.queues_by_consumer_tags.pop(consumer_tag)
        except KeyError:
            return  # what?

        self.event_queue.put(ConsumerCancelled(queue))

    ## methods to enqueue something into CHT to execute

    def _do_ackmessage(self, receivedMessage, on_completed=None):
        """
        Order acknowledging a message.
        :param receivedMessage: a ReceivedMessage object to ack
        :param on_completed: callable/0 to call when acknowledgemenet succeeded
        """
        self.order_queue.append(AcknowledgeMessage(receivedMessage.connect_id,
                                                   receivedMessage.delivery_tag,
                                                   on_completed=on_completed))


    def _do_nackmessage(self, receivedMessage, on_completed=None):
        """
        Order acknowledging a message.
        :param receivedMessage: a ReceivedMessage object to ack
        :param on_completed: callable/0 to call when acknowledgemenet succeeded
        """
        self.order_queue.put(NAcknowledgeMessage(receivedMessage.connect_id,
                                                 receivedMessage.delivery_tag,
                                                 on_completed=on_completed))
