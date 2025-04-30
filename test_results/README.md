# Test Results

CSV files contain summary statistics (mean, stdev, percentiles etc.) of various metrics across the course of each test:
- `recv_bytes_per_second_*` - total bytes received by the container, per second.
- `cpu_seconds_*` - total CPU seconds consumed by the container.  This is currently NOT expressed relative to the node (ex. percent CPU utilization).  CPU seconds on their own is a bit hard to interpret, need to make this better.
- `recv_bytes_per_second_per_cpu_*` - the first divided by the second.
- `memory_usage_bytes_*` - total bytes of memory used by the container.
- `duration_seconds` - the total runtime of the test.
- `instance_type` - the AWS instance type used in this test, if applicable.
- `cost_usd` - the AWS compute cost for the instance across the duration of the test, assumes fractional pricing.