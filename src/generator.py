from distutils.dir_util import copy_tree
from os.path import exists
from shutil import copyfile
from typing import Optional

from openapi_core import Spec

from src.generators.clients import ClientsGenerator
from src.generators.http import HTTPGenerator
from src.generators.schemas import SchemasGenerator
from src.settings import CLIENT_TEMPLATE_ROOT, CONSTANTS_ROOT, VERSION
from src.writer import write_to_manifest


class Generator:
    """
    Top-level generator.
    """

    spec: Spec
    asyncio: bool
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
        self.output_dir = output_dir
        self.file = file
        self.url = url

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
Generated using this command:

```sh
clientele generate {f"-u {self.url}" if self.url else ""}{f"-f {self.file}" if self.file else ""} -o {self.output_dir} {"--asyncio t" if self.asyncio else ""}
```
""",
            self.output_dir,
        )

    def generate(self) -> None:
        copy_tree(src=CLIENT_TEMPLATE_ROOT, dst=self.output_dir)
        if not exists(f"{self.output_dir}/constants.py"):
            copyfile(
                f"{CONSTANTS_ROOT}/constants_template.py",
                f"{self.output_dir}/constants.py",
            )
        self.generate_manifest()
        self.schemas_generator.generate_schema_classes()
        self.clients_generator.generate_paths()
        self.http_generator.generate_http_content()
        self.schemas_generator.write_helpers()
