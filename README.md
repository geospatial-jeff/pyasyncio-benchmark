# pyasyncio-benchmark
Benchmark python coroutines in various ways


# Usage
Deploy the sqlite database:
```shell
db_url=sqlite:///sqlite.db alembic upgrade head
```

Run the monitoring stack:
```shell
docker compose -f docker-compose.monitoring.yml up
```

Go to `localhost:8080` for the cAdvisor dashboard to view CPU, memory, and network metrics.


Run a test.  `TEST_NAME` may be set to any file in `benchmark/tests/`.
```shell
docker build . -t pyasyncio-benchmark:latest
LIBRARY_NAME=obstore TEST_NAME=cog_header docker compose up -d
```

## PromQL

CPU utilization:
```
 sum by (image) (rate(container_network_receive_bytes_total{image="pyasyncio-benchmark:latest"}[15s]))
```

Network I/O
```
 sum by (image) (rate(container_cpu_user_seconds_total{image="pyasyncio-benchmark:latest"}[15s]))
```