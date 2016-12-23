Tests work using either Travis CI or Vagrant.

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
