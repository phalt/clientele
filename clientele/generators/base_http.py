"""Base HTTP generator shared by standard and classbase generators."""

import collections
import pathlib
import typing

from cicerone.spec import openapi_spec as cicerone_openapi_spec
from rich import console as rich_console

console = rich_console.Console()


class BaseHTTPGenerator:
    """
    Base class for generating HTTP client code from OpenAPI specifications.
    Handles authentication schemes and HTTP client configuration.
    """

    spec: cicerone_openapi_spec.OpenAPISpec
    output_dir: str
    results: dict[str, int]
    asyncio: bool
    function_and_status_codes_bundle: dict[str, dict[str, str]]
    writer: typing.Any  # Must be set by subclass

    def __init__(self, spec: cicerone_openapi_spec.OpenAPISpec, output_dir: str, asyncio: bool) -> None:
        self.spec = spec
        self.output_dir = output_dir
        self.results = collections.defaultdict(int)
        self.asyncio = asyncio
        self.function_and_status_codes_bundle = {}

    def add_status_codes_to_bundle(self, func_name: str, status_code_map: dict[str, str]) -> None:
        """
        Build a huge map of each function and it's status code responses.
        At the end of the client generation you should call http_generator.generate_http_content()
        """
        self.function_and_status_codes_bundle[func_name] = status_code_map

    def writeable_function_and_status_codes_bundle(self) -> str:
        """Format the function-to-status-code mapping as readable Python code."""
        import json

        # Use json.dumps with indentation for readable multi-line output
        json_str = json.dumps(self.function_and_status_codes_bundle, indent=4)
        return f"\nfunc_response_code_maps = {json_str}\n"

    def generate_http_content(self) -> None:
        """Generate HTTP client setup code."""
        self.writer.write_to_http(self.writeable_function_and_status_codes_bundle(), self.output_dir)
        client_generated = False
        client_type = "AsyncClient" if self.asyncio else "Client"

        # Check if the spec has security schemes
        security_schemes = None
        if self.spec.components and self.spec.components.security_schemes:
            security_schemes = self.spec.components.security_schemes

        if security_schemes:
            console.log("client has authentication...")
            for _, info in security_schemes.items():
                if (
                    info.type == "http"
                    and info.scheme
                    and info.scheme.lower() in ["basic", "bearer"]
                    and client_generated is False
                ):
                    client_generated = True
                    if info.scheme == "bearer":
                        template = self.writer.templates.get_template("bearer_client.jinja2")
                        content = template.render(
                            client_type=client_type,
                        )
                    else:  # Can only be "basic" at this point
                        template = self.writer.templates.get_template("basic_client.jinja2")
                        content = template.render(
                            client_type=client_type,
                        )
                    console.log(
                        f"[yellow]Please see {pathlib.Path(self.output_dir) / 'config.py'} "
                        "to set authentication variables"
                    )
                elif info.type == "oauth2":
                    template = self.writer.templates.get_template("bearer_client.jinja2")
                    content = template.render(
                        client_type=client_type,
                    )
                    client_generated = True
        if client_generated is False:
            console.log(f"Generating {'async' if self.asyncio else 'sync'} client...")
            template = self.writer.templates.get_template("client.jinja2")
            content = template.render(client_type=client_type)
            client_generated = True
        self.writer.write_to_http(content, output_dir=self.output_dir)
        if self.asyncio:
            content = self.writer.templates.get_template("async_methods.jinja2").render()
        else:
            content = self.writer.templates.get_template("sync_methods.jinja2").render()
        self.writer.write_to_http(content, output_dir=self.output_dir)
