# Contributing guide

1. Keep it unit tested.
    1.1. If it's cool af, you don't have to.
2. Exhaustive pydoc.
3. If you introduce any gotchas, document them in [docs/](docs/).
4. We aim to support Python 2.7 as long as possible, keep that in account.

## Unit tests
Tests work using docker-compose.

Just
```bash
docker-compose up --build unittest
docker-compose up --build stress_tests
```

If you want to debug things, you have RabbitMQ management enabled on Vagrant. 
Go to [http://127.0.0.1:15672](http://127.0.0.1:15672) and log in with **user** / **user**

RabbitMQ management is NOT enabled on Travis CI.

If you want to see a coverage report, run tests like this:
```bash
nosetests --with-coverage --exe
coverage html
```
*--exe* is for the cases where you run on Windows, and everything in */vagrant* is 777.

and then go to [http://127.0.0.1:8765](http://127.0.0.1:8765)
