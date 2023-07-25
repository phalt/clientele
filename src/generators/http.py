from collections import defaultdict
from typing import Dict

from openapi_core import Spec
from rich.console import Console

from src.writer import write_to_http

console = Console()

BEARER_CLIENT = """
auth_key = c.get_bearer_token()
headers = dict(Authorization=f'Bearer ' + auth_key)
client = httpx.{client_type}(headers=headers)
"""

BASIC_CLIENT = """
client = httpx.{client_type}(auth=(c.get_user_key(), c.get_pass_key()))
"""

NO_AUTH_CLIENT = """
client = httpx.{client_type}()
"""

SYNC_METHODS = """
def get(url: str) -> httpx.Response:
    return client.get(parse_url(url))


def post(url: str, data: typing.Dict) -> httpx.Response:
    return client.post(parse_url(url), json=data)
"""

ASYNC_METHODS = """
async def get(url: str) -> httpx.Response:
    return await client.get(parse_url(url))


async def post(url: str, data: typing.Dict) -> httpx.Response:
    return await client.post(parse_url(url), json=data)
"""


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
        self.results: Dict[str, int] = defaultdict(int)
        self.asyncio = asyncio

    def generate_http_content(self) -> None:
        client_generated = False
        client_type = "AsyncClient" if self.asyncio else "Client"
        if security_schemes := self.spec["components"].get("securitySchemes"):
            console.log("Generating client with authentication...")
            for _, info in security_schemes.items():
                if (
                    info["type"] == "http"
                    and info["scheme"] in ["basic", "bearer"]
                    and client_generated is False
                ):
                    client_generated = True
                    if info["scheme"] == "bearer":
                        content = BEARER_CLIENT.format(
                            client_type=client_type,
                        )
                    else:  # Can only be "basic" at this point
                        content = BASIC_CLIENT.format(
                            client_type=client_type,
                        )
                    console.log(
                        f"[yellow]Please see {self.output_dir}constants.py to set authentication variables"
                    )
        if client_generated is False:
            console.log(f"Generating {'async' if self.asyncio else 'sync'} client...")
            content = NO_AUTH_CLIENT.format(client_type=client_type)
            client_generated = True
        write_to_http(content, output_dir=self.output_dir)
        if self.asyncio:
            write_to_http(ASYNC_METHODS, output_dir=self.output_dir)
        else:
            write_to_http(SYNC_METHODS, output_dir=self.output_dir)
