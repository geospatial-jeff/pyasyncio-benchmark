library_name=$1
test_name=$2

docker build . -t pyasyncio-benchmark:latest --build-arg LIBRARY_NAME=$library_name --build-arg TEST_NAME=$test_name
docker compose up