Welcome to CoolAMQP's documentation!
====================================

.. toctree::
    :maxdepth: 2
    :caption: Contents

    whatsnew
    cluster
    tutorials/send_and_receive
    how-to-guide
    caveats
    frames
    basics
    tracing
    advanced

Quick FAQ
=========

Q: **I'm running uWSGI and I can't publish messages. What's wrong?**

A: Since CoolAMQP spins a thread in the background, make sure to run_
    uwsgi with :code:`--enable-threads`

.. _run: https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html#a-note-on-python-threads

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
