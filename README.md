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


Run a test:
```shell
./scripts/run_test.sh obstore cog_header
```

## PromQL

CPU utilization:
```
 sum by (container_label_TAG) (rate(container_network_receive_bytes_total{image="pyasyncio-benchmark:latest"}[15s]))
```

Network I/O
```
 sum by (container_label_TAG) (rate(container_cpu_user_seconds_total{image="pyasyncio-benchmark:latest"}[15s]))
```