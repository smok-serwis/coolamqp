The changelog is kept as [release notes](https://git.dms-serwis.com.pl/smokserwis/coolamqp/-/releases)
on GitHub. This file serves to only note what changes
have been made so far, between releases.

# v1.3.2

* removed the requirement for a Queue that for it to be equal to other Queue if their types do match
* compile_definitions will now depend on requests
* added support for infinite (None) timeouts during start
* stress tests will run for 60 seconds now
