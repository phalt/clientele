import os
import pathlib
import subprocess
import typing
from os import path

from cicerone.spec import openapi_spec as cicerone_openapi_spec
from rich import console as rich_console

from clientele import generators, settings, utils
from clientele.generators.api import writer
from clientele.generators.api.generators import clients, schemas

console = rich_console.Console()


class APIGenerator(generators.Generator):
    """
    The framework Clientele generator.

    Produces a decorator-based Python HTTP Client library using the clientele framework.
    """

    spec: cicerone_openapi_spec.OpenAPISpec
    asyncio: bool
    regen: bool
    schemas_generator: schemas.SchemasGenerator
    clients_generator: clients.ClientsGenerator
    output_dir: str
    file: typing.Optional[str]
    url: typing.Optional[str]

    def __init__(
        self,
        spec: cicerone_openapi_spec.OpenAPISpec,
        output_dir: str,
        asyncio: bool,
        regen: bool,
        url: typing.Optional[str],
        file: typing.Optional[str],
    ) -> None:
        self.schemas_generator = schemas.SchemasGenerator(spec=spec, output_dir=output_dir)
        self.clients_generator = clients.ClientsGenerator(
            spec=spec,
            output_dir=output_dir,
            schemas_generator=self.schemas_generator,
            asyncio=asyncio,
        )
        self.spec = spec
        self.asyncio = asyncio
        self.regen = regen
        self.output_dir = output_dir
        self.file = file
        self.url = url
        # Framework generator only needs client, config, and schemas (no http.py)
        self.file_name_writer_tuple = (
            ("config.py", "config_py.jinja2", writer.write_to_config),
            ("client.py", "client_py.jinja2", writer.write_to_client),
            ("schemas.py", "schemas_py.jinja2", writer.write_to_schemas),
        )

    def generate_templates_files(self) -> None:
        new_unions = settings.PY_VERSION[1] > 10
        client_project_directory_path = utils.get_client_project_directory_path(output_dir=self.output_dir)

        # Extract base_url from OpenAPI spec servers
        base_url = "http://localhost"
        if self.spec.servers and len(self.spec.servers) > 0:
            base_url = self.spec.servers[0].url
            console.log(f"[cyan]Detected base URL from spec: {base_url}[/cyan]")

        writer.write_to_init(output_dir=self.output_dir)
        for (
            client_file,
            client_template_file,
            write_func,
        ) in self.file_name_writer_tuple:
            file_path = pathlib.Path(self.output_dir) / client_file
            if file_path.exists():
                if client_file == "config.py":  # do not replace config.py if exists
                    continue
                os.remove(file_path)
            template = writer.templates.get_template(client_template_file)
            content = template.render(
                client_project_directory_path=client_project_directory_path,
                new_unions=new_unions,
                base_url=base_url,
            )
            write_func(content, output_dir=self.output_dir)
        # Manifest file
        manifest_file = pathlib.Path(self.output_dir) / "MANIFEST.md"
        if manifest_file.exists():
            os.remove(manifest_file)
        template = writer.templates.get_template("manifest.jinja2")
        generate_command = f"{f'-u {self.url}' if self.url else ''}{f'-f {self.file}' if self.file else ''} -o {self.output_dir} {'--asyncio' if self.asyncio else ''} --regen"  # noqa
        content = (
            template.render(
                api_version=self.spec.info.version if self.spec.info else "N/A",
                openapi_version=str(self.spec.version),
                clientele_version=settings.VERSION,
                command=generate_command,
            )
            + "\n"
        )
        writer.write_to_manifest(content, output_dir=self.output_dir)
        # pyproject.toml file
        pyproject_file = pathlib.Path(self.output_dir) / "pyproject.toml"
        if pyproject_file.exists():
            # Do not replace existing pyproject.toml if it exists
            pass
        else:
            template = writer.templates.get_template("pyproject.toml.jinja2")
            content = template.render()
            writer.write_to_pyproject(content, output_dir=self.output_dir)

    def prevent_accidental_regens(self) -> bool:
        if path.exists(self.output_dir):
            if not self.regen:
                console.log("[red]WARNING! If you want to regenerate, please pass --regen")
                return False
        return True

    def format_client(self) -> None:
        directory = pathlib.Path(self.output_dir)
        # Use Ruff to format all Python files in the directory
        try:
            # Resolve the path to ensure it's absolute and normalized
            resolved_dir = directory.resolve()
            # First, format the code
            subprocess.run(
                ["ruff", "format", str(resolved_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            # Then, fix auto-fixable linting issues
            subprocess.run(
                ["ruff", "check", "--fix", str(resolved_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # Sanitize stderr to prevent log injection
            error_msg = str(e.stderr).replace("\n", " ").replace("\r", " ")[:200]
            console.log(f"[yellow]Warning: Ruff formatting failed: {error_msg}")
        except FileNotFoundError:
            console.log("[yellow]Warning: Ruff not found in PATH, skipping formatting")

    def generate(self) -> None:
        self.generate_templates_files()
        self.schemas_generator.generate_schema_classes()
        self.clients_generator.generate_paths()
        self.schemas_generator.write_helpers()
        writer.flush_buffers()  # Write all buffered content at once
        self.format_client()
