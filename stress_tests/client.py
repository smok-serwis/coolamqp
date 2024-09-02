import logging
import random
import time
import typing as tp
import uuid
from collections import deque
from queue import Empty

from satella.coding.concurrent import TerminableThread

from coolamqp.clustering.events import ReceivedMessage, NothingMuch
from coolamqp.objects import Queue, Message
from .settings import connect, queue_names, LogFramesToFile

logger = logging.getLogger(__name__)

MESSAGES_PER_SECOND_PER_CONNECTION = 0.5
CONNECTIONS_PER_SECOND = 0.9
DISCONNECTS_PER_SECOND_PER_CONNECTION = 0.1
ANSWER_PROBABILITY = 0.7

RUNNING_INTERVAL = 60       # run for 60 seconds



def run_multiple_if_probability(probability: float, callable: tp.Callable[[], None]) -> None:
    prob = random.random()
    while prob < probability:
        try:
            callable()
        except Exception as e:
            return
        prob = random.random()


def run_if_probability(probability: float, callable: tp.Callable[[], None]) -> None:
    if random.random() < probability:
        try:
            return callable()
        except Exception as e:
            pass


class Connection:
    """
    This binds to queues called forth in settings and pushes messages to this name + "-repl"
    """

    CONNECTION_COUNTER = 0

    def __init__(self, cad_thread: 'ConnectAndDisconnectThread'):
        """:raises ValueError: not more free names available"""
        self.cad_thread = cad_thread
        try:
            self.name = self.cad_thread.free_names.popleft()
        except IndexError:
            logger.warning('Ran out of free names')
            raise ValueError('Cannot create a connection %s - ran out of free names',
                             Connection.CONNECTION_COUNTER)
        self.consumer, future = cad_thread.amqp.consume(Queue(self.name))
        self.terminated = False
        Connection.CONNECTION_COUNTER += 1
        cad_thread.connections[self.name] = self

    def cancel(self):
        self.consumer.cancel()
        self.cad_thread.free_names.append(self.name)
        self.terminated = True

    def process(self):
        if not self.terminated:
            run_if_probability(MESSAGES_PER_SECOND_PER_CONNECTION, self._send)
            run_if_probability(DISCONNECTS_PER_SECOND_PER_CONNECTION, self.cancel)

    def _send(self):
        self.cad_thread.amqp.publish(Message(uuid.uuid4().hex.encode('utf8')),
                                     routing_key=self.name + '-repl')

    def on_message(self, msg: ReceivedMessage):
        run_if_probability(ANSWER_PROBABILITY, self._send)


class ConnectAndDisconnectThread(TerminableThread):
    def __init__(self, amqp):
        self.amqp = amqp
        super().__init__()
        self.free_names = deque(queue_names)
        self.connections = {}  # type: tp.Dict[str, Connection]

    def loop(self) -> None:
        started_at = time.monotonic()
        run_multiple_if_probability(CONNECTIONS_PER_SECOND, lambda: Connection(self))

        for connection in self.connections.values():
            connection.process()

        self.connections = {name: connection for name, connection in self.connections.items() if
                            not connection.terminated}

        evt = None
        while not isinstance(evt, NothingMuch):
            evt = self.amqp.drain(max(0.0, 1 - (time.monotonic() - started_at)))

            if isinstance(evt, ReceivedMessage):
                routing_key = evt.routing_key.tobytes().decode('utf8')
                if routing_key in self.connections:
                    self.connections[routing_key].on_message(evt)
                if evt.ack is not None:
                    evt.ack()

        time.sleep(max(0.0, 1 - (time.monotonic() - started_at)))


def run(client_notify, result_client, server_notify, server_result):
    logging.basicConfig(level=logging.WARNING)

    lftf = LogFramesToFile('client.txt')
    amqp = connect(on_fail=result_client, log_frames=lftf)
    cad = ConnectAndDisconnectThread(amqp)

    cad.start()
    started_at = time.monotonic()
    terminating = False
    while not terminating and (time.monotonic() < started_at + RUNNING_INTERVAL):  # run for however long is required
        try:
            client_notify.get(timeout=1.0)
            terminating = True
        except Empty:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    server_notify.put(None)

    lftf.close()
    # logger.warning('Got %s connections', len(cad.connections))
