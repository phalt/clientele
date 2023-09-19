from collections import defaultdict

from openapi_core import Spec
from rich.console import Console

from src.settings import templates
from src.writer import write_to_http

console = Console()


def env_var(output_dir: str, key: str) -> str:
    output_dir = output_dir.replace("/", "")
    return f"{output_dir.upper()}_{key.upper()}"


class HTTPGenerator:
    """
    Handles all the content generated in the clients.py file.
    """

    def __init__(self, spec: Spec, output_dir: str, asyncio: bool) -> None:
        self.spec = spec
        self.output_dir = output_dir
        self.results: dict[str, int] = defaultdict(int)
        self.asyncio = asyncio

    def generate_http_content(self) -> None:
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
                        template = templates.get_template("bearer_client.jinja2")
                        content = template.render(
                            client_type=client_type,
                        )
                    else:  # Can only be "basic" at this point
                        template = templates.get_template("basic_client.jinja2")
                        content = template.render(
                            client_type=client_type,
                        )
                    console.log(
                        f"[yellow]Please see {self.output_dir}/constants.py to set authentication variables"
                    )
                elif info["type"] == "oauth2":
                    template = templates.get_template("bearer_client.jinja2")
                    content = template.render(
                        client_type=client_type,
                    )
                    client_generated = True
        if client_generated is False:
            console.log(f"Generating {'async' if self.asyncio else 'sync'} client...")
            template = templates.get_template("client.jinja2")
            content = template.render(client_type=client_type)
            client_generated = True
        write_to_http(content, output_dir=self.output_dir)
        if self.asyncio:
            content = templates.get_template("async_methods.jinja2").render()
        else:
            content = templates.get_template("sync_methods.jinja2").render()
        write_to_http(content, output_dir=self.output_dir)
