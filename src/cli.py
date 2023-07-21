import click


@click.group()
def cli_group():
    """
    Beckett-API:  Typed API Clients from OpenAPI specs
    """


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (json file)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json file)", required=False)
@click.option(
    "-o", "--output", help="Directory for the generated client", required=True
)
@click.option("-a", "--asyncio", help="Use Async.IO", required=False)
@click.option("-d", "--debug", help="Print debug information", default=False)
def generate(url, file, output, asyncio, debug):
    """
    Generate a new client.
    """
    from httpx import Client
    from openapi_core import Spec
    from rich.pretty import pprint
    from structlog import get_logger

    from src.generator import Generator

    log = get_logger(__name__)
    if url:
        client = Client()
        spec = Spec.from_dict(client.get(url).json())
    else:
        spec = Spec.from_file(file)
    if debug:
        pprint(spec["info"])
    log.info(
        f"Found API client for {spec['info']['title']} | version {spec['info']['version']}"
    )
    Generator(spec=spec).generate(url=url, output_dir=output)


cli_group.add_command(generate)

if __name__ == "__main__":
    cli_group()
