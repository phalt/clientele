import pytest

from clientele.generators.api import clients as api_clients
from clientele.generators.api import writer as api_writer
from clientele.generators.shared.schemas import SchemasGenerator
from tests.generators.integration_utils import load_spec


def _make_clients_generator(spec, output_dir) -> api_clients.ClientsGenerator:
    schemas_gen = SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)
    return api_clients.ClientsGenerator(
        spec=spec,
        output_dir=str(output_dir),
        schemas_generator=schemas_gen,
        asyncio=False,
    )


def test_clients_generator_multiple_requestbody(tmp_path):
    """Test schemas generator with multiple requestBody schemas."""

    generator = _make_clients_generator(load_spec("multiple_requestbody.json"), tmp_path)

    generator.generate_paths()

    assert len([1 for s in generator.schemas_generator.schemas if s == 'TestInputApplicationJson']) == 1
    assert len([1 for s in generator.schemas_generator.schemas if s == 'TestInputApplicationXWwwFormUrlencoded']) == 1

