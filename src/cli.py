import click


@click.group()
def cli_group():
    """
    Typed Python OpenAPI Clients
    """


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (json file)", required=True)
@click.option(
    "-o", "--output", help="Directory for the generated client", required=True
)
def generate(url, output):
    """
    Generate a new client.
    """
    from openapi_parser import parse
    from structlog import get_logger

    from src.generator import generate

    log = get_logger(__name__)
    spec = parse(url)
    log.info(f"Found API client for {spec.info.title} | version {spec.info.version}")
    generate(url=url, specification=spec, output_dir=output)


cli_group.add_command(generate)

if __name__ == "__main__":
    cli_group()
