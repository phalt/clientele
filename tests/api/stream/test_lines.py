"""Tests for clientele.api.stream.lines."""

import json
import typing

import pytest

from clientele.api.stream import lines

# A JSONL body that exercises the awkward cases at once: CRLF and LF endings,
# blank lines, multi-byte UTF-8, and raw U+2028 / U+2029 inside JSON strings
# (valid JSON, and a line break for str.splitlines).
JSONL_BODY = (
    '{"text": "café \U0001f600"}\r\n'
    "\n"
    '{"text": "before after"}\n'
    "\r\n"
    '{"text": "para graph"}\n'
    '{"text": "no newline at end"}'
).encode("utf-8")

JSONL_LINES = [
    '{"text": "café \U0001f600"}',
    '{"text": "before after"}',
    '{"text": "para graph"}',
    '{"text": "no newline at end"}',
]


def split_at(body: bytes, *offsets: int) -> list[bytes]:
    """Split body into chunks at the given byte offsets."""
    bounds = [0, *offsets, len(body)]
    return [body[start:end] for start, end in zip(bounds, bounds[1:])]


async def as_async(chunks: typing.Iterable[bytes]) -> typing.AsyncGenerator[bytes, None]:
    for chunk in chunks:
        yield chunk


async def collect(chunks: typing.Iterable[bytes]) -> list[str]:
    return [line async for line in lines.aiter_lines(as_async(chunks))]


class TestIterLines:
    def test_single_chunk(self):
        assert list(lines.iter_lines([JSONL_BODY])) == JSONL_LINES

    def test_lines_are_valid_json(self):
        """Each yielded line is a complete JSON document."""
        for line in lines.iter_lines([JSONL_BODY]):
            json.loads(line)

    def test_line_separator_inside_json_string_is_not_a_line_break(self):
        body = '{"text": "a b"}\n{"text": "c d"}\n'.encode()
        assert list(lines.iter_lines([body])) == ['{"text": "a b"}', '{"text": "c d"}']

    @pytest.mark.parametrize("char", ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " "])
    def test_only_newline_splits_lines(self, char: str):
        """Characters that str.splitlines treats as line breaks stay inside the line."""
        body = f"left{char}right\n".encode()
        assert list(lines.iter_lines([body])) == [f"left{char}right"]

    def test_crlf_and_lf_both_end_lines(self):
        assert list(lines.iter_lines([b"a\r\nb\nc\r\n"])) == ["a", "b", "c"]

    def test_only_one_trailing_carriage_return_is_stripped(self):
        assert list(lines.iter_lines([b"a\r\r\n"])) == ["a\r"]

    def test_lone_carriage_return_is_not_a_line_break(self):
        assert list(lines.iter_lines([b"a\rb\n"])) == ["a\rb"]

    def test_crlf_split_across_chunks(self):
        assert list(lines.iter_lines([b"a\r", b"\nb\r", b"\n"])) == ["a", "b"]

    def test_blank_lines_are_dropped(self):
        assert list(lines.iter_lines([b"\n\r\na\n\n\nb\n\r\n"])) == ["a", "b"]

    def test_whitespace_only_lines_are_kept(self):
        """Only empty lines are dropped, matching the previous backend behaviour."""
        assert list(lines.iter_lines([b"a\n \nb\n"])) == ["a", " ", "b"]

    def test_final_line_without_newline_is_flushed(self):
        assert list(lines.iter_lines([b"a\nb"])) == ["a", "b"]

    def test_final_line_with_only_carriage_return_is_flushed(self):
        assert list(lines.iter_lines([b"a\r"])) == ["a"]

    def test_empty_input(self):
        assert list(lines.iter_lines([])) == []

    def test_empty_chunks_are_ignored(self):
        assert list(lines.iter_lines([b"", b"a", b"", b"\n", b""])) == ["a"]

    def test_line_spanning_many_chunks(self):
        body = b"x" * 10_000 + b"\n"
        chunks = [body[i : i + 7] for i in range(0, len(body), 7)]
        assert list(lines.iter_lines(chunks)) == ["x" * 10_000]

    def test_every_single_split_point(self):
        """Splitting the body at any byte offset, including inside a UTF-8 sequence, gives the same lines."""
        for offset in range(len(JSONL_BODY) + 1):
            assert list(lines.iter_lines(split_at(JSONL_BODY, offset))) == JSONL_LINES, offset

    def test_one_byte_chunks(self):
        chunks = [JSONL_BODY[i : i + 1] for i in range(len(JSONL_BODY))]
        assert list(lines.iter_lines(chunks)) == JSONL_LINES

    def test_invalid_utf8_is_replaced(self):
        assert list(lines.iter_lines([b"a\xffb\n"])) == ["a�b"]

    def test_truncated_utf8_at_end_is_replaced(self):
        assert list(lines.iter_lines([b"a\n\xe2\x80"])) == ["a", "�"]

    def test_lines_are_yielded_as_chunks_arrive(self):
        """A line is available as soon as its newline arrives, before later chunks are read."""
        consumed: list[bytes] = []

        def chunks() -> typing.Generator[bytes, None, None]:
            for chunk in (b"first\n", b"second\n"):
                consumed.append(chunk)
                yield chunk

        iterator = lines.iter_lines(chunks())
        assert next(iterator) == "first"
        assert consumed == [b"first\n"]


class TestAiterLines:
    @pytest.mark.asyncio
    async def test_single_chunk(self):
        assert await collect([JSONL_BODY]) == JSONL_LINES

    @pytest.mark.asyncio
    async def test_crlf_split_across_chunks(self):
        assert await collect([b"a\r", b"\nb\r", b"\n"]) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_blank_lines_are_dropped(self):
        assert await collect([b"\n\r\na\n\n\nb\n\r\n"]) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_final_line_without_newline_is_flushed(self):
        assert await collect([b"a\nb"]) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_empty_input(self):
        assert await collect([]) == []

    @pytest.mark.asyncio
    async def test_every_single_split_point(self):
        for offset in range(len(JSONL_BODY) + 1):
            assert await collect(split_at(JSONL_BODY, offset)) == JSONL_LINES, offset

    @pytest.mark.asyncio
    async def test_lines_are_yielded_as_chunks_arrive(self):
        consumed: list[bytes] = []

        async def chunks() -> typing.AsyncGenerator[bytes, None]:
            for chunk in (b"first\n", b"second\n"):
                consumed.append(chunk)
                yield chunk

        iterator = lines.aiter_lines(chunks())
        assert await anext(iterator) == "first"
        assert consumed == [b"first\n"]
