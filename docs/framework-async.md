# Async support

Clientele framework supports both async and sync methods.

They can even be mixed in together if you prefer.

## Async and sync example

```python
from clientele import framework
from .my_config import Config
from .my_models import BookResponse, CreateBookReponse, CreateBookRequest

client = framework.Client(config=Config())

@client.post("/books")
def create_user(
    data: CreateBookReponse,
    result: CreateBookReponse,
) -> CreateBookReponse:
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
