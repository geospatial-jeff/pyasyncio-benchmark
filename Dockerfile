FROM python:3.11-alpine

# Bash for convenience :)
RUN apk update && apk add bash gdal-dev alpine-sdk
RUN pip install poetry

WORKDIR app

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
COPY benchmark benchmark
COPY README.md README.md
RUN poetry install

# Add labels to track container-level metrics
ARG LIBRARY_NAME
ARG TEST_NAME

LABEL TAG=${LIBRARY_NAME}_${TEST_NAME}

ENV LIBRARY_NAME=${LIBRARY_NAME}
ENV TEST_NAME=${TEST_NAME}

CMD poetry run benchmark docker-entrypoint $LIBRARY_NAME $TEST_NAME