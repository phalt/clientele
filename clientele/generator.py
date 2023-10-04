from distutils.dir_util import copy_tree
from os.path import exists
from os import remove
from shutil import copyfile
from typing import Optional

from openapi_core import Spec
from rich.console import Console
import subprocess

from clientele.generators.clients import ClientsGenerator
from clientele.generators.http import HTTPGenerator
from clientele.generators.schemas import SchemasGenerator
from clientele.settings import (
    CLIENT_TEMPLATE_ROOT,
    CONSTANTS_ROOT,
    VERSION,
    PY_VERSION,
    templates,
)
from clientele.writer import write_to_manifest, write_to_http

console = Console()


class Generator:
    """
    Top-level generator.
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

    def generate_http_py(self):
        if exists(f"{self.output_dir}/http.py"):
            remove(f"{self.output_dir}/http.py")
        new_unions = PY_VERSION[1] > 10
        template = templates.get_template("http_py.jinja2")
        content = template.render(
            new_unions=new_unions,
        )
        write_to_http(content, output_dir=self.output_dir)

    def generate_manifest(self):
        """
        A manifest file with useful information
        """
        write_to_manifest(
            f"\nAPI VERSION: {self.spec['info']['version']}\n", self.output_dir
        )
        write_to_manifest(f"OPENAPI VERSION: {self.spec['openapi']}\n", self.output_dir)
        write_to_manifest(f"CLIENTELE VERSION: {VERSION}\n", self.output_dir)
        # ruff: noqa
        write_to_manifest(
            f"""
Regnerate using this command:

```sh
clientele generate {f"-u {self.url}" if self.url else ""}{f"-f {self.file}" if self.file else ""} -o {self.output_dir} {"--asyncio t" if self.asyncio else ""} --regen t
```
""",
            self.output_dir,
        )

    def prevent_accidental_regens(self) -> bool:
        if exists(self.output_dir):
            if not self.regen:
                console.log(
                    "[red]WARNING! If you want to regenerate, please pass --regen t"
                )
                return False
        return True

    def format_client(self) -> None:
        subprocess.run(
            ["black", self.output_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def generate(self) -> None:
        copy_tree(src=CLIENT_TEMPLATE_ROOT, dst=self.output_dir)
        if not exists(f"{self.output_dir}/config.py"):
            copyfile(
                f"{CONSTANTS_ROOT}/config_template.py",
                f"{self.output_dir}/config.py",
            )
        self.generate_http_py()
        self.generate_manifest()
        self.schemas_generator.generate_schema_classes()
        self.clients_generator.generate_paths()
        self.http_generator.generate_http_content()
        self.schemas_generator.write_helpers()
        self.format_client()
