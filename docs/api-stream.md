# 🌊 Streaming

Clientele supports HTTP streaming responses through the `streaming_response=True` parameter.

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

## Synchronous Streaming

You can also use synchronous iterators for blocking streams:

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

## Parsing Server-Sent Events (SSE)

For Server-Sent Events format (with `data:`, `event:`, `id:` fields), use a custom `response_parser` to extract the data:

```python
from typing import AsyncIterator
import json

def parse_sse(line: str) -> dict | None:
    """Parse SSE format: extracts data from 'data: {json}' lines."""
    if line.startswith('data: '):
        json_str = line[6:]  # Remove 'data: ' prefix
        return json.loads(json_str)
    # Skip other SSE fields (event:, id:, retry:, comments)
    return None

class ChatMessage(BaseModel):
    role: str
    content: str

@client.post("/chat/stream", streaming_response=True, response_parser=parse_sse)
async def stream_chat(*, data: dict, result: AsyncIterator[ChatMessage]) -> AsyncIterator[ChatMessage]:
    return result
```

```python
# Server sends SSE format:
# data: {"role": "assistant", "content": "Hello"}
#
# data: {"role": "assistant", "content": "How can I help?"}
#

async for message in await stream_chat(data={"prompt": "Hi"}):
    if message:  # Skip None values from non-data lines
        print(f"{message.role}: {message.content}")
```

**Note**: The `response_parser` receives each line as a string and should return the parsed value. Return `None` to skip lines (e.g., SSE comments or event type declarations).

## Custom Parsing with response_parser

You can provide a custom `response_parser` callback to control how each streamed line is parsed:

```python
from typing import AsyncIterator

def parse_csv_log(line: str) -> dict:
    """Custom parser for CSV-formatted log lines."""
    parts = line.split(",")
    return {
        "timestamp": parts[0],
        "message": parts[1],
        "level": parts[2] if len(parts) > 2 else "info"
    }

@client.get("/logs", streaming_response=True, response_parser=parse_csv_log)
async def stream_logs(*, result: AsyncIterator[dict]) -> AsyncIterator[dict]:
    return result
```

```python
async for log_entry in await stream_logs():
    print(f"{log_entry['timestamp']}: {log_entry['message']}")
```

The `response_parser` is called for each non-empty line received from the stream, giving you full control over how the data is transformed before being yielded to your code.
