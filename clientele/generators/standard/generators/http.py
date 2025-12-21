from cicerone.spec import openapi_spec as cicerone_openapi_spec

from clientele.generators import base_http
from clientele.generators.standard import writer


def env_var(output_dir: str, key: str) -> str:
    """Generate environment variable name from output directory and key."""
    output_dir = output_dir.replace("/", "")
    return f"{output_dir.upper()}_{key.upper()}"


class HTTPGenerator(base_http.BaseHTTPGenerator):
    """
    Handles all the content generated in the http.py file for standard clients.
    """

    def __init__(self, spec: cicerone_openapi_spec.OpenAPISpec, output_dir: str, asyncio: bool) -> None:
        super().__init__(spec, output_dir, asyncio)
        self.writer = writer
