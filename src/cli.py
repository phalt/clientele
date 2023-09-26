import click


@click.group()
def cli_group():
    """
    Clientele:  Generate loveable Python HTTP API Clients
    https://github.com/phalt/clientele
    """


@click.command()
def version():
    """
    Print the current version of clientele
    """
    from src.settings import VERSION

    print(f"clientele {VERSION}")


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (json file)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json file)", required=False)
def validate(url, file):
    """
    Validate an OpenAPI schema. Will error if anything is wrong with the schema
    """
    from json import JSONDecodeError

    import yaml
    from httpx import Client
    from openapi_core import Spec
    from rich.console import Console

    console = Console()

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
            Spec.from_file(f)
    console.log(
        f"Found API specification: {spec['info']['title']} | version {spec['info']['version']}"
    )
    major, _, _ = spec["openapi"].split(".")
    if int(major) < 3:
        console.log(
            f"[red]Clientele only supports OpenAPI version 3.0.0 and up, and you have {spec['openapi']}"
        )
        return
    console.log("schema validated successfully! You can generate a client with it")


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (json file)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json file)", required=False)
@click.option(
    "-o", "--output", help="Directory for the generated client", required=True
)
@click.option("-a", "--asyncio", help="Use Async.IO", required=False)
def generate(url, file, output, asyncio):
    """
    Generate a new client from an OpenAPI schema
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
        f"Found API specification: {spec['info']['title']} | version {spec['info']['version']}"
    )
    major, _, _ = spec["openapi"].split(".")
    if int(major) < 3:
        console.log(
            f"[red]Clientele only supports OpenAPI version 3.0.0 and up, and you have {spec['openapi']}"
        )
        return
    Generator(
        spec=spec, asyncio=asyncio, output_dir=output, url=url, file=file
    ).generate()
    console.log("\n[green]⚜️ Client generated! ⚜️ \n")
    console.log(
        "[yellow]REMEMBER: install `httpx` `pydantic`, and `respx` to use your new client"
    )


cli_group.add_command(generate)
cli_group.add_command(version)
cli_group.add_command(validate)

if __name__ == "__main__":
    cli_group()
