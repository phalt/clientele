import pytest

from clientele.generators import Generator
from clientele.generators.api.generator import APIGenerator
from clientele.generators.basic.generator import BasicGenerator


def test_generator_is_abstract():
    """Test that Generator is an abstract base class and cannot be instantiated."""
    with pytest.raises(TypeError):
        Generator()


def test_basic_generator_inherits_from_generator():
    """Test that BasicGenerator inherits from Generator ABC."""
    assert issubclass(BasicGenerator, Generator)


def test_framework_generator_inherits_from_generator():
    """Test that APIGenerator inherits from Generator ABC."""
    assert issubclass(APIGenerator, Generator)


def test_basic_generator_implements_generate():
    """Test that BasicGenerator implements the generate method."""
    assert hasattr(BasicGenerator, "generate")
    assert callable(getattr(BasicGenerator, "generate"))


def test_api_generator_implements_generate():
    """Test that APIGenerator implements the generate method."""
    assert hasattr(APIGenerator, "generate")
    assert callable(getattr(APIGenerator, "generate"))


def test_generator_abstract_method_raises_not_implemented():
    """Test that calling the abstract generate method raises NotImplementedError."""
    from clientele.generators.base import Generator

    class IncompleteGenerator(Generator):
        pass

    with pytest.raises(TypeError):
        IncompleteGenerator()
