import pytest

from clientele import api, http, retries


def test_retries_retry_default_behaviour():
    fake_backend = http.FakeHTTPBackend()
    client = api.APIClient(
        config=api.BaseConfig(
            base_url="http://fake.api",
            http_backend=fake_backend,
        )
    )

    # Configure fake responses: first a 500 error, then a 200 success
    fake_backend.queue_response(status=500, content={"error": "Server error"})
    fake_backend.queue_response(status=200, content={"data": "Success"})

    @retries.retry(attempts=3)
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        return result

    response = get_test_endpoint()

    assert response == {"data": "Success"}
    assert len(fake_backend.requests) == 2  # Ensure it retried once


def test_retries_retry_with_explicit_statuses():
    fake_backend = http.FakeHTTPBackend()
    client = api.APIClient(
        config=api.BaseConfig(
            base_url="http://fake.api",
            http_backend=fake_backend,
        )
    )

    # Configure fake responses: first a 500 error, then a 400 error, then a 200 success
    fake_backend.queue_response(status=500, content={"error": "Server error"})
    fake_backend.queue_response(status=400, content={"error": "Bad request"})
    fake_backend.queue_response(status=200, content={"data": "Success"})

    @retries.retry(attempts=3, on_status=[500, 400])
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        return result

    response = get_test_endpoint()

    assert response == {"data": "Success"}
    assert len(fake_backend.requests) == 3  # Ensure it retried twice


def test_retries_do_not_block_other_statuses_from_raising_properly():
    fake_backend = http.FakeHTTPBackend()
    client = api.APIClient(
        config=api.BaseConfig(
            base_url="http://fake.api",
            http_backend=fake_backend,
        )
    )

    # Configure fake responses: first a 500 error, then a 400 error which should raise
    fake_backend.queue_response(status=500, content={"error": "Server error"})
    fake_backend.queue_response(status=400, content={"error": "Bad request"})

    @retries.retry(attempts=3, on_status=[500])
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        return result

    with pytest.raises(api.exceptions.APIException):
        get_test_endpoint()

    assert len(fake_backend.requests) == 2  # Ensure it retried once


def test_retries_do_not_block_other_exceptions():
    fake_backend = http.FakeHTTPBackend()
    client = api.APIClient(
        config=api.BaseConfig(
            base_url="http://fake.api",
            http_backend=fake_backend,
        )
    )
    fake_backend.queue_response(status=200, content={"error": "Server error"})

    @retries.retry(attempts=3)
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        raise TypeError("Some other exception")

    with pytest.raises(TypeError):
        get_test_endpoint()

    assert len(fake_backend.requests) == 1  # Ensure it did not retry
