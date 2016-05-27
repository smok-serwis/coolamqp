import threading
import Queue
import logging

logger = logging.getLogger(__name__)



class ClusterHandlerThread(threading.Thread):
    """
    Thread that does bookkeeping for a Cluster
    """
    def __init__(self, cluster):
        """
        :param cluster: coolamqp.Cluster
        """

        self.cluster = cluster
        self.is_terminating = False
        self.order_queue = Queue.Queue()    # queue for inbound orders
        self.event_queue = Queue.Queue()    # queue for tasks done
        self.connect_id = -1                # connectID of current connection

        self.declared_exchanges = {}        # declared exchanges, by their names
        self.subscribed_queues = []         # list of subscribed queues


    def _reconnect(self):
        node = self.cluster.node_to_connect_to.next()

        logger.info('Connecting to ', node)





    def terminate(self):
        """
        Called by Cluster. Tells to finish all jobs and quit.
        Unacked messages will not be acked. If this is called, connection may die at any time.
        """
        self.is_terminating = True


    ## methods to enqueue something into CHT to execute

    def _do_ackmessage(self, receivedMessage, on_completed=None):
        """
        Order acknowledging a message.
        :param receivedMessage: a ReceivedMessage object to ack
        :param on_completed: callable/0 to call when acknowledgemenet succeeded
        """
        raise NotImplementedError


    def _do_nackmessage(self, receivedMessage, on_completed=None):
        """
        Order acknowledging a message.
        :param receivedMessage: a ReceivedMessage object to ack
        :param on_completed: callable/0 to call when acknowledgemenet succeeded
        """
        raise NotImplementedError