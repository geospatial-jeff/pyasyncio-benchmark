# pyasyncio-benchmark
Benchmark python coroutines in various ways


# Usage

Run the monitoring stack:
```shell
docker compose -f docker-compose.monitoring.yml up
```

Go to `localhost:8080` for the cAdvisor dashboard to view CPU, memory, and network metrics.


Run a test.  This runs `main.py` across 10 containers (processes).  Make sure to rebuild the container
after modifying `main.py`.
```shell
docker build . -t pyasyncio-benchmark:latest
docker compose up -d
```
