import click


@click.group()
def cli_group():
    """
    Clientele:  Typed API Clients from OpenAPI schemas
    """


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (json file)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json file)", required=False)
@click.option(
    "-o", "--output", help="Directory for the generated client", required=True
)
@click.option("-a", "--asyncio", help="Use Async.IO", required=False)
def generate(url, file, output, asyncio):
    """
    Generate a new client from an openapi.json spec
    """
    from json import JSONDecodeError

    import yaml
    from httpx import Client
    from openapi_core import Spec
    from rich.console import Console

    console = Console()

    from src.generator import Generator

    assert url or file, "Must pass either a URL or a file"

    if url:
        client = Client()
        response = client.get(url)
        try:
            data = response.json()
        except JSONDecodeError:
            # It's probably yaml
            data = yaml.safe_load(response.content)
        spec = Spec.from_dict(data)
    else:
        with open(file, "r") as f:
            spec = Spec.from_file(f)
    console.log(
        f"Found API specification for {spec['info']['title']} | version {spec['info']['version']}"
    )
    major, _, _ = spec["openapi"].split(".")
    if int(major) < 3:
        console.log(
            f"[red]clientele only supports OpenAPI version 3.0.0 and up, and you have {spec['openapi']}"
        )
        return
    console.log(f"OpenAPI version {spec['openapi']}")
    if asyncio:
        console.log("Generating async client...")
    else:
        console.log("Generating sync client...")
    Generator(spec=spec, asyncio=asyncio, output_dir=output).generate()


cli_group.add_command(generate)

if __name__ == "__main__":
    cli_group()
