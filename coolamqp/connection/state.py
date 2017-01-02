# coding=UTF-8
from __future__ import absolute_import, division, print_function
import six
from coolamqp.uplink import Handshaker
from coolamqp.connection.orders import LinkSetup
from coolamqp.framing.definitions import ChannelOpenOk, ChannelOpen
from coolamqp.framing.frames import AMQPMethodFrame


class Broker(object):
    """
    A connection to a single broker
    """

    def __init__(self, connection, node_definition):
        """
        :param connection: coolamqp.uplink.Connection, before .start is called
        :param node_definition: node definition that will be used to handshake
        """
        self.connection = connection
        self.node_definition = node_definition

        self.free_channels = [] # list of channels usable for consuming shit

    @staticmethod
    def from_node_def(node_def, listener_thread, debug=True):
        """
        :param node_def: NodeDefinition to use
        :param listener_thread: ListenerThread to use
        :return: a Broker with Connection.
        """
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((node_def.host, node_def.port))
        s.settimeout(0)
        s.send('AMQP\x00\x00\x09\x01')

        from coolamqp.uplink import Connection
        con = Connection(s, listener_thread)

        if debug:
            from coolamqp.uplink.transcript import SessionTranscript
            con.transcript = SessionTranscript()

        return Broker(con, node_def)


    def connect(self):
        """Return an LinkSetup order to get when it connects"""
        ls = LinkSetup()

        def send_channel_opened():
            # OK, opened
            ls.on_done()

        def handshake_complete():
            if handshaker.channel_max < 1:
                self.connection.send(None, 'channel_max < 1 !!!')
                ls.on_fail()
                return

            for free_chan in six.moves.xrange(2, handshaker.channel_max+1):
                self.free_channels.append(free_chan)

            # It's OK, open channel 1 for sending messages
            self.connection.watch_for_method(1, ChannelOpenOk, send_channel_opened)
            self.connection.send([AMQPMethodFrame(1, ChannelOpen())])

        handshaker = Handshaker(
            self.connection,
            self.node_definition.user,
            self.node_definition.password,
            self.node_definition.virtual_host,
            handshake_complete,
            ls.on_failed,
            heartbeat=self.node_definition.heartbeat or 0
        )

        def send_channel_opened(frame):
            # OK, opened
            ls.on_done()

        def handshake_complete():
            if handshaker.channel_max < 1:
                self.connection.send(None, 'channel_max < 1 !!!')
                ls.on_fail()
                return

            for free_chan in six.moves.xrange(2, handshaker.channel_max+1):
                self.free_channels.append(free_chan)

            # It's OK, open channel 1 for sending messages
            self.connection.watch_for_method(1, ChannelOpenOk, send_channel_opened)
            self.connection.send([AMQPMethodFrame(1, ChannelOpen())])

        self.connection.start()

        return ls


