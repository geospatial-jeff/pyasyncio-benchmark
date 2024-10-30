# pyasyncio-benchmark
Benchmark python coroutines in various ways


# Usage

Run the monitoring stack:
```shell
docker compose -f docker-compose.monitoring.yml up
```

Go to `localhost:8080` for the cAdvisor dashboard to view CPU, memory, and network metrics.


Run a test.  `TEST_NAME` may be set to any file in `benchmark/tests/`.
```shell
docker build . -t pyasyncio-benchmark:latest
TEST_NAME=obstore_cog_header docker compose up -d
```
