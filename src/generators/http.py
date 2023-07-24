from collections import defaultdict
from typing import Dict

from openapi_core import Spec
from rich.console import Console

from src.writer import write_to_http

console = Console()

BEARER_CLIENT = """
AUTH_TOKEN = environ.get("{bearer_token_key}")
headers = dict(Authorization=f'Bearer {{AUTH_TOKEN}}')
client = httpx.{client_type}(headers=headers)
"""

BASIC_CLIENT = """
AUTH_USER = environ.get("{user_key}")
AUTH_PASS = environ.get("{pass_key}")
client = httpx.{client_type}(auth=(AUTH_USER, AUTH_PASS))
"""

NO_AUTH_CLIENT = """
client = httpx.{client_type}()
"""

SYNC_METHODS = """
def get(url: str) -> httpx.Response:
    return client.get(url)


def post(url: str, data: typing.Dict) -> httpx.Response:
    return client.post(url, json=data)
"""

ASYNC_METHODS = """
async def get(url: str) -> httpx.Response:
    return await client.get(url)


async def post(url: str, data: typing.Dict) -> httpx.Response:
    return await client.post(url, json=data)
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
                        test_key = env_var(output_dir=self.output_dir, key="AUTH_KEY")
                        content = BEARER_CLIENT.format(
                            client_type=client_type,
                            bearer_token_key=f"{test_key}",
                        )
                        console.log(
                            f"[yellow]Please use \n* {test_key}\nenvironment variable to use bearer authentication"
                        )
                    else:  # Can only be "basic" at this point
                        user_key = env_var(
                            output_dir=self.output_dir, key="AUTH_USER_KEY"
                        )
                        pass_key = env_var(
                            output_dir=self.output_dir, key="AUTH_PASS_KEY"
                        )
                        console.log(
                            f"[yellow]Please set \n* {user_key}\n* {pass_key} \nenvironment variable to use basic authentication"  # noqa
                        )
                        content = BASIC_CLIENT.format(
                            client_type=client_type,
                            user_key=f"{user_key}",
                            pass_key=f"{pass_key}",
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
