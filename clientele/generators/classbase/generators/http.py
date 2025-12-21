"""
HTTP generator for class-based clients.
"""

from cicerone.spec import openapi_spec as cicerone_openapi_spec

from clientele.generators import base_http
from clientele.generators.classbase import writer


class HTTPGenerator(base_http.BaseHTTPGenerator):
    """
    Handles all the content generated in the http.py file for class-based clients.
    """

    def __init__(self, spec: cicerone_openapi_spec.OpenAPISpec, output_dir: str, asyncio: bool) -> None:
        super().__init__(spec, output_dir, asyncio)
        self.writer = writer
