from os import remove
from os.path import exists
from pathlib import Path
from typing import Optional

import black
from openapi_core import Spec
from rich.console import Console

from clientele import settings, utils
from clientele.generators.standard import writer
from clientele.generators.standard.generators import clients, http, schemas

console = Console()


class StandardGenerator:
    """
    The standard Clientele generator.

    Produces a Python HTTP Client library.
    """

    spec: Spec
    asyncio: bool
    regen: bool
    schemas_generator: schemas.SchemasGenerator
    clients_generator: clients.ClientsGenerator
    http_generator: http.HTTPGenerator
    output_dir: str
    file: Optional[str]
    url: Optional[str]

    def __init__(
        self,
        spec: Spec,
        output_dir: str,
        asyncio: bool,
        regen: bool,
        url: Optional[str],
        file: Optional[str],
    ) -> None:
        self.http_generator = http.HTTPGenerator(spec=spec, output_dir=output_dir, asyncio=asyncio)
        self.schemas_generator = schemas.SchemasGenerator(spec=spec, output_dir=output_dir)
        self.clients_generator = clients.ClientsGenerator(
            spec=spec,
            output_dir=output_dir,
            schemas_generator=self.schemas_generator,
            http_generator=self.http_generator,
            asyncio=asyncio,
        )
        self.spec = spec
        self.asyncio = asyncio
        self.regen = regen
        self.output_dir = output_dir
        self.file = file
        self.url = url
        self.file_name_writer_tuple = (
            ("config.py", "config_py.jinja2", writer.write_to_config),
            ("client.py", "client_py.jinja2", writer.write_to_client),
            ("http.py", "http_py.jinja2", writer.write_to_http),
            ("schemas.py", "schemas_py.jinja2", writer.write_to_schemas),
        )

    def generate_templates_files(self):
        new_unions = settings.PY_VERSION[1] > 10
        client_project_directory_path = utils.get_client_project_directory_path(output_dir=self.output_dir)
        writer.write_to_init(output_dir=self.output_dir)
        for (
            client_file,
            client_template_file,
            write_func,
        ) in self.file_name_writer_tuple:
            if exists(f"{self.output_dir}/{client_file}"):
                if client_file == "config.py": # do not replace config.py if exists
                    continue
                remove(f"{self.output_dir}/{client_file}")
            template = writer.templates.get_template(client_template_file)
            content = template.render(
                client_project_directory_path=client_project_directory_path,
                new_unions=new_unions,
            )
            write_func(content, output_dir=self.output_dir)
        # Manifest file
        if exists(f"{self.output_dir}/MANIFEST.md"):
            remove(f"{self.output_dir}/MANIFEST.md")
        template = writer.templates.get_template("manifest.jinja2")
        generate_command = f'{f"-u {self.url}" if self.url else ""}{f"-f {self.file}" if self.file else ""} -o {self.output_dir} {"--asyncio t" if self.asyncio else ""} --regen t'  # noqa
        content = (
            template.render(
                api_version=self.spec["info"]["version"],
                openapi_version=self.spec["openapi"],
                clientele_version=settings.VERSION,
                command=generate_command,
            )
            + "\n"
        )
        writer.write_to_manifest(content, output_dir=self.output_dir)

    def prevent_accidental_regens(self) -> bool:
        if exists(self.output_dir):
            if not self.regen:
                console.log("[red]WARNING! If you want to regenerate, please pass --regen t")
                return False
        return True

    def format_client(self) -> None:
        directory = Path(self.output_dir)
        for f in directory.glob("*.py"):
            black.format_file_in_place(f, fast=False, mode=black.Mode(), write_back=black.WriteBack.YES)

    def generate(self) -> None:
        self.generate_templates_files()
        self.schemas_generator.generate_schema_classes()
        self.clients_generator.generate_paths()
        self.http_generator.generate_http_content()
        self.schemas_generator.write_helpers()
        self.format_client()
