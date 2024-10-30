# pyasyncio-benchmark
Benchmark python coroutines in various ways


# Usage

Run the monitoring stack:
```shell
docker compose -f docker-compose.monitoring.yml up
```

Go to `localhost:8080` for the cAdvisor dashboard.


Slam a http server with requests:

```shell
npx http-server
docker build . -t pyasyncio-benchmark:latest
docker-compose up -d
```
