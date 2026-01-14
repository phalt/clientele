# 🌊 Streaming

Clientele supports streaming responses using Server-Sent Events through the `streaming_response=True` parameter.

## Basic stream Example

```python
from typing import AsyncIterator
from pydantic import BaseModel
from clientele import api

client = api.APIClient(base_url="http://localhost:8000")

class Event(BaseModel):
    text: str

@client.get("/events", streaming_response=True)
async def stream_events(*, result: AsyncIterator[Event]) -> AsyncIterator[Event]:
    return result
```

```python
async for event in await stream_events():
    print(event.text)
```

## Type-Based Hydration

The type inside `AsyncIterator[T]` determines how responses are parsed:

**String (no parsing)**:

```python
@client.get("/events", streaming_response=True)
async def stream_text(*, result: AsyncIterator[str]) -> AsyncIterator[str]:
    return result
```

```python
async for line in await stream_text():
    print(line)  # Raw string
```

**Dictionary (JSON parsing)**:

```python
@client.get("/events", streaming_response=True)
async def stream_json(*, result: AsyncIterator[dict]) -> AsyncIterator[dict]:
    return result
```

```python
async for data in await stream_json():
    print(data["field"])  # Parsed JSON as dict
```

**Pydantic Model (JSON + validation)**:

```python
class Token(BaseModel):
    text: str
    id: int

@client.get("/stream", streaming_response=True)
async def stream_tokens(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
    return result
```

```python
async for token in await stream_tokens():
    print(token.text, token.id)  # Validated Pydantic model
```

## Support methods

Clientele streams support:

- `HTTP GET`
- `HTTP POST`
- `HTTP PUT`
- `HTTP PATCH`
- `HTTP DELETE`

## Synchronous SSE

You can also use synchronous iterators for blocking SSE streams:

```python
from typing import Iterator

@client.get("/events", streaming_response=True)
def stream_events_sync(*, result: Iterator[Event]) -> Iterator[Event]:
    return result
```

```python
for event in stream_events_sync():
    print(event.text)
```
