from cicerone.spec import openapi_spec as cicerone_openapi_spec

from clientele.generators import base_clients
from clientele.generators.classbase import writer
from clientele.generators.classbase.generators import http, schemas


class ClientsGenerator(base_clients.BaseClientsGenerator):
    """
    Handles all the content generated in the client.py file for class-based clients.
    """

    schemas_generator: schemas.SchemasGenerator
    http_generator: http.HTTPGenerator

    def __init__(
        self,
        spec: cicerone_openapi_spec.OpenAPISpec,
        output_dir: str,
        schemas_generator: schemas.SchemasGenerator,
        http_generator: http.HTTPGenerator,
        asyncio: bool,
    ) -> None:
        super().__init__(spec, output_dir, schemas_generator, http_generator, asyncio)
        self.writer = writer
