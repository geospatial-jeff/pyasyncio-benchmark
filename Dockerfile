FROM python:3.11-alpine

# Bash for convenience :)
RUN apk update && apk add bash gdal-dev alpine-sdk
RUN pip install poetry

WORKDIR app

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
COPY README.md README.md
RUN poetry install --no-root
COPY benchmark benchmark

# Add labels to track container-level metrics
ARG LIBRARY_NAME
ARG TEST_NAME
ARG POOL_SIZE
ARG KEEP_ALIVE
ARG KEEP_ALIVE_TIMEOUT
ARG USE_DNS_CACHE
ARG RUN_ID

LABEL TAG=${LIBRARY_NAME}_${TEST_NAME}
LABEL RUN_ID=${RUN_ID}

ENV LIBRARY_NAME=${LIBRARY_NAME}
ENV TEST_NAME=${TEST_NAME}
ENV RUN_ID="${RUN_ID}"
ENV POOL_SIZE=${POOL_SIZE}
ENV KEEP_ALIVE=${KEEP_ALIVE}
ENV KEEP_ALIVE_TIMEOUT=${KEEP_ALIVE_TIMEOUT}
ENV USE_DNS_CACHE=${USE_DNS_CACHE}


CMD poetry run benchmark docker-entrypoint $LIBRARY_NAME $TEST_NAME $RUN_ID --pool-size $POOL_SIZE --keep-alive $KEEP_ALIVE --keep-alive-timeout $KEEP_ALIVE_TIMEOUT --use-dns-cache $USE_DNS_CACHE