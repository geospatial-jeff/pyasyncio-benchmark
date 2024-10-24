# pyasyncio-benchmark
Benchmark python coroutines in various ways


# Usage

Run via docker:

```shell
docker build . -t pyasyncio-benchmark:latest
docker run --rm -v main.py:/var/task/ -it benchmark:latest python /var/task/main.py
```
