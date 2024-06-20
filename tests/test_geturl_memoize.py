import time

import pytest
from geturl import get_with_retry

try:
    import joblib
except ImportError:
    pytest.skip("joblib is not installed", allow_module_level=True)

try:
    import pytest_httpserver
    from werkzeug import Request, Response
except ImportError:
    pytest.skip("pytest-httpserver is not installed", allow_module_level=True)

@pytest.fixture
def memory() -> joblib.Memory:
    return joblib.Memory("_test_memory", verbose=0)

class Timer:
    dt: float = 0.0

    def __enter__(self) -> "Timer":
        self.tic = time.time()
        return self

    def __exit__(self, *args) -> None:
        self.toc = time.time()
        self.dt = self.toc - self.tic


def test_memoize_google(memory: joblib.Memory) -> None:
    with Timer() as t1:
        code, result = get_with_retry("https://www.google.com", memory=memory)

    assert code == 200

    with Timer() as t2:
        code, result = get_with_retry("https://www.google.com", memory=memory)

    assert code == 200
    assert t2.dt < t1.dt


def test_memoize_httpserver(memory: joblib.Memory, httpserver: pytest_httpserver.HTTPServer) -> None:

    def handler(request: Request) -> Response:
        time.sleep(1)
        return Response("Hello, world!", status=200)

    httpserver.expect_request("/").respond_with_handler(handler)

    with Timer() as t1:
        code, result = get_with_retry(httpserver.url_for("/"), memory=memory)

    assert t1.dt > 1
    assert code == 200

    with Timer() as t2:
        code, result = get_with_retry(httpserver.url_for("/"), memory=memory)

    assert t2.dt < 0.1
    assert code == 200
    assert t2.dt < t1.dt
