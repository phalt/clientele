"""
Classification of OpenAPI security schemes for client generation.

The generator can produce typed credential fields for the common schemes:
HTTP bearer, HTTP basic, and API keys sent in a header. Everything else
(oauth2, openIdConnect, mutualTLS, API keys in query/cookie) requires
manual configuration. This module classifies a spec's securitySchemes so
the generator and the validator agree on what is supported.
"""

import typing

from cicerone.spec import openapi_spec as cicerone_openapi_spec

from clientele.generators.shared import utils

# Field names already used by BaseConfig that credential fields must not shadow
RESERVED_CONFIG_FIELDS = frozenset(
    {
        "base_url",
        "headers",
        "timeout",
        "follow_redirects",
        "verify",
        "http2",
        "cache_backend",
        "http_backend",
        "logger",
        "bearer_token",
        "basic_username",
        "basic_password",
    }
)


def describe_scheme(scheme: typing.Any) -> str:
    """A short human-readable description of a security scheme."""
    scheme_type = getattr(scheme, "type", None) or "unknown"
    if scheme_type == "apiKey":
        return f"apiKey in {getattr(scheme, 'in_', None)}"
    if scheme_type == "http":
        return f"http {(getattr(scheme, 'scheme', None) or '').lower()}"
    return scheme_type


def classify_security_schemes(spec: cicerone_openapi_spec.OpenAPISpec) -> typing.Optional[dict]:
    """
    Classify a spec's securitySchemes into what the generator supports.

    Returns None when the spec declares no security schemes, otherwise a dict:
        bearer:      {"scheme_name": str} or None (first http/bearer scheme)
        basic:       {"scheme_name": str} or None (first http/basic scheme)
        api_keys:    [{"scheme_name": str, "header_name": str, "field_name": str}]
        unsupported: [{"scheme_name": str, "description": str}]
    """
    components = spec.components
    schemes = getattr(components, "security_schemes", None) if components else None
    if not schemes:
        return None

    bearer: typing.Optional[dict] = None
    basic: typing.Optional[dict] = None
    api_keys: list[dict] = []
    unsupported: list[dict] = []

    for name, scheme in schemes.items():
        scheme_type = getattr(scheme, "type", None)
        http_scheme = (getattr(scheme, "scheme", None) or "").lower()
        in_ = getattr(scheme, "in_", None)
        if scheme_type == "http" and http_scheme == "bearer" and bearer is None:
            bearer = {"scheme_name": name}
        elif scheme_type == "http" and http_scheme == "basic" and basic is None:
            basic = {"scheme_name": name}
        elif scheme_type == "apiKey" and in_ == "header":
            api_keys.append({"scheme_name": name, "header_name": scheme.name})
        else:
            unsupported.append({"scheme_name": name, "description": describe_scheme(scheme)})

    if len(api_keys) == 1:
        api_keys[0]["field_name"] = "api_key"
    else:
        seen: set[str] = set(RESERVED_CONFIG_FIELDS)
        for api_key in api_keys:
            field_name = utils.snake_case_prop(api_key["scheme_name"])
            while field_name in seen:
                field_name = f"{field_name}_key"
            seen.add(field_name)
            api_key["field_name"] = field_name

    return {
        "bearer": bearer,
        "basic": basic,
        "api_keys": api_keys,
        "unsupported": unsupported,
    }
