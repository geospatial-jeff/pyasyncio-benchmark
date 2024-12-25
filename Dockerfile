FROM python:3.11-alpine

# Bash for convenience :)
RUN apk update && apk add bash
RUN pip install poetry

WORKDIR app

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
RUN poetry install
COPY benchmark benchmark
COPY main.py main.py

# Add labels to track container-level metrics
ARG LIBRARY_NAME
ARG TEST_NAME

LABEL LIBRARY_NAME=${LIBRARY_NAME}
LABEL TEST_NAME=${TEST_NAME}

ENV LIBRARY_NAME=${LIBRARY_NAME}
ENV TEST_NAME=${TEST_NAME}

ENTRYPOINT ["poetry", "run"]
CMD python main.py $LIBRARY_NAME $TEST_NAME