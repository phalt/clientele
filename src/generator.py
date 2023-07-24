from distutils.dir_util import copy_tree

from openapi_core import Spec

from src.generators.clients import ClientsGenerator
from src.generators.schemas import SchemasGenerator
from src.settings import TEMPLATE_ROOT


class Generator:
    """
    Top-level generator.
    """

    spec: Spec
    asyncio: bool
    schemas_generator: SchemasGenerator
    clients_generator: ClientsGenerator
    output_dir: str

    def __init__(self, spec: Spec, output_dir: str, asyncio: bool) -> None:
        self.schemas_generator = SchemasGenerator(spec=spec, output_dir=output_dir)
        self.clients_generator = ClientsGenerator(
            spec=spec, output_dir=output_dir, schemas_generator=self.schemas_generator
        )
        self.spec = spec
        self.asyncio = asyncio
        self.output_dir = output_dir

    def generate(
        self,
        url: str,
    ) -> None:
        copy_tree(src=TEMPLATE_ROOT, dst=self.output_dir)
        self.schemas_generator.generate_schema_classes()
        self.clients_generator.generate_paths(api_url=url)
