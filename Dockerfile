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

ENTRYPOINT ["poetry", "run"]