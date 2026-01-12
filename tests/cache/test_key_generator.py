from __future__ import annotations

from clientele.cache.key_generator import (
    extract_path_params,
    generate_cache_key,
    serialize_value,
)


class TestSerializeValue:
    def test_serialize_none(self):
        assert serialize_value(None) == "null"

    def test_serialize_bool(self):
        assert serialize_value(True) == "True"
        assert serialize_value(False) == "False"

    def test_serialize_int(self):
        assert serialize_value(42) == "42"
        assert serialize_value(0) == "0"
        assert serialize_value(-100) == "-100"

    def test_serialize_float(self):
        assert serialize_value(3.14) == "3.14"
        assert serialize_value(0.0) == "0.0"
        assert serialize_value(-2.5) == "-2.5"

    def test_serialize_string(self):
        assert serialize_value("hello") == "hello"
        assert serialize_value("") == ""
        assert serialize_value("with spaces") == "with spaces"

    def test_serialize_dict(self):
        result = serialize_value({"b": 2, "a": 1})
        assert result == '{"a":1,"b":2}'

    def test_serialize_dict_nested(self):
        result = serialize_value({"z": {"y": 1, "x": 2}, "a": 3})
        # Keys should be sorted at all levels
        assert '"a":3' in result
        assert '"z":' in result
        assert '"x":2' in result
        assert '"y":1' in result

    def test_serialize_list(self):
        result = serialize_value([1, 2, 3])
        assert result == "[1,2,3]"

    def test_serialize_list_with_dicts(self):
        result = serialize_value([{"b": 2, "a": 1}])
        assert result == '[{"a":1,"b":2}]'

    def test_serialize_pydantic_model(self):
        class MockModel:
            def model_dump(self):
                return {"name": "test", "id": 123}

        model = MockModel()
        result = serialize_value(model)
        assert result == '{"id":123,"name":"test"}'

    def test_serialize_unknown_type(self):
        class CustomClass:
            def __repr__(self):
                return "<CustomClass>"

        obj = CustomClass()
        assert serialize_value(obj) == "<CustomClass>"


class TestExtractPathParams:
    def test_extract_single_param(self):
        result = extract_path_params("/pokemon/{id}")
        assert result == ["id"]

    def test_extract_multiple_params(self):
        result = extract_path_params("/users/{user_id}/posts/{post_id}")
        assert result == ["user_id", "post_id"]

    def test_extract_no_params(self):
        result = extract_path_params("/users")
        assert result == []

    def test_extract_params_with_complex_names(self):
        result = extract_path_params("/api/v1/{resource_id}/items/{item_123}")
        assert result == ["resource_id", "item_123"]

    def test_extract_adjacent_params(self):
        result = extract_path_params("/{first}/{second}")
        assert result == ["first", "second"]


class TestGenerateCacheKey:
    def test_generate_cache_key_with_path_template(self):
        def dummy_func(id: int):
            pass

        result = generate_cache_key(dummy_func, (25,), {}, "/pokemon/{id}")
        assert result == "/pokemon/{id}:id=25"

    def test_generate_cache_key_without_path_template(self):
        def get_pokemon(id: int):
            pass

        result = generate_cache_key(get_pokemon, (25,), {}, None)
        assert result == "get_pokemon:id=25"

    def test_generate_cache_key_no_params(self):
        def list_all():
            pass

        result = generate_cache_key(list_all, (), {}, "/users")
        assert result == "/users"

    def test_generate_cache_key_excludes_result_param(self):
        def get_user(id: int, result: dict):
            pass

        result = generate_cache_key(get_user, (123, {}), {}, "/users/{id}")
        assert result == "/users/{id}:id=123"
        assert "result" not in result

    def test_generate_cache_key_excludes_response_param(self):
        def get_user(id: int, response: dict):
            pass

        result = generate_cache_key(get_user, (123, {}), {}, "/users/{id}")
        assert result == "/users/{id}:id=123"
        assert "response" not in result

    def test_generate_cache_key_excludes_data_param(self):
        def create_user(name: str, data: dict):
            pass

        # Note: This shouldn't be used for POST but testing the filtering
        result = generate_cache_key(create_user, ("Alice", {}), {}, "/users")
        assert result == "/users:name=Alice"
        assert "data" not in result

    def test_generate_cache_key_excludes_all_reserved_params(self):
        def complex_function(id: int, name: str, result: dict, response: dict, data: dict):
            pass

        cache_key = generate_cache_key(
            complex_function,
            (123, "Alice", {}, {}, {}),
            {},
            "/users/{id}",
        )
        assert cache_key == "/users/{id}:id=123:name=Alice"
        assert "result" not in cache_key
        assert "response" not in cache_key
        assert "data" not in cache_key

    def test_generate_cache_key_deterministic_ordering(self):
        def search(z: int, a: int, m: int):
            pass

        result = generate_cache_key(search, (), {"z": 1, "a": 2, "m": 3}, "/search")
        assert result == "/search:a=2:m=3:z=1"

    def test_generate_cache_key_with_kwargs(self):
        def search(query: str, limit: int):
            pass

        result = generate_cache_key(search, (), {"query": "python", "limit": 10}, "/search")
        assert result == "/search:limit=10:query=python"

    def test_generate_cache_key_mixed_args_kwargs(self):
        def get_post(user_id: int, post_id: int):
            pass

        result = generate_cache_key(get_post, (123,), {"post_id": 456}, "/users/{user_id}/posts/{post_id}")
        assert result == "/users/{user_id}/posts/{post_id}:post_id=456:user_id=123"

    def test_generate_cache_key_with_defaults(self):
        def search(query: str, limit: int = 10):
            pass

        result = generate_cache_key(search, ("python",), {}, "/search")
        assert result == "/search:limit=10:query=python"

    def test_generate_cache_key_complex_values(self):
        def search(query: str, filters: dict):
            pass

        result = generate_cache_key(
            search,
            (),
            {"query": "test", "filters": {"status": "active", "type": "user"}},
            "/search",
        )
        assert "query=test" in result
        # Dict should be serialized as sorted JSON
        assert 'filters={"status":"active","type":"user"}' in result

    def test_generate_cache_key_with_none_values(self):
        def get_user(id: int, role: None):
            pass

        result = generate_cache_key(get_user, (123, None), {}, "/users/{id}")
        assert result == "/users/{id}:id=123:role=null"

    def test_generate_cache_key_consistency(self):
        def search(a: int, b: int, c: int):
            pass

        key1 = generate_cache_key(search, (), {"a": 1, "b": 2, "c": 3}, "/search")
        key2 = generate_cache_key(search, (), {"c": 3, "a": 1, "b": 2}, "/search")
        key3 = generate_cache_key(search, (), {"b": 2, "c": 3, "a": 1}, "/search")

        # All should be identical despite different kwarg order
        assert key1 == key2 == key3
