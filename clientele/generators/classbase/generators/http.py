"""
Wrapper for HTTP generator that uses classbase writer.
"""
import collections

import openapi_core
import rich.console

import clientele.generators.classbase.writer

console = rich.console.Console()


class HTTPGenerator:
    """
    Handles all the content generated in the http.py file.
    Uses classbase writer.
    """

    def __init__(self, spec: openapi_core.Spec, output_dir: str, asyncio: bool) -> None:
        self.spec = spec
        self.output_dir = output_dir
        self.results: dict[str, int] = collections.defaultdict(int)
        self.asyncio = asyncio
        self.function_and_status_codes_bundle: dict[str, dict[str, str]] = {}

    def add_status_codes_to_bundle(self, func_name: str, status_code_map: dict[str, str]) -> None:
        """
        Build a huge map of each function and it's status code responses.
        At the end of the client generation you should call http_generator.generate_http_content()
        """
        self.function_and_status_codes_bundle[func_name] = status_code_map

    def writeable_function_and_status_codes_bundle(self) -> str:
        return f"\nfunc_response_code_maps = {self.function_and_status_codes_bundle}"

    def generate_http_content(self) -> None:
        clientele.generators.classbase.writer.write_to_http(
            self.writeable_function_and_status_codes_bundle(), self.output_dir
        )
        client_generated = False
        client_type = "AsyncClient" if self.asyncio else "Client"
        if security_schemes := self.spec["components"].get("securitySchemes"):
            console.log("client has authentication...")
            for _, info in security_schemes.items():
                if (
                    info["type"] == "http"
                    and info["scheme"].lower() in ["basic", "bearer"]
                    and client_generated is False
                ):
                    client_generated = True
                    if info["scheme"] == "bearer":
                        template = clientele.generators.classbase.writer.templates.get_template("bearer_client.jinja2")
                        content = template.render(
                            client_type=client_type,
                        )
                    else:  # Can only be "basic" at this point
                        template = clientele.generators.classbase.writer.templates.get_template("basic_client.jinja2")
                        content = template.render(
                            client_type=client_type,
                        )
                    console.log(f"[yellow]Please see {self.output_dir}config.py to set authentication variables")
                elif info["type"] == "oauth2":
                    template = clientele.generators.classbase.writer.templates.get_template("bearer_client.jinja2")
                    content = template.render(
                        client_type=client_type,
                    )
                    client_generated = True
        if client_generated is False:
            console.log(f"Generating {'async' if self.asyncio else 'sync'} client...")
            template = clientele.generators.classbase.writer.templates.get_template("client.jinja2")
            content = template.render(client_type=client_type)
            client_generated = True
        clientele.generators.classbase.writer.write_to_http(content, output_dir=self.output_dir)
        if self.asyncio:
            content = clientele.generators.classbase.writer.templates.get_template("async_methods.jinja2").render()
        else:
            content = clientele.generators.classbase.writer.templates.get_template("sync_methods.jinja2").render()
        clientele.generators.classbase.writer.write_to_http(content, output_dir=self.output_dir)
