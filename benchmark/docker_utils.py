from docker.client import DockerClient
import requests_unixsocket
import time

from benchmark.settings import get_settings


def get_container_id() -> str:
    """Fetches the ID of a docker container, from inside the container.  Only works if called
    from within a running container with a volume mount to `/var/run/docker.sock`, for example:

        `-v /var/run/docker.sock:/var/run/docker.sock`

    The container ID is also exposed by prometheus/cadvisor under the `id` tag
    (id=`docker/<container_id>`).  This is used to correlate each test with the metrics
    captured by prometheus.
    """
    r = requests_unixsocket.get(
        f"http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/{get_settings().HOSTNAME}/json"
    )
    r.raise_for_status()
    resp_json = r.json()
    return resp_json["Id"]


def block_until_container_exits(
    docker_client: DockerClient, backoff_seconds: int = 10
) -> str:
    """Block until all `pyasyncio-benchmark` containers exit."""
    is_running = True
    while is_running:
        time.sleep(backoff_seconds)
        running_containers = docker_client.containers.list()
        is_running = any(
            [
                "pyasyncio-benchmark" in container.name
                for container in running_containers
            ]
        )
