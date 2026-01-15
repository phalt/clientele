import typing

from clientele import cache


class FakeCacheBackend(cache.CacheBackend):
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        if key in self.store:
            del self.store[key]

    def clear(self):
        self.store = {}

    def exists(self, key):
        return key in self.store

    def set(self, key: str, value: typing.Any, ttl: typing.Optional[int | float] = None) -> None:
        self.store[key] = value
