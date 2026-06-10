"""
Tests for enum schema generation.

OpenAPI enums are not restricted to strings: integer enums (status codes,
versions), number enums, and mixed-type enums are all legal. Historically the
generator assumed string values and crashed with an AttributeError when it
called .upper() on a non-string member.

Expected behaviour:
  - string enums      -> class Colour(str, enum.Enum) with UPPER_CASE members
  - integer enums     -> class StatusCode(enum.IntEnum) with VALUE_<n> members
  - number enums      -> class SampleRate(enum.Enum) with VALUE_<n> members
  - mixed-type enums  -> class Priority(enum.Enum), strings named as usual,
                         non-strings named VALUE_<n>
  - negative numbers  -> "-" becomes MINUS_ (e.g. VALUE_MINUS_12)
  - generated enums must round-trip through pydantic validation
"""

import enum
import sys
from contextlib import contextmanager

import pydantic
import pytest

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


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    """Generate the enums client once for the whole module."""
    tmp_path = tmp_path_factory.mktemp("enums_client")
    spec = load_spec("enums.json")
    generator = APIGenerator(
        spec=spec,
        output_dir=str(tmp_path),
        asyncio=False,
        regen=True,
        url=None,
        file=str(get_spec_path("enums.json")),
    )
    generator.generate()
    return tmp_path


class TestStringEnums:
    """Regression: string enums keep their existing shape."""

    def test_string_enum_subclasses_str_and_enum(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            assert issubclass(schemas.Colour, str)
            assert issubclass(schemas.Colour, enum.Enum)

    def test_string_enum_members(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            assert schemas.Colour.RED.value == "red"
            assert schemas.Colour.GREEN.value == "green"
            assert schemas.Colour.BLUE.value == "blue"


class TestIntegerEnums:
    """Integer enums must generate an enum.IntEnum, not crash."""

    def test_generation_does_not_crash(self, generated):
        # The fixture generation itself is the core regression: it used to
        # raise AttributeError: 'int' object has no attribute 'upper'.
        assert (generated / "schemas.py").exists()

    def test_integer_enum_is_int_enum(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            assert issubclass(schemas.StatusCode, enum.IntEnum)

    def test_integer_enum_members(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            assert schemas.StatusCode.VALUE_1.value == 1
            assert schemas.StatusCode.VALUE_2.value == 2
            assert schemas.StatusCode.VALUE_3.value == 3

    def test_negative_integer_members(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            assert schemas.TimezoneOffset.VALUE_MINUS_12.value == -12
            assert schemas.TimezoneOffset.VALUE_0.value == 0
            assert schemas.TimezoneOffset.VALUE_12.value == 12


class TestNumberEnums:
    """Number (float) enums generate a plain enum.Enum with VALUE_ members."""

    def test_number_enum_members(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            assert issubclass(schemas.SampleRate, enum.Enum)
            assert schemas.SampleRate.VALUE_0_5.value == 0.5
            assert schemas.SampleRate.VALUE_1_0.value == 1.0
            assert schemas.SampleRate.VALUE_2_5.value == 2.5


class TestMixedEnums:
    """Mixed string/number enums generate a plain enum.Enum."""

    def test_mixed_enum_members(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            assert issubclass(schemas.Priority, enum.Enum)
            # A mixed enum cannot subclass str or int
            assert not issubclass(schemas.Priority, str)
            assert not issubclass(schemas.Priority, int)
            assert schemas.Priority.LOW.value == "low"
            assert schemas.Priority.VALUE_1.value == 1
            assert schemas.Priority.VALUE_2.value == 2


class TestPydanticIntegration:
    """Generated enums must validate from raw JSON values via pydantic."""

    def test_model_validates_enum_values(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            device = schemas.Device.model_validate(
                {
                    "status": 2,
                    "colour": "red",
                    "priority": 1,
                    "offset": -12,
                    "sample_rate": 0.5,
                }
            )
            assert device.status == schemas.StatusCode.VALUE_2
            assert device.colour == schemas.Colour.RED
            assert device.priority == schemas.Priority.VALUE_1
            assert device.offset == schemas.TimezoneOffset.VALUE_MINUS_12
            assert device.sample_rate == schemas.SampleRate.VALUE_0_5

    def test_model_rejects_values_outside_enum(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            with pytest.raises(pydantic.ValidationError):
                schemas.Device.model_validate({"status": 99, "colour": "red"})

    def test_model_serialises_enum_values_back_to_raw(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            device = schemas.Device.model_validate({"status": 1, "colour": "blue"})
            dumped = device.model_dump(mode="json", exclude_none=True)
            assert dumped["status"] == 1
            assert dumped["colour"] == "blue"


class TestMemberNameCollisions:
    """Values that sanitise to the same member name must be deduplicated."""

    def test_colliding_names_get_suffixes(self, tmp_path):
        from clientele.generators.api import writer
        from clientele.generators.shared.generators.schemas import SchemasGenerator

        spec = load_spec("enums.json")
        generator = SchemasGenerator(spec=spec, output_dir=str(tmp_path), writer=writer)
        # "YES" and "yes" both upper-case to YES
        generator.make_schema_class("Answer", {"type": "string", "enum": ["YES", "yes", "no"]})
        writer.flush_buffers()
        content = (tmp_path / "schemas.py").read_text()

        assert 'YES = "YES"' in content
        assert 'YES_2 = "yes"' in content
        assert 'NO = "no"' in content
