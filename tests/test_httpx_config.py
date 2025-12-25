"""Tests for extended httpx configuration options."""

import httpx
import pytest
from respx import MockRouter

from .test_class_client import config as class_config
from .test_class_client.client import Client
from .test_client import config, http


def test_functional_client_timeout_config():
    """Test that timeout configuration is accessible."""
    timeout = config.config.timeout
    assert timeout == 5.0
    assert isinstance(timeout, float)


def test_functional_client_follow_redirects_config():
    """Test that follow_redirects configuration is accessible."""
    follow_redirects = config.config.follow_redirects
    assert follow_redirects is False
    assert isinstance(follow_redirects, bool)


def test_functional_client_verify_ssl_config():
    """Test that verify_ssl configuration is accessible."""
    verify_ssl = config.config.verify_ssl
    assert verify_ssl is True
    assert isinstance(verify_ssl, bool)


def test_functional_client_http2_config():
    """Test that http2 configuration is accessible."""
    http2 = config.config.http2
    assert http2 is False
    assert isinstance(http2, bool)


def test_functional_client_max_redirects_config():
    """Test that max_redirects configuration is accessible."""
    max_redirects = config.config.max_redirects
    assert max_redirects == 20
    assert isinstance(max_redirects, int)


def test_class_based_client_config_defaults():
    """Test that class-based client Config has correct defaults."""
    cfg = class_config.Config()
    assert cfg.timeout == 5.0
    assert cfg.follow_redirects is False
    assert cfg.verify_ssl is True
    assert cfg.http2 is False
    assert cfg.max_redirects == 20


def test_class_based_client_config_custom_timeout():
    """Test that class-based client accepts custom timeout."""
    cfg = class_config.Config(timeout=10.0)
    assert cfg.timeout == 10.0


def test_class_based_client_config_custom_follow_redirects():
    """Test that class-based client accepts custom follow_redirects."""
    cfg = class_config.Config(follow_redirects=True)
    assert cfg.follow_redirects is True


def test_class_based_client_config_custom_verify_ssl():
    """Test that class-based client accepts custom verify_ssl."""
    cfg = class_config.Config(verify_ssl=False)
    assert cfg.verify_ssl is False


def test_class_based_client_config_custom_http2():
    """Test that class-based client accepts custom http2."""
    cfg = class_config.Config(http2=True)
    assert cfg.http2 is True


def test_class_based_client_config_custom_max_redirects():
    """Test that class-based client accepts custom max_redirects."""
    cfg = class_config.Config(max_redirects=10)
    assert cfg.max_redirects == 10


def test_class_based_client_config_all_custom():
    """Test that class-based client accepts all custom configurations."""
    cfg = class_config.Config(
        api_base_url="https://api.example.com",
        bearer_token="custom-token",
        timeout=15.0,
        follow_redirects=True,
        verify_ssl=False,
        http2=True,
        max_redirects=5,
    )
    assert cfg.api_base_url == "https://api.example.com"
    assert cfg.bearer_token == "custom-token"
    assert cfg.timeout == 15.0
    assert cfg.follow_redirects is True
    assert cfg.verify_ssl is False
    assert cfg.http2 is True
    assert cfg.max_redirects == 5


def test_class_based_client_with_custom_config():
    """Test that class-based client can be instantiated with custom config."""
    cfg = class_config.Config(
        api_base_url="http://test.example.com",
        timeout=10.0,
    )
    test_client = Client(config=cfg)
    assert test_client._http_client.config.timeout == 10.0
    assert test_client._http_client.config.api_base_url == "http://test.example.com"


@pytest.mark.respx(base_url="http://localhost")
def test_functional_client_uses_timeout(respx_mock: MockRouter):
    """Test that functional client uses timeout configuration."""
    # The httpx client should be created with the timeout from config
    assert isinstance(http.client.timeout, httpx.Timeout)


@pytest.mark.respx(base_url="http://localhost")
def test_functional_client_uses_follow_redirects(respx_mock: MockRouter):
    """Test that functional client uses follow_redirects configuration."""
    # The httpx client should be created with follow_redirects from config
    assert http.client.follow_redirects is False


@pytest.mark.respx(base_url="http://localhost")
def test_functional_client_uses_max_redirects(respx_mock: MockRouter):
    """Test that functional client uses max_redirects configuration."""
    # The httpx client should be created with max_redirects from config
    assert http.client.max_redirects == 20


def test_functional_client_limits_config():
    """Test that limits configuration is accessible and returns None by default."""
    limits = config.config.limits
    assert limits is None


def test_functional_client_transport_config():
    """Test that transport configuration is accessible and returns None by default."""
    transport = config.config.transport
    assert transport is None


def test_class_based_client_config_custom_limits():
    """Test that class-based client Config can be created with custom limits."""
    custom_limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    cfg = class_config.Config(limits=custom_limits)
    assert cfg.limits == custom_limits
    assert cfg.limits is not None
    assert cfg.limits.max_connections == 50


def test_class_based_client_config_custom_transport():
    """Test that class-based client Config can be created with custom transport."""
    custom_transport = httpx.HTTPTransport(retries=3)
    cfg = class_config.Config(transport=custom_transport)
    assert cfg.transport == custom_transport


def test_class_based_client_with_custom_limits():
    """Test that class-based client can be instantiated with custom limits."""
    custom_limits = httpx.Limits(max_connections=100)
    cfg = class_config.Config(limits=custom_limits)
    test_client = Client(config=cfg)
    # The client should use the custom limits
    assert test_client._http_client.config.limits == custom_limits


def test_class_based_client_with_custom_transport():
    """Test that class-based client can be instantiated with custom transport."""
    custom_transport = httpx.HTTPTransport(retries=5)
    cfg = class_config.Config(transport=custom_transport)
    test_client = Client(config=cfg)
    # The client should use the custom transport
    assert test_client._http_client.config.transport == custom_transport
