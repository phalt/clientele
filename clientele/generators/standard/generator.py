from os import remove
from os.path import exists
from pathlib import Path
from typing import Optional

import black
from openapi_core import Spec
from rich.console import Console

from clientele.generators.standard.generators.clients import ClientsGenerator
from clientele.generators.standard.generators.http import HTTPGenerator
from clientele.generators.standard.generators.schemas import SchemasGenerator
from clientele.generators.standard.utils import get_client_project_directory_path
from clientele.generators.standard.writer import (
    templates,
    write_to_client,
    write_to_config,
    write_to_http,
    write_to_init,
    write_to_manifest,
    write_to_schemas,
)
from clientele.settings import (
    PY_VERSION,
    VERSION,
)

console = Console()


class Generator:
    """
    The standard Clientele generator.

    Produces a Python HTTP Client library.
    """

    spec: Spec
    asyncio: bool
    regen: bool
    schemas_generator: SchemasGenerator
    clients_generator: ClientsGenerator
    http_generator: HTTPGenerator
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
        self.http_generator = HTTPGenerator(
            spec=spec, output_dir=output_dir, asyncio=asyncio
        )
        self.schemas_generator = SchemasGenerator(spec=spec, output_dir=output_dir)
        self.clients_generator = ClientsGenerator(
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

    def generate_templates_files(self):
        new_unions = PY_VERSION[1] > 10
        client_project_directory_path = get_client_project_directory_path(
            output_dir=self.output_dir
        )
        write_to_init(output_dir=self.output_dir)
        if not exists(f"{self.output_dir}/config.py"):
            template = templates.get_template("config_py.jinja2")
            content = template.render()
            write_to_config(content, output_dir=self.output_dir)
        # client file
        if exists(f"{self.output_dir}/client.py"):
            remove(f"{self.output_dir}/client.py")
        template = templates.get_template("client_py.jinja2")
        content = template.render(
            client_project_directory_path=client_project_directory_path
        )
        write_to_client(content, output_dir=self.output_dir)
        # http file
        if exists(f"{self.output_dir}/http.py"):
            remove(f"{self.output_dir}/http.py")
        template = templates.get_template("http_py.jinja2")
        content = template.render(
            new_unions=new_unions,
            client_project_directory_path=client_project_directory_path,
        )
        write_to_http(content, output_dir=self.output_dir)
        # schemas file
        if exists(f"{self.output_dir}/schemas.py"):
            remove(f"{self.output_dir}/schemas.py")
        template = templates.get_template("schemas_py.jinja2")
        content = template.render()
        write_to_schemas(content, output_dir=self.output_dir)
        # Manifest file
        if exists(f"{self.output_dir}/MANIFEST.md"):
            remove(f"{self.output_dir}/MANIFEST.md")
        template = templates.get_template("manifest.jinja2")
        generate_command = f'{f"-u {self.url}" if self.url else ""}{f"-f {self.file}" if self.file else ""} -o {self.output_dir} {"--asyncio t" if self.asyncio else ""} --regen t'  # noqa
        content = (
            template.render(
                api_version=self.spec["info"]["version"],
                openapi_version=self.spec["openapi"],
                clientele_version=VERSION,
                command=generate_command,
            )
            + "\n"
        )
        write_to_manifest(content, output_dir=self.output_dir)

    def prevent_accidental_regens(self) -> bool:
        if exists(self.output_dir):
            if not self.regen:
                console.log(
                    "[red]WARNING! If you want to regenerate, please pass --regen t"
                )
                return False
        return True

    def format_client(self) -> None:
        directory = Path(self.output_dir)
        for f in directory.glob("*.py"):
            black.format_file_in_place(
                f, fast=False, mode=black.Mode(), write_back=black.WriteBack.YES
            )

    def generate(self) -> None:
        self.generate_templates_files()
        self.schemas_generator.generate_schema_classes()
        self.clients_generator.generate_paths()
        self.http_generator.generate_http_content()
        self.schemas_generator.write_helpers()
        self.format_client()
