FROM python:3.11-alpine

# Bash for convenience :)
RUN apk update && apk add bash
RUN pip install aiohttp

WORKDIR app

COPY benchmark benchmark

COPY main.py main.py

ENTRYPOINT python main.py