# Framework Client Tests - Implementation Notes

This directory contains tests for the framework clients generated using the `generate-framework` command. These tests mirror the coverage of the old client tests but account for the differences in the framework client implementation.

## Test Coverage

The tests in this directory provide 100% equivalent coverage to the old client tests:

- **test_framework_generated_client.py**: 12 tests for sync framework client
- **test_async_framework_generated_client.py**: 12 tests for async framework client

Total: 24 tests matching the 24 tests from the old clients.

## Key Differences from Old Clients

### 1. Exception Handling
- **Old clients**: Use custom `http.APIException` for unexpected status codes
- **Framework clients**: 
  - Routes WITHOUT `response_map`: Raise `httpx.HTTPStatusError` 
  - Routes WITH `response_map`: Return the appropriate typed response
  
This is why `test_simple_request_simple_request_get_raises_exception` catches `httpx.HTTPStatusError` instead of `APIException`.

### 2. Query Parameter Naming
- **Old clients**: Use camelCase parameter names as defined in OpenAPI spec (e.g., `yourInput`)
- **Framework clients**: Use Python snake_case parameter names (e.g., `your_input`)

The framework client automatically converts Python parameter names to the appropriate API format.

### 3. Headers Handling
- **Old clients**: Accept Pydantic model instances for headers
- **Framework clients**: Accept dict for headers parameter

Headers must be converted to dict using `model_dump(by_alias=True, exclude_unset=True)`.

### 4. Optional Query Parameters
- **Old clients**: Filter out `None` values from query parameters
- **Framework clients**: Include `None` values as empty strings in query parameters

This difference doesn't affect functionality but is reflected in the test assertions.

## Test Structure

Each test follows the pattern:
1. **Given**: Mock the HTTP response using respx
2. **When**: Call the client method
3. **Then**: Assert the response is correctly typed and the request was made correctly

## Running Tests

```bash
# Run all framework client tests
pytest tests/generate_framework_client_tests/ -v

# Run only sync tests
pytest tests/generate_framework_client_tests/test_framework_generated_client.py -v

# Run only async tests
pytest tests/generate_framework_client_tests/test_async_framework_generated_client.py -v
```
