import click


def _load_openapi_spec(url: str = None, file: str = None):
    """
    Load OpenAPI spec from URL or file.
    Returns the spec object and handles JSON/YAML parsing.
    """
    import json

    import httpx
    import openapi_core
    import yaml

    assert url or file, "Must pass either a URL or a file"

    if url:
        with httpx.Client() as client:  # Use context manager for proper cleanup
            response = client.get(url)
            try:
                data = response.json()
            except json.JSONDecodeError:
                # It's probably yaml
                data = yaml.safe_load(response.content)
        return openapi_core.Spec.from_dict(data)
    else:
        with open(file, "r") as f:
            return openapi_core.Spec.from_file(f)


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
    import clientele.settings

    print(f"clientele {clientele.settings.VERSION}")


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (json file)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json file)", required=False)
def validate(url, file):
    """
    Validate an OpenAPI schema. Will error if anything is wrong with the schema
    """
    import rich.console

    console = rich.console.Console()

    spec = _load_openapi_spec(url=url, file=file)
    console.log(f"Found API specification: {spec['info']['title']} | version {spec['info']['version']}")
    major, _, _ = spec["openapi"].split(".")
    if int(major) < 3:
        console.log(f"[red]Clientele only supports OpenAPI version 3.0.0 and up, and you have {spec['openapi']}")
        return
    console.log("schema validated successfully! You can generate a client with it")


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (URL)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json or yaml file)", required=False)
@click.option("-o", "--output", help="Directory for the generated client", required=True)
@click.option("-a", "--asyncio", help="Generate async client", required=False)
@click.option("-r", "--regen", help="Regenerate client", required=False)
def generate(url, file, output, asyncio, regen):
    """
    Generate a new client from an OpenAPI schema
    """
    import rich.console

    console = rich.console.Console()

    import clientele.generators.standard.generator

    spec = _load_openapi_spec(url=url, file=file)
    console.log(f"Found API specification: {spec['info']['title']} | version {spec['info']['version']}")
    major, _, _ = spec["openapi"].split(".")
    if int(major) < 3:
        console.log(f"[red]Clientele only supports OpenAPI version 3.0.0 and up, and you have {spec['openapi']}")
        return
    generator = clientele.generators.standard.generator.StandardGenerator(
        spec=spec, asyncio=asyncio, regen=regen, output_dir=output, url=url, file=file
    )
    if generator.prevent_accidental_regens():
        generator.generate()
        console.log("\n[green]⚜️ Client generated! ⚜️ \n")
        console.log("[yellow]REMEMBER: install `httpx` `pydantic`, and `respx` to use your new client")


@click.command()
@click.option("-o", "--output", help="Directory for the generated client", required=True)
def generate_basic(output):
    """
    Generate a "basic" file structure, no code.
    """
    import rich.console

    import clientele.generators.basic.generator

    console = rich.console.Console()

    console.log(f"Generating basic client at {output}...")

    generator = clientele.generators.basic.generator.BasicGenerator(output_dir=output)

    generator.generate()


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (URL)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json or yaml file)", required=False)
@click.option("-o", "--output", help="Directory for the generated client", required=True)
@click.option("-a", "--asyncio", help="Generate async client", required=False)
@click.option("-r", "--regen", help="Regenerate client", required=False)
def generate_class(url, file, output, asyncio, regen):
    """
    Generate a class-based client from an OpenAPI schema
    """
    import rich.console

    console = rich.console.Console()

    import clientele.generators.classbase.generator

    spec = _load_openapi_spec(url=url, file=file)
    console.log(f"Found API specification: {spec['info']['title']} | version {spec['info']['version']}")
    major, _, _ = spec["openapi"].split(".")
    if int(major) < 3:
        console.log(f"[red]Clientele only supports OpenAPI version 3.0.0 and up, and you have {spec['openapi']}")
        return
    generator = clientele.generators.classbase.generator.ClassbaseGenerator(
        spec=spec, asyncio=asyncio, regen=regen, output_dir=output, url=url, file=file
    )
    if generator.prevent_accidental_regens():
        generator.generate()
        console.log("\n[green]⚜️ Class-based client generated! ⚜️ \n")
        console.log("[yellow]REMEMBER: install `httpx` `pydantic`, and `respx` to use your new client")


cli_group.add_command(generate)
cli_group.add_command(generate_basic)
cli_group.add_command(generate_class)
cli_group.add_command(version)
cli_group.add_command(validate)

if __name__ == "__main__":
    cli_group()
