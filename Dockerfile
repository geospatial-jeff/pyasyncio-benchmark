FROM python:3.11-alpine

# Bash for convenience :)
RUN apk update && apk add bash

WORKDIR app

COPY benchmark benchmark
