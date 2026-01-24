import pytest

from clientele import api, retries, testing

client = api.APIClient(config=api.BaseConfig(base_url="http://fake.api"))


def test_retries_retry_default_behaviour():
    fake_backend = testing.configure_client_for_testing(client)

    # Configure fake responses: first a 500 error, then a 200 success
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.internal_server_error(
            data=b'{"error": "Server error"}',
            headers={"content-type": "application/json"},
        ),
    )
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.ok(
            data=b'{"data": "Success"}',
            headers={"content-type": "application/json"},
        ),
    )

    @retries.retry(attempts=3)
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        return result

    response = get_test_endpoint()

    assert response == {"data": "Success"}
    assert len(fake_backend.requests) == 2  # Ensure it retried once


def test_retries_retry_with_explicit_statuses():
    fake_backend = testing.configure_client_for_testing(client)

    # Configure fake responses: first a 500 error, then a 400 error, then a 200 success
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.internal_server_error(
            data=b'{"error": "Server error"}',
            headers={"content-type": "application/json"},
        ),
    )
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.bad_request(
            data=b'{"error": "Bad request"}',
            headers={"content-type": "application/json"},
        ),
    )
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.ok(
            data=b'{"data": "Success"}',
            headers={"content-type": "application/json"},
        ),
    )

    @retries.retry(attempts=3, on_status=[500, 400])
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        return result

    response = get_test_endpoint()

    assert response == {"data": "Success"}
    assert len(fake_backend.requests) == 3  # Ensure it retried twice


def test_retries_do_not_block_other_statuses_from_raising_properly():
    fake_backend = testing.configure_client_for_testing(client)

    # Configure fake responses: first a 500 error, then a 400 error which should raise
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.internal_server_error(
            data=b'{"error": "Server error"}',
            headers={"content-type": "application/json"},
        ),
    )
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.bad_request(
            data=b'{"error": "Bad request"}',
            headers={"content-type": "application/json"},
        ),
    )

    @retries.retry(attempts=3, on_status=[500])
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        return result

    with pytest.raises(api.exceptions.APIException):
        get_test_endpoint()

    assert len(fake_backend.requests) == 2  # Ensure it retried once


def test_retries_do_not_block_other_exceptions():
    fake_backend = testing.configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/test-endpoint",
        response_obj=testing.ResponseFactory.ok(
            data=b'{"error": "Server error"}',
            headers={"content-type": "application/json"},
        ),
    )

    @retries.retry(attempts=3)
    @client.get("/test-endpoint")
    def get_test_endpoint(result: dict) -> dict:
        raise TypeError("Some other exception")

    with pytest.raises(TypeError):
        get_test_endpoint()

    assert len(fake_backend.requests) == 1  # Ensure it did not retry
