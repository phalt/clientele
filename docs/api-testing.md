# 🧪 Testing

Clientele is designed for easy testing with our built-in fake backend.

## FakeHTTPBackend

The `FakeHTTPBackend` allows you to test your API client without making real HTTP requests.

Instead of making real network calls, the fake backend captures all requests and returns configurable responses.

### Basic Example

Assuming you have a pre-written client:

```python
from my_api_client import client, get_user
from clientele.http import FakeHTTPBackend, Response
from clientele.testing import configure_client_for_testing


def test_my_api():
    # Configure a fake backend with default response
    fake_backend: FakeHTTPBackend = configure_client_for_testing(client)

    # Configure the HTTP response itself
    fake_backend.queue_response(
        path="/users/1",
        response_obj=Response(
            status_code=200,
            content=b'{"id": 1, "name": "Bob"}',
            headers={"content-type": "application/json"},
        ),
    )

    # Call your API method
    user = get_user(user_id=123)

    # Verify the response
    assert user.id == 1
    assert user.name == "Bob"

    # Verify what was requested
    assert len(fake_backend.requests) == 1
    assert fake_backend.requests[0]["method"] == "GET"
    assert "/users/1" in fake_backend.requests[0]["url"]
```

### Queuing Different Responses

You can queue different responses for specific request paths:

```python
from my_api_client import client, create_user, get_user
from clientele.http import FakeHTTPBackend, Response
from clientele.testing import configure_client_for_testing

# Replace the HTTP backend
fake_backend: FakeHTTPBackend = configure_client_for_testing(client)

# Queue responses for a specific path
fake_backend.queue_response(
    path="/users",
    response_obj=Response(
        status_code=201,
        content=b'{"id": 11, "name": "Bob"}',
        headers={"content-type": "application/json"},
    ),
)
fake_backend.queue_response(
    path="/users/10",
    response_obj=Response(
        status_code=200,
        content=b'{"id": 10, "name": "Bob"}',
        headers={"content-type": "application/json"},
    ),
)

# First request gets the /users response
created = create_user(data={"name": "Bob", "email": "bob@example.com"})
assert created.id == 11

# Second request gets the /users/10 response
fetched = get_user(user_id=10)
assert fetched.name == "Bob"
```

### Error Responses

You can also simulate error responses:

```python
from my_api_client import client, get_user
from clientele.http import FakeHTTPBackend, Response
from clientele.testing import configure_client_for_testing

# Replace the HTTP backend
fake_backend: FakeHTTPBackend = configure_client_for_testing(client)

# Queue a 404 error response
fake_backend.queue_response(
    path="/users/999",
    response_obj=Response(
        status_code=404,
        content=b'{"error": "User not found", "code": 404}',
        headers={"content-type": "application/json"},
    ),
)

error = get_user(user_id=999)
assert error.error == "User not found"
```
