# 🚨 Exception Handling

Clientele will handle unexpected API responses by raising an `APIException`.

## When APIException is Raised

The `APIException` is raised when the API returns a response code that doesn't match any of the expected response codes defined in the OpenAPI schema for that endpoint.

Each API function has a mapping of expected response codes to response types. If the actual response code isn't in this mapping, Clientele raises an `APIException` instead of trying to parse the response.

## Catching APIException

Import `APIException` from your client's `http` module:

```python
from my_client import client, http

try:
    user = client.get_user(user_id=999)
except http.APIException as e:
    # Handle unexpected response
    print(f"Unexpected status: {e.response.status_code}")
    print(f"Response body: {e.response.text}")
```

## Exception Attributes

The `APIException` provides access to:

- `response`: The raw `httpx.Response` object for debugging
- `reason`: A string explaining why the exception was raised

```python
try:
    user = client.get_user(user_id=999)
except http.APIException as e:
    print(f"Reason: {e.reason}")
    print(f"Status: {e.response.status_code}")
    print(f"Headers: {e.response.headers}")
    print(f"Body: {e.response.text}")
```

## Common Scenarios

### Server Error (500)

If the API returns a 500 error and it's not defined in the schema:

```python
try:
    result = client.create_user(data=user_data)
except http.APIException as e:
    if e.response.status_code >= 500:
        # Server error - retry logic
        logger.error(f"Server error: {e.response.status_code}")
```

### Unexpected Client Error

If the API returns an error code you didn't expect:

```python
try:
    result = client.delete_user(user_id=123)
except http.APIException as e:
    if e.response.status_code == 403:
        # Not defined in schema, but API returned it
        logger.warning("Permission denied")
    elif e.response.status_code == 404:
        logger.info("User not found")
```

## Best Practices

1. **Always catch APIException** when calling API functions that might return unexpected responses
2. **Log the full response** for debugging - it contains valuable information
3. **Check the OpenAPI schema** if you consistently get `APIException` for a specific endpoint - the schema might be incomplete
4. **Use pattern matching** (Python 3.10+) for clean error handling:

```python
try:
    result = client.get_user(user_id=999)
except http.APIException as e:
    match e.response.status_code:
        case 404:
            print("User not found")
        case 500:
            print("Server error")
        case _:
            print(f"Unexpected error: {e.response.status_code}")
```
