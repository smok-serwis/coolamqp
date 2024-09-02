Previous release notes are hosted on [GitHub](https://github.com/smok-serwis/coolamqp/releases).
Since v1.3.2 they'll be put here and in release description.

# v1.4.0

* removed the requirement for a Queue that for it to be equal to other Queue if their types do match
* compile_definitions will now depend on requests
* added support for infinite (None) timeouts during start
* stress tests will run for 120 seconds now
* stress tests will be harder, and use more queues
* added arguments to queues, queue binds and exchanges
* creating auto_delete non-exclusive queues will be met with a [PendingDeprecationWarning](https://www.rabbitmq.com/blog/2021/08/21/4.0-deprecation-announcements)
* added unit tests for Python 2.7
