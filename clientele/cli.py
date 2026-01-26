from __future__ import annotations

import textwrap

import click

from clientele import settings

CLIENTELE_HEADER = r"""
   ___ _ _            _       _
  / __\ (_) ___ _ __ | |_ ___| | ___
 / /  | | |/ _ \ '_ \| __/ _ \ |/ _ \
/ /___| | |  __/ | | | ||  __/ |  __/
\____/|_|_|\___|_| |_|\__\___|_|\___|
""".strip("\n")


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
    pass


cli_group.help = textwrap.dedent(f"""\
\b
{CLIENTELE_HEADER}

⚜️ Clientele is a different way to build Python API Clients

🔢 Version {settings.VERSION}

📚 Read the docs: https://docs.clientele.dev

🐙 Contribute on GitHub: https://github.com/phalt/clientele

""").strip("\n")


@click.command()
def version():
    """
    Print the current version of Clientele
    """
    from clientele import settings

    print(f"clientele {settings.VERSION}")


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


def scaffold_api(url, file, output, asyncio=False, regen=False):
    """
    Scaffold an API client from an OpenAPI schema.
    """
    from rich.console import Console

    console = Console()

    from clientele.generators.api.generator import APIGenerator

    spec = _prepare_spec(console=console, url=url, file=file)
    if not spec:
        return
    generator = APIGenerator(spec=spec, asyncio=asyncio, regen=regen, output_dir=output, url=url, file=file)
    if generator.prevent_accidental_regens():
        generator.generate()
        console.log("\n[green]⚜️ client generated! ⚜️ \n")


@click.command()
@click.option("-u", "--url", help="URL to openapi schema (URL)", required=False)
@click.option("-f", "--file", help="Path to openapi schema (json or yaml file)", required=False)
@click.option("-o", "--output", help="Directory for the generated client", required=True)
@click.option("-a", "--asyncio", is_flag=True, help="Generate async client")
@click.option("-r", "--regen", is_flag=True, help="Regenerate client")
def start_api(url, file, output, asyncio=False, regen=False):
    """
    Set up a new API Client

    -o / --output: Directory for the generated client

    If -u / --url or -f / --file is provided, generates the client from the OpenAPI schema.
    Otherwise, creates a basic scaffold.

    if -a / --asyncio is provided, generates an async client.

    if -r / --regen is provided, regenerates the client even if files exist.
    """
    if not url and not file:
        # No schema provided, generate basic scaffold
        generate_basic(output=output)
    else:
        # Schema provided, generate full client
        scaffold_api(url=url, file=file, output=output, asyncio=asyncio, regen=regen)


cli_group.add_command(version)
cli_group.add_command(start_api)

if __name__ == "__main__":
    cli_group()
