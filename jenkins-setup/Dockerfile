FROM python:3.9-slim

RUN mkdir /workspace
COPY nodemonitor /workspace
COPY manager.py /workspace
COPY config.ini /workspace
COPY requirements.txt /workspace

WORKDIR /workspace

RUN pip install -r requirements.txt

# Note that this container needs to be run with the NODEMONITOR_ENCRYPTION_PASSWORD
# environment variable set!
CMD ["/usr/local/bin/python", "monitor.py", "-c", "config.ini"]
