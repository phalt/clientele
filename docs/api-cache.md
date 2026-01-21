# 💾 Caching

Clientele provides built-in support for caching HTTP GET requests using the `@memoize` decorator.

## Quick Start

```python
from clientele import api, cache

client = api.APIClient(base_url="https://api.example.com")

@cache.memoize(ttl=300)  # Cache for 5 minutes
@client.get("/users/{id}")
def get_user(id: int, result: dict) -> dict:
    return result

# First call - hits the API
user = get_user(id=123)

# Second call - returns cached result
user = get_user(id=123)  # No HTTP request made!
```

## How It Works

The `@memoize` decorator:

1. **Extracts request context** from the underlying `@client.get()` decorator
2. **Generates cache keys** from the HTTP method, path template, and function parameters
3. **Checks the cache** before executing the HTTP request
4. **Stores results** with optional TTL (time-to-live) expiration
5. **Respects LRU eviction** when the cache reaches its maximum size

!!! warning "GET Requests Only"
    Only use `@memoize` with GET requests (idempotent operations). POST/PUT/PATCH/DELETE should **not** be cached as they modify server state.

## Configuration

### Basic TTL (Time-To-Live)

Set how long cached responses remain valid:

```python
@memoize(ttl=300)  # 5 minutes
@client.get("/pokemon/{id}")
def get_pokemon(id: int, result: dict) -> dict:
    return result
```

### Custom Cache Keys

Override the default key generation with a custom function:

```python
@memoize(
    ttl=600,
    key=lambda user_id: f"user:{user_id}"  # Custom key format
)
@client.get("/users/{user_id}")
def get_user(user_id: int, result: dict) -> dict:
    return result
```

The custom key function receives all parameters **except** `result` and `response` (which are injected by Clientele).

### Conditional Caching

Enable or disable caching based on configuration:

```python
import os

ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true") == "true"

@memoize(ttl=300, enabled=ENABLE_CACHE)
@client.get("/pokemon/{id}")
def get_pokemon(id: int, result: dict) -> dict:
    return result
```

### Custom Backend

Swap the default in-memory backend for your own:

```python
from clientele.cache import memoize, MemoryBackend

# Create a backend with smaller cache size
small_cache = MemoryBackend(max_size=50)

@memoize(ttl=300, backend=small_cache)
@client.get("/items/{id}")
def get_item(id: int, result: dict) -> dict:
    return result
```

Alternatively you can set it through the `BaseConfig` object to prevent constantly setting it through the decorator:

```python
from clientele import api, cache

client = api.APIClient(config=api.BaseConfig(
    base_url="https://myapi.com/",
    # Set to your own backend here
    cache_backend=cache.MemoryBackend
))

@cache.memoize(ttl=300)
@client.get("/items/{id}")
def get_item(id: int, result: dict) -> dict:
    return result
```


## Async Support

The `@memoize` decorator works seamlessly with async functions:

```python
@memoize(ttl=300)
@client.get("/users/{id}")
async def get_user(id: int, result: dict) -> dict:
    return result

# Usage
user = await get_user(id=123)
user = await get_user(id=123)  # Cached!
```

## Cache Key Generation

Cache keys are automatically generated from:

1. **HTTP method** - Prepended to the key (e.g., `GET:`)
2. **Path template** - The API endpoint path
3. **Function parameters** - Sorted alphabetically for consistency

Example cache keys:

```python
# GET /pokemon/{id} with id=25
# Key: "GET:/pokemon/{id}:id=25"

# GET /search with query="python", limit=10
# Key: "GET:/search:limit=10:query=python"
```

### Excluded Parameters

The following parameters are **automatically excluded** from cache keys because they are injected by Clientele at runtime:

- `result` - The parsed response object
- `response` - The raw HTTP response
- `data` - The request body

## Writing a Custom Backend

The `MemoryBackend` is suitable for single-process applications.

For production systems, you may want Redis, Memcached, or disk-based caching.

### Redis Backend example

Implement the `CacheBackend` protocol:

```python
import redis
from typing import Any, Optional
from clientele import cache

class RedisBackend(cache.CacheBackend):
    """Redis-based cache backend example."""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis."""
        import pickle
        data = self.redis.get(key)
        if data is None:
            return None
        return pickle.loads(data)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in Redis with optional TTL."""
        import pickle
        serialized = pickle.dumps(value)
        if ttl is not None:
            self.redis.setex(key, ttl, serialized)
        else:
            self.redis.set(key, serialized)
    
    def delete(self, key: str) -> None:
        """Remove a value from Redis."""
        self.redis.delete(key)
    
    def clear(self) -> None:
        """Clear all values (use with caution!)."""
        self.redis.flushdb()
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        return bool(self.redis.exists(key))
```

### Using Your Custom Backend

```python
from clientele import cache

# Create and configure your backend
redis_cache = RedisBackend(redis_url="redis://localhost:6379/0")

# Use per-decorator
@cache.memoize(ttl=300, backend=redis_cache)
@client.get("/users/{id}")
def get_user(id: int, result: dict) -> dict:
    return result
```

- [API Configuration](api-configuration.md) - General API client configuration
- [Async Support](api-async.md) - Using async/await with Clientele
- [Testing](api-testing.md) - How to test code that uses caching
