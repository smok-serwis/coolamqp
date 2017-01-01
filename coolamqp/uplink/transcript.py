# coding=UTF-8
from __future__ import absolute_import, division, print_function

from coolamqp.framing.frames import AMQPMethodFrame


class SessionTranscript(object):
    """
    For debugging you may wish to enable logging of the AMQP session
    """

    def on_close_client(self, reason=None):
        """Uplink is being terminated client-side"""
        print('Closed client side, reason is ', reason)

    def on_fail(self):
        """Uplink closed server-side"""
        print('Uplink terminated.')

    def on_frame(self, frame):
        """Received a frame"""
        if isinstance(frame, AMQPMethodFrame):
            print('RECEIVED', frame.payload.NAME)
        else:
            print('RECEIVED ', frame)

    def on_send(self, frame, reason=None):
        """Frames are being relayed"""
        if isinstance(frame, AMQPMethodFrame):
            print ('SENT', frame.payload.NAME, 'because', reason)
        else:
            print ('SENT', frame, 'because', reason)