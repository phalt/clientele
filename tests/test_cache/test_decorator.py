from __future__ import annotations

import inspect

from clientele.cache.backends import MemoryBackend
from clientele.cache.decorator import (
    _extract_request_context,
    memoize,
)


class TestMemoizeDecorator:
    def test_memoize_preserves_function_name(self):
        """Decorator should preserve the original function name."""

        @memoize(ttl=300)
        def my_function():
            return "result"

        assert my_function.__name__ == "my_function"

    def test_memoize_preserves_function_signature(self):
        """Decorator should preserve the original function signature."""

        @memoize(ttl=300)
        def my_function(a: int, b: str, c: float = 3.14) -> str:
            return f"{a}-{b}-{c}"

        sig = inspect.signature(my_function)
        params = list(sig.parameters.keys())
        assert params == ["a", "b", "c"]

        # Check parameter types
        assert sig.parameters["a"].annotation == "int"
        assert sig.parameters["b"].annotation == "str"
        assert sig.parameters["c"].annotation == "float"
        assert sig.parameters["c"].default == 3.14

        # Check return type
        assert sig.return_annotation == "str"

    def test_memoize_preserves_docstring(self):
        """Decorator should preserve the original function docstring."""

        @memoize(ttl=300)
        def my_function():
            """This is a test function."""
            return "result"

        assert my_function.__doc__ == "This is a test function."

    def test_memoize_uses_custom_backend(self):
        """Decorator should use custom backend when provided."""
        custom_backend = MemoryBackend(max_size=50)

        @memoize(ttl=300, backend=custom_backend)
        def my_function(x: int) -> int:
            return x * 2

        # Call function
        result = my_function(5)
        assert result == 10

        # Verify it's stored in the custom backend
        # The key should exist in the custom backend
        assert custom_backend.exists("my_function:x=5")

    def test_memoize_with_custom_key_function(self):
        """Decorator should use custom key function when provided."""
        custom_backend = MemoryBackend()

        @memoize(ttl=300, backend=custom_backend, key=lambda x, y: f"custom:{x}")
        def my_function(x: int, y: int) -> int:
            return x + y

        # Call with different y values
        result1 = my_function(5, 10)
        result2 = my_function(5, 20)

        # Both should use the same cache key (ignoring y)
        assert result1 == 15  # First call
        assert result2 == 15  # Cached (same key despite different y)

        # Verify only one entry exists with the custom key
        assert custom_backend.exists("custom:5")

    def test_memoize_basic_caching(self):
        """Decorator should cache function results."""
        call_count = 0
        backend = MemoryBackend()

        @memoize(ttl=300, backend=backend)
        def my_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = my_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should use cache
        result2 = my_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

    def test_memoize_disabled(self):
        """Decorator with enabled=False should not cache."""
        call_count = 0
        backend = MemoryBackend()

        @memoize(ttl=300, backend=backend, enabled=False)
        def my_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = my_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should NOT use cache
        result2 = my_function(5)
        assert result2 == 10
        assert call_count == 2  # Incremented again

    def test_memoize_none_results_not_cached(self):
        """None results should not be cached."""
        call_count = 0
        backend = MemoryBackend()

        @memoize(ttl=300, backend=backend)
        def my_function(x: int):
            nonlocal call_count
            call_count += 1
            return None

        # First call
        result1 = my_function(5)
        assert result1 is None
        assert call_count == 1

        # Second call - should NOT use cache (None not cached)
        result2 = my_function(5)
        assert result2 is None
        assert call_count == 2  # Incremented again


class TestExtractRequestContext:
    """Tests for _extract_request_context function."""

    def test_extract_request_context_no_closure(self):
        """Function without closure should return (None, None)."""

        def regular_function():
            pass

        path, method = _extract_request_context(regular_function)
        assert path is None
        assert method is None

    def test_extract_request_context_with_mock_closure(self):
        """Function with clientele-like closure should extract context."""

        # Create a mock _RequestContext object
        class MockRequestContext:
            def __init__(self):
                self.path_template = "/pokemon/{id}"
                self.method = "get"

        # Create a function with closure containing the mock context
        context = MockRequestContext()

        def make_closure():
            # Capture context in closure
            ctx = context

            def inner():
                return ctx

            return inner

        func = make_closure()

        path, method = _extract_request_context(func)
        assert path == "/pokemon/{id}"
        assert method == "GET"  # Should be uppercase

    def test_extract_request_context_handles_exceptions(self):
        """Function should gracefully handle exceptions."""

        # Create a function with a problematic closure
        class ProblematicObject:
            @property
            def __dict__(self):
                raise AttributeError("Boom!")

        obj = ProblematicObject()

        def make_closure():
            captured = obj

            def inner():
                return captured

            return inner

        func = make_closure()

        # Should not raise, should return (None, None)
        path, method = _extract_request_context(func)
        assert path is None
        assert method is None

    def test_extract_request_context_missing_attributes(self):
        """Function with incomplete closure should return (None, None)."""

        class IncompleteContext:
            def __init__(self):
                self.path_template = "/users"
                # Missing 'method' attribute

        context = IncompleteContext()

        def make_closure():
            ctx = context

            def inner():
                return ctx

            return inner

        func = make_closure()

        path, method = _extract_request_context(func)
        assert path is None
        assert method is None

    def test_extract_request_context_wrong_types(self):
        """Function with wrong attribute types should return (None, None)."""

        class WrongTypeContext:
            def __init__(self):
                self.path_template = 123  # Should be string
                self.method = "get"

        context = WrongTypeContext()

        def make_closure():
            ctx = context

            def inner():
                return ctx

            return inner

        func = make_closure()

        path, method = _extract_request_context(func)
        assert path is None
        assert method is None

    def test_extract_request_context_multiple_closure_cells(self):
        """Should find context even with multiple closure variables."""

        class MockRequestContext:
            def __init__(self):
                self.path_template = "/items/{id}"
                self.method = "post"

        context = MockRequestContext()
        other_var = "something else"

        def make_closure():
            ctx = context
            var = other_var

            def inner():
                return ctx, var

            return inner

        func = make_closure()

        path, method = _extract_request_context(func)
        assert path == "/items/{id}"
        assert method == "POST"
