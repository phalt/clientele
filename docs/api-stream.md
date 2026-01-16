# 🌊 Streaming

Clientele supports streaming responses using Server-Sent Events through the `streaming_response=True` parameter.

## Basic stream Example

```python
from typing import AsyncIterator

from clientele import api
from pydantic import BaseModel


client = api.APIClient(base_url="https://httpbin.org")


class Event(BaseModel):
    id: int
    url: str


@client.get("/stream/{n}", streaming_response=True)
async def stream_events(n: int, result: AsyncIterator[Event]) -> AsyncIterator[Event]:
    return result
```

```python
async for event in await stream_events(n=4):
    print(event)
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

## Custom Parsing with response_parser

You can provide a custom `response_parser` callback to control how each streamed item is parsed:

```python
from typing import AsyncIterator

def parse_custom_event(line: str) -> dict:
    """Custom parser for each streamed line."""
    parts = line.split(",")
    return {
        "timestamp": parts[0],
        "message": parts[1],
        "level": parts[2] if len(parts) > 2 else "info"
    }

@client.get("/logs", streaming_response=True, response_parser=parse_custom_event)
async def stream_logs(*, result: AsyncIterator[dict]) -> AsyncIterator[dict]:
    return result
```

```python
async for log_entry in await stream_logs():
    print(f"{log_entry['timestamp']}: {log_entry['message']}")
```

The `response_parser` is called for each line received from the stream, giving you full control over how the data is transformed before being yielded to your code.
