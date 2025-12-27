# Testing

Clientele is designed for easy testing. 

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

We recommend installing [respx](https://lundberg.github.io/respx/) for writing your tests.
