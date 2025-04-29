import enum
import yaml

from pydantic import BaseModel, model_validator, PrivateAttr

from benchmark.clients import HttpClientConfig


class LibraryName(str, enum.Enum):
    aioboto3 = "aioboto3"
    aiohttp = "aiohttp"
    asynctiff = "asynctiff"
    fsspec_async = "fsspec_async"
    httpx = "httpx"
    obstore = "obstore"
    rasterio = "rasterio"
    requests = "requests"


class TestName(str, enum.Enum):
    cog_header = "cog_header"
    fetch_range = "fetch_range"


class TestParams(BaseModel):
    _test_name: TestName = PrivateAttr()


class TestCase(BaseModel):
    library_name: LibraryName
    test_name: TestName
    timeout: int = -1
    n_requests: int
    replicas: int
    client_config: HttpClientConfig = HttpClientConfig()
    params: dict = {}
    debug: bool = False


class ValueOrExpression(BaseModel):
    value: int | None = None
    expression: str | None = None

    @model_validator(mode="after")
    def validate_mutually_exclusive(self):
        if not self.value and not self.expression:
            raise ValueError("Must provide either 'value' or 'expression'")
        if self.value and self.expression:
            raise ValueError("'value' and 'expression' are mutually exclusive")
        return self


"""Test specific configuration"""


class FetchRangeConfig(TestParams):
    _test_name = TestName.fetch_range
    request_size: ValueOrExpression


"""Top level config file"""


class TestConfig(BaseModel):
    tests: list[TestCase]

    @classmethod
    def from_yaml(cls, filename: str):
        with open(filename) as f:
            data = yaml.safe_load(f)

            # Validate config file.
            config = cls(**data)

            # Validate parameters for each test.
            test_params = {t._test_name.default: t for t in TestParams.__subclasses__()}
            for test in config.tests:
                try:
                    validator = test_params[test.test_name]
                except KeyError:
                    raise ValueError(
                        f"Test {test.library_name.value}.{test.test_name.value} does not support parameterization"
                    )
                validator(**test.params)

            return config
