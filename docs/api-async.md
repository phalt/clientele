# 🔀 Async support

Clientele API supports both async and sync functions.

They can even be mixed in together if you prefer.

## Async and sync example

```python
from clientele import api as clientele_api
from .my_config import Config
from .my_models import BookResponse, CreateBookResponse, CreateBookRequest

client = clientele_api.APIClient(config=Config())

@client.post("/books")
def create_user(
    data: CreateBookResponse,
    result: CreateBookResponse,
) -> CreateBookResponse:
    return result


# Mix sync and async functions in the same client
@client.get("/book/{book_id}")
async def get_book(book_id: int, result: BookResponse) -> BookResponse:
    return result
```

## Async and sync usage

```python
from my_clientele_client import client, schemas

# handle sync requests
response = client.create_book(
    data=schemas.CreateBookRequest(title="My awesome book")
)

match response:
    case schemas.CreateBookResponse():
        # handle valid response
    case schemas.ValidationError():
        # handle errors

# Handle async requests
book_response = await client.get_book(book_id=123)
```
