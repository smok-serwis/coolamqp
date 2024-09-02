Previous release notes are hosted on [GitHub](https://github.com/smok-serwis/coolamqp/releases).
Since v1.3.2 they'll be put here and in release description.

# v1.4.0

* removed the requirement for a Queue that for it to be equal to other Queue if their types do match
* compile_definitions will now depend on requests
* added support for infinite (None) timeouts during start
* stress tests will run for 120 seconds now
* stress tests will be harder, and use more queues
* added arguments to queues, queue binds and exchanges
