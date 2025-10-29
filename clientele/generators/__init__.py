# For __init__.py files, we allow from imports to expose the API
from clientele.generators.base import Generator

__all__ = ["Generator"]
