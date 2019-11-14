* v0.95rc1:

 * added a select-based listener in order to integrate with gevent

* v0.94:

 * _no such version_

* v0.93:

 * Large refactor of XML schema compiler
 
* v0.92:

 * Added `on_fail` event handler - fired upon connection loss

* v0.91:
  * removed annoying warnings

* v0.90:
  * first release with a *stable API*
  * You can pick how your received _message.body_ will look like - bytes,
  a zero-copy-for-short-messages memoryview, or maybe a totally zero-copy list of memoryviews?

* v0.89.1:
  * **Critical bugfix**: messages larger than a frame got corrupted

* v0.89:
   * Events are no longer timestamped by CoolAMQP, it's your job now
   * You can delete queues (_Cluster.delete_queue_)
   * Race condition _Connection.start_ fixed
   * Queue can accept _bytes_ as name
   * Consumer will set _cancelled_ to _True_ if
   [Consumer Cancel Notification](https://www.rabbitmq.com/consumer-cancel.html) is received
   * You can register callbacks for:
       * Consumer being cancelled for any reason
       * Consumer being cancelled with a CCN

* v0.88:
    * Cluster.start will RuntimeError if called more than once
    * Cluster.shutdown will RuntimeError if called without .start
    * Warning with content list is shorter


Latest:
* stability bug fixes
* ...
