"""
Split a streamed HTTP body into lines.

HTTP backends hand clientele.api raw byte chunks; this module turns them into
lines for line-delimited streams such as JSONL.

Only ``\\n`` ends a line, and one trailing ``\\r`` is stripped. The HTTP
libraries' own line iterators follow ``str.splitlines`` and also break on
characters such as U+2028, which JSON allows unescaped inside strings, so a
JSONL record containing one would be cut in half.
"""

from __future__ import annotations

import codecs
import typing


class LineDecoder:
    """
    Incrementally decode UTF-8 byte chunks into complete lines.

    Chunks may split a line or a multi-byte character at any point. Empty
    lines are dropped. Invalid UTF-8 is replaced with U+FFFD.
    """

    def __init__(self) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        # Text received since the last newline, kept as parts so that a long
        # line spread over many chunks is joined once, not re-copied per chunk.
        self._pending: list[str] = []

    def decode(self, chunk: bytes) -> list[str]:
        """Feed one chunk and return the lines it completes."""
        text = self._decoder.decode(chunk)
        if "\n" not in text:
            if text:
                self._pending.append(text)
            return []

        first, *rest = text.split("\n")
        self._pending.append(first)
        completed = ["".join(self._pending), *rest[:-1]]
        self._pending = [rest[-1]] if rest[-1] else []
        return [line for raw in completed if (line := raw.removesuffix("\r"))]

    def flush(self) -> list[str]:
        """Return the final line if the body did not end with a newline."""
        self._pending.append(self._decoder.decode(b"", final=True))
        line = "".join(self._pending).removesuffix("\r")
        self._pending = []
        return [line] if line else []


def iter_lines(chunks: typing.Iterable[bytes]) -> typing.Generator[str, None, None]:
    """Yield each non-empty line from a sync stream of byte chunks."""
    decoder = LineDecoder()
    for chunk in chunks:
        yield from decoder.decode(chunk)
    yield from decoder.flush()


async def aiter_lines(chunks: typing.AsyncIterable[bytes]) -> typing.AsyncGenerator[str, None]:
    """Yield each non-empty line from an async stream of byte chunks."""
    decoder = LineDecoder()
    async for chunk in chunks:
        for line in decoder.decode(chunk):
            yield line
    for line in decoder.flush():
        yield line
