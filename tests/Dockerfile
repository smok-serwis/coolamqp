# For both unit tests and stress tests
# refer to docker-compose.yaml and README.md for details
FROM python:3.7

ADD requirements.txt /tmp/requirements.txt
ADD stress_tests/requirements.txt /tmp/requirements2.txt
RUN pip install -r /tmp/requirements.txt && \
    pip install -r /tmp/requirements2.txt && \
    pip install nose mock coverage

ADD . /coolamqp
WORKDIR /coolamqp

ENV AMQP_HOST=amqp

# for those pesky builds on Windows
RUN chmod -R ugo-x /coolamqp

CMD python setup.py nosetests --tests tests

