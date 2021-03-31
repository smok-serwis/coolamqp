Frame tracing
=============

CoolAMQP allows you to trace every sent or received frame. Just provide an instance of

.. autoclass:: coolamqp.tracing.BaseFrameTracer
    :members:


LoggingFrameTracer
~~~~~~~~~~~~~~~~~~

To show each frame that is sent or received to the server use the following:

.. code-block:: python

    import logging

    logger = logging.getLogger(__name__)

    from coolamqp.tracing import LoggingFrameTracer

    frame_tracer = LoggingFrameTracer(logger, logging.WARNING)

    cluster = Cluster([NODE], log_frames=frame_logger)
    cluster.start()


Documentation of the class:

.. autoclass:: coolamqp.tracing.LoggingFrameTracer
    :members:

HoldingFrameTracer
~~~~~~~~~~~~~~~~~~

.. autoclass:: coolamqp.tracing.HoldingFrameTracer
    :members:
