import logging

from satella.coding.concurrent import TerminableThread

from coolamqp.clustering.events import ReceivedMessage
from coolamqp.objects import Queue, Message
from ..settings import queue_names, connect, LogFramesToFile


class Server(TerminableThread):
    def __init__(self, amqp):
        self.amqp = amqp
        super().__init__()
        self.consumers = []
        for queue_name in queue_names:
            cons, fut = self.amqp.consume(Queue(queue_name + '-repl'))
            self.consumers.append(cons)

    def loop(self):
        evt = self.amqp.drain(timeout=1.0)
        if isinstance(evt, ReceivedMessage):
            routing_key = evt.routing_key.tobytes().decode('utf8').replace('-repl', '')
            self.amqp.publish(Message(evt.body), routing_key=routing_key)


def run(notify_client, result_client, notify_server, server_result):
    logging.basicConfig(level=logging.WARNING)

    lftf = LogFramesToFile('server.txt')

    amqp = connect(on_fail=server_result, log_frames=lftf)
    server = Server(amqp)

    server.start()

    try:
        notify_server.get()
    except KeyboardInterrupt:
        pass

    server.terminate().join()

    lftf.close()
