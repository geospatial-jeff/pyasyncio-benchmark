# pyasyncio-benchmark
Benchmark I/O libraries for geospatial use cases.  Currently testing:
- `aioboto3`
- `aiohttp`
- `fsspec` (`s3fs`)
- `httpx`
- `obstore`
- `requests`

## Setup
Deploy the sqlite database:
```shell
db_url=sqlite:///sqlite.db alembic upgrade head
```

Run the monitoring stack:
```shell
docker compose -f docker-compose.monitoring.yml up
```

The stack includes a prometheus metrics server which leverages cAdvisor to monitor container
metrics like CPU/memory utilization and network throughput.
- cAdvisor is available at `localhost:8080`
- Prometheus is available at `localhost:9090`


## Run Tests
Tests are run through a CLI available through the poetry environment.  First
run `poetry install`, then call the CLI.

```shell
➜  benchmark --help
Usage: benchmark [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  get-results        Save test results to CSV file.
  run-all            Run all available tests.
  run-test           Run a single test.
```

Tests are run within container(s) managed by a docker-compose stack.  You may change the number
of replicas used for each test by updating `services.benchmark-runner.deploy.replicas` in
`docker-compose.yaml` (default is 1). Using a higher number of replicas allows running tests
at high throughputs by scaling horizontally, assuming the underlying hardware can support it.

Each test is commited to the repo at `benchmark/tests/{library_name}/{test_name}.py`.  Tests
are fully self-contained and may run on their own outside of this benchmarking tool.  Please feel
free to implement your own tests, PRs are welcome!

## Test Results

The `benchmark get-results` command fetches results from each test by querying the Prometheus
metrics server, using information stored by each test in the SQLite database.

The command creates a CSV file containing summary statistics across throughput/cpu and derived metrics like requests per second.
At some point I will type up some better documentation on the outputs, hopefully the column names are straight forward enough.
Note there is one row for each `{library_name} x {test_name} x {replica_count}`.  The library does not (yet) attempt to aggregate metrics across multiple containers.

This command need only be run once after all desired tests have completed.  An end-to-end workflow
looks like:

```shell
# Install the library
poetry install

# Run all tests.  Blocks until all tests complete.
benchmark run-all

# Save test results to CSV.
benchmark get-results test_results.csv
```

This command returns ALL test results in the database.  You may start a fresh by recreating the
SQLite database.
```shell
rm sqlite.db
db_url=sqlite:///sqlite.db alembic upgrade head
```


## Live Monitoring

Prometheus (`localhost:9090`) provides a live view into container metrics as tests run.  It is often helpful to have
the prometheus dashboard up in a separate window as tests run.  Prometheus uses a functional query language called PromQL, 
below are a few useful prometheus queries to look at while running tests, simply:
1. Go to `localhost:9090`.
2. Switch to `Graph` view (defaults to `Table`).
3. Type a query into the command box, or copy and paste one from below.
4. Run the query by clicking `Execute`.
5. Adjust time slider as needed.


CPU Utilization:
```
rate(container_cpu_user_seconds_total{}[15s])
```

Network throughput:
```
rate(container_network_receive_bytes_total{}[15s])
```

A full list of prometheus metrics available through cAdvisor are available [here](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md).
