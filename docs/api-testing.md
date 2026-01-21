# 🧪 Testing

Clientele is designed for easy testing with our built-in fake backends or with existing third party tools.

## FakeHTTPBackend

The `FakeHTTPBackend` allows you to test your API client without making real HTTP requests.

Instead of making real network calls, the fake backend captures all requests and returns configurable responses. You can swap out the HTTP backend on an existing client by replacing `client.config.http_backend`.

### Basic Example

Assuming you have a pre-written client:

```python
from my_api_client import client
from clientele.http import FakeHTTPBackend
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

# Create a fake backend with default response
fake_backend = FakeHTTPBackend(
    default_content={"id": 1, "name": "Alice"},
    default_status=200,
)

# Replace the client's HTTP backend
client.config.http_backend = fake_backend

# Call your API method
user = client.get_user(user_id=123)

# Verify the response
assert user.id == 1
assert user.name == "Alice"

# Verify what was requested
assert len(fake_backend.requests) == 1
assert fake_backend.requests[0]["method"] == "GET"
assert "/users/123" in fake_backend.requests[0]["url"]
```

### Queuing Different Responses

You can queue different responses for multiple requests:

```python
from my_api_client import client
from clientele.http import FakeHTTPBackend

# Replace the HTTP backend
fake_backend = FakeHTTPBackend()
client.config.http_backend = fake_backend

# Queue responses in order
fake_backend.queue_response(
    status=201,
    content={"id": 10, "name": "Bob"},
)
fake_backend.queue_response(
    status=200,
    content={"id": 10, "name": "Bob"},
)

# First request gets the 201 response
created = client.create_user(data={"name": "Bob", "email": "bob@example.com"})
assert created.id == 10

# Second request gets the 200 response
fetched = client.get_user(user_id=10)
assert fetched.name == "Bob"
```

### Error Responses

You can also simulate error responses:

```python
from my_api_client import client
from clientele.http import FakeHTTPBackend

# Replace the HTTP backend
fake_backend = FakeHTTPBackend()
client.config.http_backend = fake_backend

# Queue a 404 error response
fake_backend.queue_response(
    status=404,
    content={"error": "User not found", "code": 404},
)

error = client.get_user(user_id=999)
assert error.error == "User not found"
```

## RESPX

You can use [respx](https://lundberg.github.io/respx/) for easy testing if you have the default [httpx backend](api-http-backends.md) installed.

Our [own test suite](https://github.com/phalt/clientele/blob/0.4.4/tests/test_generated_client.py) shows how you can write mock tests for your API client.

```python
import pytest
from httpx import Response
from respx import MockRouter

from .test_client import client, constants, schemas

BASE_URL = constants.api_base_url()


@pytest.mark.respx(base_url=BASE_URL)
def test_simple_request_simple_request_get(respx_mock: MockRouter):
    # Given
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    respx_mock.get(mock_path).mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    # When
    response = client.simple_request_simple_request_get()
    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path
```
