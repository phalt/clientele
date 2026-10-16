"""Tests for clientele.http.response module."""

import pytest

from clientele import api, cache, http
from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.cache import types as cache_types
from clientele.http import response as http_response


class TestRaiseForStatus:
    @pytest.mark.parametrize("status_code", [400, 404, 500, 599])
    def test_raises_http_status_error_for_error_status(self, status_code):
        resp = http_response.Response(status_code=status_code, headers={}, content=b"")
        with pytest.raises(http_response.HTTPStatusError) as exc_info:
            resp.raise_for_status()
        assert exc_info.value.response is resp
        assert exc_info.value.reason == f"HTTP {status_code}"

    @pytest.mark.parametrize("status_code", [200, 204, 301, 399])
    def test_does_not_raise_for_other_status(self, status_code):
        resp = http_response.Response(status_code=status_code, headers={}, content=b"")
        resp.raise_for_status()


class TestMovedClassesKeepTheirOldImportPaths:
    def test_exceptions(self):
        assert api.APIException is http.APIException
        assert api_exceptions.APIException is http_response.APIException
        assert api_exceptions.HTTPStatusError is http.HTTPStatusError
        assert issubclass(http.HTTPStatusError, api.APIException)

    def test_cache_backend(self):
        assert cache.CacheBackend is api_config.CacheBackend
        assert cache_types.CacheBackend is api_config.CacheBackend
