from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import click


def _print_dependency_instructions(console):
    """
    Print installation instructions for client dependencies.
    """
    console.log("[yellow]Install the following dependencies to use your new client:\n")
    console.log("[cyan]# For requirements.txt:")
    console.log("httpx")
    console.log("pydantic")
    console.log("respx  # For testing\n")
    console.log("[cyan]# For pyproject.toml:")
    console.log('dependencies = ["httpx", "pydantic"]')
    console.log("\\[dependency-groups]")
    console.log('dev = ["respx"]')


def _load_openapi_spec(url: str | None = None, file: str | None = None):
    """
    Load OpenAPI spec from URL or file using cicerone's parsers, normalizing
    OpenAPI 3.1 schemas for cicerone compatibility when needed.

    Normalization must happen BEFORE parsing with cicerone to avoid validation errors
    on OpenAPI 3.1 features like type arrays (e.g., type: ['string', 'null']).

    Note: This function only normalizes OpenAPI 3.x specs. Swagger 2.x specs are
    parsed as-is and will be auto-converted by cicerone (though they should be
    rejected by _prepare_spec).
    """
    import json
    import pathlib

    import yaml
    from cicerone import parse as cicerone_parse

    from clientele.generators.cicerone_compat import normalize_openapi_31_spec

    assert url or file, "Must pass either a URL or a file"

    if url is not None:
        # For URLs, we need to fetch and parse the content first
        import urllib.request

        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")

        # Try to determine format from URL or content
        if url.endswith((".yaml", ".yml")):
            spec_dict = yaml.safe_load(content)
        else:
            # Try JSON first, fall back to YAML
            try:
                spec_dict = json.loads(content)
            except json.JSONDecodeError:
                spec_dict = yaml.safe_load(content)
    elif file is not None:
        # Read file content
        file_path = pathlib.Path(file)
        content = file_path.read_text()

        # Parse based on file extension
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            spec_dict = yaml.safe_load(content)
        else:
            spec_dict = json.loads(content)
    else:  # pragma: no cover - guarded by the assert above
        raise AssertionError("Must pass either a URL or a file")

    # Only normalize if this is OpenAPI 3.x (not Swagger 2.x)
    # Check for 'openapi' field to identify OpenAPI 3.x specs
    if "openapi" in spec_dict:
        # Normalize OpenAPI 3.1 features before parsing with cicerone
        normalized_spec_dict = normalize_openapi_31_spec(spec_dict)
    else:
        # Swagger 2.x or other format - parse as-is
        normalized_spec_dict = spec_dict

    # Parse with cicerone
    return cicerone_parse.parse_spec_from_dict(normalized_spec_dict)


def _prepare_spec(console, url: str | None = None, file: str | None = None):
    spec = _load_openapi_spec(url=url, file=file)
    console.log(f"Found API specification: {spec.info.title} | version {spec.info.version}")
    major, _, _ = str(spec.version).partition(".")
    if major and int(major) < 3:
        console.log(f"[red]Clientele only supports OpenAPI version 3.0.0 and up, and you have {spec.version}")
        return None
    return spec


@click.group()
def cli_group():
    """
    Clientele:  The Python API Client Generator for FastAPI, Django REST Framework, and Django Ninja
    https://github.com/phalt/clientele
    """


@click.command()
def version():
    """
    Print the current version of clientele
    """
    from clientele import settings

    print(f"clientele {settings.VERSION}")


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
    from rich.console import Console

    console = Console()

    from clientele.generators.standard.generator import StandardGenerator

    spec = _prepare_spec(console=console, url=url, file=file)
    if not spec:
        return
    generator = StandardGenerator(spec=spec, asyncio=asyncio, regen=regen, output_dir=output, url=url, file=file)
    if generator.prevent_accidental_regens():
        generator.generate()
        console.log("\n[green]⚜️ Client generated! ⚜️ \n")
        _print_dependency_instructions(console)


@click.command()
@click.option("-o", "--output", help="Directory for the generated client", required=True)
def generate_basic(output):
    """
    Generate a "basic" file structure, no code.
    """
    from rich.console import Console

    from clientele.generators.basic.generator import BasicGenerator

    console = Console()

    console.log(f"Generating basic client at {output}...")

    generator = BasicGenerator(output_dir=output)

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
    from rich.console import Console

    console = Console()

    from clientele.generators.classbase.generator import ClassbaseGenerator

    spec = _prepare_spec(console=console, url=url, file=file)
    if not spec:
        return
    generator = ClassbaseGenerator(spec=spec, asyncio=asyncio, regen=regen, output_dir=output, url=url, file=file)
    if generator.prevent_accidental_regens():
        generator.generate()
        console.log("\n[green]⚜️ Class-based client generated! ⚜️ \n")
        _print_dependency_instructions(console)


@click.command()
@click.option("-c", "--client", help="Path to generated client directory", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json or yaml file)", required=False)
@click.option("-u", "--url", help="URL to openapi schema (URL)", required=False)
def explore(client, file, url):
    """
    Interactive API explorer - test and discover APIs interactively
    """
    from rich.console import Console

    from clientele.explore.introspector import ClientIntrospector
    from clientele.explore.repl import ClienteleREPL
    from clientele.generators.standard.generator import StandardGenerator

    console = Console()

    # Determine client path
    client_path = None
    temp_dir = None

    if client:
        # Use existing client
        client_path = Path(client)
        if not client_path.exists():
            console.log(f"[red]Client directory not found: {client_path}[/red]")
            return
        if not (client_path / "client.py").exists():
            console.log(f"[red]Not a valid client directory (missing client.py): {client_path}[/red]")
            return

    elif file or url:
        # Generate temporary client from schema
        console.log("[cyan]Generating temporary client from schema...[/cyan]")

        spec = _load_openapi_spec(url=url, file=file)

        # Validate spec version
        major, _, _ = str(spec.version).split(".")
        if int(major) < 3:
            console.log(f"[red]Clientele only supports OpenAPI version 3.0.0 and up, and you have {spec.version}")
            return

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="clientele_explore_")
        client_path = Path(temp_dir)

        # Generate client
        generator = StandardGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(client_path), url=url, file=file
        )
        generator.generate()

        console.log(f"[green]Client generated at {client_path}[/green]")

    else:
        console.log("[red]Error: Must provide either --client, --file, or --url[/red]")
        console.log("Examples:")
        console.log("  clientele explore -c ./my_client")
        console.log("  clientele explore -f ./openapi.json")
        console.log("  clientele explore -u https://api.example.com/openapi.json")
        return

    # Load and introspect the client
    try:
        introspector = ClientIntrospector(client_path)
        introspector.load_client()
        introspector.discover_operations()

        # Start REPL
        repl = ClienteleREPL(introspector)
        repl.run()

    except Exception as e:
        console.log(f"[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up temporary directory if created
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Ignore cleanup errors


cli_group.add_command(generate)
cli_group.add_command(generate_basic)
cli_group.add_command(generate_class)
cli_group.add_command(version)
cli_group.add_command(explore)

if __name__ == "__main__":
    cli_group()
