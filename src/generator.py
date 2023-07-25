from distutils.dir_util import copy_tree
from os.path import exists
from shutil import copyfile

from openapi_core import Spec

from src.generators.clients import ClientsGenerator
from src.generators.http import HTTPGenerator
from src.generators.schemas import SchemasGenerator
from src.settings import CONSTANTS_ROOT, TEMPLATE_ROOT, VERSION
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

    def __init__(self, spec: Spec, output_dir: str, asyncio: bool) -> None:
        self.schemas_generator = SchemasGenerator(spec=spec, output_dir=output_dir)
        self.clients_generator = ClientsGenerator(
            spec=spec,
            output_dir=output_dir,
            schemas_generator=self.schemas_generator,
            asyncio=asyncio,
        )
        self.http_generator = HTTPGenerator(
            spec=spec, output_dir=output_dir, asyncio=asyncio
        )
        self.spec = spec
        self.asyncio = asyncio
        self.output_dir = output_dir

    def generate_manifest(self):
        """
        A manifest file with useful information
        """
        write_to_manifest(
            f"API VERSION: {self.spec['info']['version']}\n", self.output_dir
        )
        write_to_manifest(f"OPENAPI VERSION: {self.spec['openapi']}\n", self.output_dir)
        write_to_manifest(f"CLIENTELE VERSION: {VERSION}\n", self.output_dir)

    def generate(self) -> None:
        copy_tree(src=TEMPLATE_ROOT, dst=self.output_dir)
        if not exists(f"{self.output_dir}constants.py"):
            copyfile(
                f"{CONSTANTS_ROOT}/constants_template.py",
                f"{self.output_dir}constants.py",
            )
        self.generate_manifest()
        self.schemas_generator.generate_schema_classes()
        self.clients_generator.generate_paths()
        self.http_generator.generate_http_content()
