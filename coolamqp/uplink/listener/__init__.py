# coding=UTF-8
"""
A listener is a thread that monitors a bunch of sockets for activity.

Think "asyncio" but I couldn't be bothered to learn Twisted.

It provides both for sending and receiving messages. It is written
as a package, because the optimal network call, epoll, is not
available on Windows, and you might just want to use it.

select and poll are not optimal, because if you wanted to send
something in that small gap where select/poll blocks, you won't
immediately be able to do so. With epoll, you can.
"""
from __future__ import absolute_import, division, print_function

from coolamqp.uplink.listener.thread import ListenerThread
