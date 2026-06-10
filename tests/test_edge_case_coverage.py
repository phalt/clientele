"""Additional tests for edge cases to reach 100% coverage."""

import tempfile


def test_schemas_generator_no_schemas_branch():
    """Test schemas generator when components has no schemas attribute."""
    from clientele.generators.api import writer as api_writer
    from clientele.generators.shared.schemas import SchemasGenerator

    spec_dict = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {},
        "paths": {},
    }

    from cicerone import parse as cicerone_parse

    spec = cicerone_parse.parse_spec_from_dict(spec_dict)

    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SchemasGenerator(spec=spec, output_dir=str(tmpdir), writer=api_writer)

        generator.generate_schema_classes()

        # Should complete without error
