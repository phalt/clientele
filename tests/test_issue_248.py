"""
Regression tests for GitHub issue #248.

Bug 1 (enum forward refs in client.py) was fixed by PR #247.

Two remaining bugs:
  Bug 2 - Array response schemas are emitted as plain type aliases
           (list[...]) instead of pydantic.RootModel subclasses.
           list[...] is a GenericAlias, not a type, so pydantic rejects
           it in response_map: dict[int, type[Any]].
  Bug 3 - The generated config.py docstring example says API_BASE_URL
           but pydantic-settings reads the field as BASE_URL (field name
           is base_url). The wrong name is silently ignored and the
           client falls back to http://localhost.
"""

import sys
from contextlib import contextmanager

from clientele.generators.api.generator import APIGenerator
from tests.generators.integration_utils import get_spec_path, load_spec


@contextmanager
def _import_generated_schemas(tmp_path):
    sys.path.insert(0, str(tmp_path))
    try:
        yield
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod in ("schemas", "client", "config"):
                del sys.modules[mod]


def _make_generator(tmp_path, spec_filename="issue_248.json"):
    spec = load_spec(spec_filename)
    spec_path = get_spec_path(spec_filename)
    return APIGenerator(
        spec=spec,
        output_dir=str(tmp_path),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    )


class TestBug2ArrayResponseRootModel:
    """
    Bug 2: array response schemas are emitted as plain type aliases
    (e.g. UploadFaces200Response = list[FaceItem]).  A GenericAlias is
    not a type, so pydantic rejects it in response_map: dict[int, type[Any]].
    The fix is to emit a pydantic.RootModel subclass instead.
    """

    def test_array_response_schema_is_rootmodel_not_type_alias(self, tmp_path):
        """schemas.py must emit a pydantic.RootModel subclass for array responses, not a bare type alias."""
        generator = _make_generator(tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert "UploadFaces200Response = list[" not in schemas_content, (
            "schemas.py emitted a plain type alias for an array response; "
            "it should emit a pydantic.RootModel subclass instead"
        )
        assert "class UploadFaces200Response(pydantic.RootModel[list[FaceItem]]):" in schemas_content, (
            "schemas.py should emit a pydantic.RootModel subclass for array responses"
        )

    def test_array_response_rootmodel_is_valid_type(self, tmp_path):
        """The generated array response class must satisfy isinstance(cls, type) so pydantic accepts it in response_map."""
        generator = _make_generator(tmp_path)
        generator.generate()

        with _import_generated_schemas(tmp_path):
            import schemas  # type: ignore

            cls = schemas.UploadFaces200Response
            assert isinstance(cls, type), f"{cls!r} is not a type; pydantic would reject it in response_map"

    def test_array_response_rootmodel_instantiation(self, tmp_path):
        """The generated RootModel subclass must be instantiable with a list."""
        generator = _make_generator(tmp_path)
        generator.generate()

        with _import_generated_schemas(tmp_path):
            import schemas  # type: ignore

            instance = schemas.UploadFaces200Response(root=[{"id": 1, "name": "Alice"}])
            assert len(instance.root) == 1
            assert instance.root[0].id == 1


class TestBug3ConfigEnvVarName:
    """
    Bug 3: generated config.py docstring example says API_BASE_URL but
    pydantic-settings maps field base_url to env var BASE_URL.  The wrong
    name is silently ignored (extra='ignore') so the client defaults to
    http://localhost.  The fix is to document the correct name BASE_URL.
    """

    def test_generated_config_documents_base_url_not_api_base_url(self, tmp_path):
        """Generated config.py must document BASE_URL, not API_BASE_URL, in its env-var example."""
        generator = _make_generator(tmp_path)
        generator.generate()

        config_content = (tmp_path / "config.py").read_text()

        assert "API_BASE_URL" not in config_content, (
            "config.py documents API_BASE_URL but pydantic-settings reads BASE_URL; the wrong name is silently ignored"
        )
        assert "BASE_URL" in config_content, "config.py should document BASE_URL as the environment variable name"

    def test_generated_config_direct_instantiation_example_uses_base_url(self, tmp_path):
        """The direct-instantiation example must use base_url=, not api_base_url=."""
        generator = _make_generator(tmp_path)
        generator.generate()

        config_content = (tmp_path / "config.py").read_text()

        assert "api_base_url=" not in config_content, (
            "config.py uses api_base_url= in example but the field is base_url"
        )
        assert "base_url=" in config_content, "config.py direct-instantiation example should use base_url="
